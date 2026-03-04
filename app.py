import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import re

st.title("Site Feasibility Tool")

# -------------------------------------------------
# Convert DMS → Decimal
# -------------------------------------------------
def convert_coord(coord):

    coord = str(coord).strip()

    try:
        return float(coord)
    except:
        pass

    pattern = r"(\d+)°(\d+)'([\d\.]+)\"?([NSEW])"
    match = re.match(pattern, coord)

    if match:
        deg, minutes, seconds, direction = match.groups()

        decimal = float(deg) + float(minutes)/60 + float(seconds)/3600

        if direction in ["S","W"]:
            decimal = -decimal

        return decimal

    return None


# -------------------------------------------------
# Load Data
# -------------------------------------------------
p0 = pd.read_csv("P0.csv")
qis = pd.read_csv("QIS Locations.csv")
deals = pd.read_csv("deals.csv")

# Clean column names
p0.columns = p0.columns.str.strip()
qis.columns = qis.columns.str.strip()
deals.columns = deals.columns.str.strip()

# Remove duplicate QIS
if "QIS No." in qis.columns:
    qis = qis.drop_duplicates(subset=["QIS No."])

# Convert coordinates
p0["Latitude"] = pd.to_numeric(p0["Latitude"], errors="coerce")
p0["Longitude"] = pd.to_numeric(p0["Longitude"], errors="coerce")

qis["Lat"] = pd.to_numeric(qis["Lat"], errors="coerce")
qis["Long"] = pd.to_numeric(qis["Long"], errors="coerce")

deals["Latitude"] = pd.to_numeric(deals["Latitude"], errors="coerce")
deals["Longitude"] = pd.to_numeric(deals["Longitude"], errors="coerce")

# Drop invalid rows
p0 = p0.dropna(subset=["Latitude","Longitude"])
qis = qis.dropna(subset=["Lat","Long"])
deals = deals.dropna(subset=["Latitude","Longitude"])

# Remove invalid coordinates
deals = deals[
    (deals["Latitude"] >= -90) &
    (deals["Latitude"] <= 90) &
    (deals["Longitude"] >= -180) &
    (deals["Longitude"] <= 180)
]

# Detect QIS count column automatically
p0_qis_col = next((c for c in p0.columns if "qis" in c.lower()), None)
deal_qis_col = next((c for c in deals.columns if "qis" in c.lower()), None)

# -------------------------------------------------
# User Input
# -------------------------------------------------
lat_input = st.text_input("Enter Latitude (Decimal or DMS)")
lon_input = st.text_input("Enter Longitude (Decimal or DMS)")

if st.button("Check Location"):

    lat = convert_coord(lat_input)
    lon = convert_coord(lon_input)

    if lat is None or lon is None:
        st.error("Invalid coordinate format")
        st.stop()

    input_point = (lat, lon)

    # -------------------------------------------------
    # P0 Analysis
    # -------------------------------------------------
    p0_results = []
    nearest_p0 = None
    nearest_p0_distance = 999

    for _, row in p0.iterrows():

        p0_point = (row["Latitude"], row["Longitude"])
        distance = geodesic(input_point, p0_point).km

        if distance < nearest_p0_distance:
            nearest_p0_distance = distance
            nearest_p0 = row["Location"]

        if distance <= 1.5:
            p0_results.append({
                "Location": row["Location"],
                "QIS Count": row[p0_qis_col] if p0_qis_col else "",
                "Distance_km": round(distance,3)
            })


    # -------------------------------------------------
    # QIS Analysis
    # -------------------------------------------------
    qis_results = []
    nearest_qis = None
    nearest_qis_distance = 999

    for _, row in qis.iterrows():

        qis_point = (row["Lat"], row["Long"])
        distance = geodesic(input_point, qis_point).km

        if distance < nearest_qis_distance:
            nearest_qis_distance = distance
            nearest_qis = row["QIS Name"]

        qis_results.append({
            "QIS ID": row.get("QIS No.",""),
            "QIS Name": row["QIS Name"],
            "Distance_km": round(distance,3)
        })

    qis_table = pd.DataFrame(qis_results).sort_values("Distance_km").head(10)

    # -------------------------------------------------
    # Work in Progress Deals
    # -------------------------------------------------
    wip_results = []

    for _, row in deals.iterrows():

        deal_point = (row["Latitude"], row["Longitude"])
        distance = geodesic(input_point, deal_point).km

        if distance <= 2:

            wip_results.append({
                "Deal Name": row.get("Deal Name",""),
                "QIS Count": row[deal_qis_col] if deal_qis_col else "",
                "Distance_km": round(distance,3)
            })

    wip_table = pd.DataFrame(wip_results)

    # -------------------------------------------------
    # Feasibility
    # -------------------------------------------------
    st.subheader("Feasibility Result")

    if len(p0_results) > 0:
        st.success("Feasible (P0 exists within 1.5 km)")
    else:
        st.error("Non-Feasible")

    st.write("Nearest P0:", nearest_p0, "| Distance:", round(nearest_p0_distance,3),"km")
    st.write("Nearest QIS:", nearest_qis, "| Distance:", round(nearest_qis_distance,3),"km")

    # -------------------------------------------------
    # Tables
    # -------------------------------------------------
    st.subheader("P0 Locations within 1.5 km")
    st.dataframe(pd.DataFrame(p0_results))

    st.subheader("Nearest QIS Stations")
    st.dataframe(qis_table)

    st.subheader("Nearby Work-in-Progress Sites")
    if not wip_table.empty:
        st.dataframe(wip_table)
    else:
        st.write("No WIP sites nearby")

    # -------------------------------------------------
    # MAP
    # -------------------------------------------------
    st.subheader("Map View")

    m = folium.Map(location=[lat, lon], zoom_start=13)

    # Input location
    folium.Marker(
        [lat, lon],
        popup="Input Location",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    # 1.5 km radius
    folium.Circle(
        location=[lat, lon],
        radius=1500,
        color="blue",
        fill=True,
        fill_opacity=0.1
    ).add_to(m)

    # P0 markers
    for _, row in p0.iterrows():
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=5,
            color="green",
            popup=row["Location"]
        ).add_to(m)

    # QIS markers
    for _, row in qis.iterrows():
        folium.CircleMarker(
            location=[row["Lat"], row["Long"]],
            radius=4,
            color="orange",
            popup=row["QIS Name"]
        ).add_to(m)

    # Deals markers
    for _, row in deals.iterrows():
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=5,
            color="red",
            popup=row.get("Deal Name","Deal")
        ).add_to(m)

    st_folium(m, width=700, height=500)


# -------------------------------------------------
# Footer
# -------------------------------------------------
st.markdown("---")
st.markdown("Created by Manul 🌐")
