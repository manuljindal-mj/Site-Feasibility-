import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.title("Site Feasibility Checker")

# Load data
p0_df = pd.read_csv("P0.csv")
qis_df = pd.read_csv("QIS Locations.csv")

# Convert coordinates to numeric
p0_df["Latitude"] = pd.to_numeric(p0_df["Latitude"], errors="coerce")
p0_df["Longitude"] = pd.to_numeric(p0_df["Longitude"], errors="coerce")

qis_df["Lat"] = pd.to_numeric(qis_df["Lat"], errors="coerce")
qis_df["Long"] = pd.to_numeric(qis_df["Long"], errors="coerce")

# Remove rows with missing coordinates
p0_df = p0_df.dropna(subset=["Latitude", "Longitude"])
qis_df = qis_df.dropna(subset=["Lat", "Long"])

# User inputs
lat = st.number_input("Enter Latitude", format="%.6f")
lon = st.number_input("Enter Longitude", format="%.6f")

if st.button("Check Feasibility"):

    input_point = (float(lat), float(lon))

    feasible = False
    nearest_p0 = None
    nearest_p0_distance = 999

    # Check P0 distance
    for _, row in p0_df.iterrows():

        p0_point = (float(row["Latitude"]), float(row["Longitude"]))
        distance = geodesic(input_point, p0_point).km

        if distance < nearest_p0_distance:
            nearest_p0_distance = distance
            nearest_p0 = row["Location"]

        if distance <= 1.5:
            feasible = True

    # Find nearest QIS station
    nearest_qis = None
    nearest_qis_distance = 999

    for _, row in qis_df.iterrows():

        qis_point = (float(row["Lat"]), float(row["Long"]))
        distance = geodesic(input_point, qis_point).km

        if distance < nearest_qis_distance:
            nearest_qis_distance = distance
            nearest_qis = row["QIS Name"]

    st.subheader("Feasibility Result")

    if feasible:
        st.success("Feasible - Within 1.5 km of P0")
    else:
        st.error("Non-Feasible")

    st.write("Nearest P0 Location:", nearest_p0)
    st.write("Distance to P0 (km):", round(nearest_p0_distance, 3))

    st.write("Nearest QIS Station:", nearest_qis)
    st.write("Distance to QIS (km):", round(nearest_qis_distance, 3))

st.write("")
st.write("Created by Manul 🌐")
