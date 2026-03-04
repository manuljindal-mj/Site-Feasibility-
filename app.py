import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import re

st.title("Site Feasibility Tool")

# -----------------------------
# Convert DMS → Decimal
# -----------------------------
def convert_to_decimal(coord):

    if coord is None:
        return None

    coord = str(coord).strip()

    # if already decimal
    try:
        return float(coord)
    except:
        pass

    # DMS format
    pattern = r"(\d+)°(\d+)'([\d\.]+)\"?([NSEW])"
    match = re.match(pattern, coord)

    if match:

        deg, minutes, seconds, direction = match.groups()

        decimal = float(deg) + float(minutes)/60 + float(seconds)/3600

        if direction in ["S","W"]:
            decimal = -decimal

        return decimal

    return None


# -----------------------------
# Load datasets
# -----------------------------
p0 = pd.read_csv("P0.csv")
qis = pd.read_csv("QIS Locations.csv")

# remove duplicate QIS
qis = qis.drop_duplicates(subset=["QIS No."])

# clean coordinates
p0["Latitude"] = pd.to_numeric(p0["Latitude"], errors="coerce")
p0["Longitude"] = pd.to_numeric(p0["Longitude"], errors="coerce")

qis["Lat"] = pd.to_numeric(qis["Lat"], errors="coerce")
qis["Long"] = pd.to_numeric(qis["Long"], errors="coerce")

p0 = p0.dropna(subset=["Latitude","Longitude"])
qis = qis.dropna(subset=["Lat","Long"])


# -----------------------------
# User input
# -----------------------------
lat_input = st.text_input("Enter Latitude (Decimal or DMS)")
lon_input = st.text_input("Enter Longitude (Decimal or DMS)")

if st.button("Check Location"):

    lat = convert_to_decimal(lat_input)
    lon = convert_to_decimal(lon_input)

    if lat is None or lon is None:
        st.error("Invalid coordinates format")
        st.stop()

    input_point = (lat, lon)

    # -----------------------------
    # P0 Distance Calculation
    # -----------------------------
    p0_results = []
    nearest_p0_distance = 999
    nearest_p0 = None

    for _, row in p0.iterrows():

        p0_point = (row["Latitude"], row["Longitude"])

        distance = geodesic(input_point, p0_point).km

        if distance < nearest_p0_distance:
            nearest_p0_distance = distance
            nearest_p0 = row["Location"]

        if distance <= 1.5:
            p0_results.append({
                "Location": row["Location"],
                "Latitude": row["Latitude"],
                "Longitude": row["Longitude"],
                "Distance_km": round(distance,3)
            })


    # -----------------------------
    # QIS Distance Calculation
    # -----------------------------
    qis_results = []
    nearest_qis_distance = 999
    nearest_qis = None

    for _, row in qis.iterrows():

        qis_point = (row["Lat"], row["Long"])

        distance = geodesic(input_point, qis_point).km

        if distance < nearest_qis_distance:
            nearest_qis_distance = distance
            nearest_qis = row["QIS Name"]

        qis_results.append({
            "QIS ID": row["QIS No."],
            "QIS Name": row["QIS Name"],
            "Latitude": row["Lat"],
            "Longitude": row["Long"],
            "Distance_km": round(distance,3)
        })


    p0_table = pd.DataFrame(p0_results)
    qis_table = pd.DataFrame(qis_results).sort_values("Distance_km").head(10)


    # -----------------------------
    # Feasibility Result
    # -----------------------------
    st.subheader("Feasibility Result")

    if len(p0_table) > 0:
        st.success("Feasible (P0 exists within 1.5 km)")
    else:
        st.error("Non-Feasible")


    # -----------------------------
    # Nearest Locations
    # -----------------------------
    st.write("Nearest P0:", nearest_p0)
    st.write("Distance to nearest P0 (km):", round(nearest_p0_distance,3))

    st.write("Nearest QIS:", nearest_qis)
    st.write("Distance to nearest QIS (km):", round(nearest_qis_distance,3))


    # -----------------------------
    # Tables
    # -----------------------------
    st.subheader("P0 Locations within 1.5 km")

    if not p0_table.empty:
        st.dataframe(p0_table)
    else:
        st.write("No P0 locations within 1.5 km")


    st.subheader("Nearest QIS Stations")

    st.dataframe(qis_table)


# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.markdown("Created by Manul 🌐")
