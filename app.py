import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.title("Site Feasibility Tool")

# Load data
p0 = pd.read_csv("P0.csv")
qis = pd.read_csv("QIS Locations.csv")

# Convert coordinates to numeric
p0["Latitude"] = pd.to_numeric(p0["Latitude"], errors="coerce")
p0["Longitude"] = pd.to_numeric(p0["Longitude"], errors="coerce")

qis["Lat"] = pd.to_numeric(qis["Lat"], errors="coerce")
qis["Long"] = pd.to_numeric(qis["Long"], errors="coerce")

# Remove bad rows
p0 = p0.dropna(subset=["Latitude", "Longitude"])
qis = qis.dropna(subset=["Lat", "Long"])

lat = st.number_input("Enter Latitude", format="%.6f")
lon = st.number_input("Enter Longitude", format="%.6f")

if st.button("Check Location"):

    input_point = (lat, lon)

    p0_results = []
    qis_results = []

    # Calculate P0 distances
    for _, row in p0.iterrows():

        p0_point = (row["Latitude"], row["Longitude"])
        distance = geodesic(input_point, p0_point).km

        p0_results.append({
            "Location": row["Location"],
            "Distance_km": round(distance, 3)
        })

    # Calculate QIS distances
    for _, row in qis.iterrows():

        qis_point = (row["Lat"], row["Long"])
        distance = geodesic(input_point, qis_point).km

        qis_results.append({
            "QIS Name": row["QIS Name"],
            "Distance_km": round(distance, 3)
        })

    p0_df = pd.DataFrame(p0_results)
    qis_df = pd.DataFrame(qis_results)

    # Sort by distance
    p0_df = p0_df.sort_values("Distance_km")
    qis_df = qis_df.sort_values("Distance_km")

    st.subheader("Nearest P0 Locations")
    st.dataframe(p0_df.head(10))

    st.subheader("Nearest QIS Stations")
    st.dataframe(qis_df.head(10))

    # Apply radius filter
    st.subheader("P0 locations within 1.5 km")

    st.dataframe(p0_df[p0_df["Distance_km"] <= 1.5])

    st.subheader("QIS stations between 3–4 km")

    st.dataframe(qis_df[(qis_df["Distance_km"] >= 3) & (qis_df["Distance_km"] <= 4)])
