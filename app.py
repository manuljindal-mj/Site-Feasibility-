import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import re

st.title("Site Feasibility Checker")

# Function to convert DMS to decimal
def dms_to_decimal(coord):

    if isinstance(coord, float) or isinstance(coord, int):
        return float(coord)

    coord = coord.strip()

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


# Load data
p0_df = pd.read_csv("P0.csv")
qis_df = pd.read_csv("QIS Locations.csv")

# Clean coordinates
p0_df["Latitude"] = pd.to_numeric(p0_df["Latitude"], errors="coerce")
p0_df["Longitude"] = pd.to_numeric(p0_df["Longitude"], errors="coerce")

qis_df["Lat"] = pd.to_numeric(qis_df["Lat"], errors="coerce")
qis_df["Long"] = pd.to_numeric(qis_df["Long"], errors="coerce")

p0_df = p0_df.dropna(subset=["Latitude","Longitude"])
qis_df = qis_df.dropna(subset=["Lat","Long"])


# Input
lat_input = st.text_input("Enter Latitude (Decimal or DMS)")
lon_input = st.text_input("Enter Longitude (Decimal or DMS)")

if st.button("Check Feasibility"):

    lat = dms_to_decimal(lat_input)
    lon = dms_to_decimal(lon_input)

    if lat is None or lon is None:
        st.error("Invalid coordinate format")

    else:

        input_point = (lat, lon)

        feasible = False
        nearest_p0 = None
        nearest_p0_distance = 999

        p0_results = []

        # Check P0
        for _, row in p0_df.iterrows():

            p0_point = (row["Latitude"], row["Longitude"])
            distance = geodesic(input_point, p0_point).km

            if distance < nearest_p0_distance:
                nearest_p0_distance = distance
                nearest_p0 = row["Location"]

            if distance <= 1.5:
                feasible = True

                p0_results.append({
                    "Location": row["Location"],
                    "Latitude": row["Latitude"],
                    "Longitude": row["Longitude"],
                    "Distance_km": round(distance,3)
                })


        # QIS analysis
        nearest_qis = None
        nearest_qis_distance = 999

        qis_results = []

        for _, row in qis_df.iterrows():

            qis_point = (row["Lat"], row["Long"])
            distance = geodesic(input_point, qis_point).km

            if distance < nearest_qis_distance:
                nearest_qis_distance = distance
                nearest_qis = row["QIS Name"]

            qis_results.append({
                "QIS ID": row.get("QIS ID",""),
                "QIS Name": row["QIS Name"],
                "Latitude": row["Lat"],
                "Longitude": row["Long"],
                "Distance_km": round(distance,3)
            })


        qis_table = pd.DataFrame(qis_results).sort_values("Distance_km").head(10)
        p0_table = pd.DataFrame(p0_results)


        st.subheader("Feasibility Result")

        if feasible:
            st.success("Feasible (Within 1.5 km of P0)")
        else:
            st.error("Non-Feasible")


        st.write("Nearest P0:", nearest_p0)
        st.write("Distance to P0 (km):", round(nearest_p0_distance,3))

        st.write("Nearest QIS:", nearest_qis)
        st.write("Distance to QIS (km):", round(nearest_qis_distance,3))


        st.subheader("P0 Locations within 1.5 km")

        if not p0_table.empty:
            st.dataframe(p0_table)
        else:
            st.write("No P0 locations within 1.5 km")


        st.subheader("Nearest QIS Stations")

        st.dataframe(qis_table)


st.write("")
st.write("Created by Manul 🌐")
