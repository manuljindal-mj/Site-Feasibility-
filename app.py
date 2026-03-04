import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.title("Site Feasibility Tool")

# Load data
p0 = pd.read_csv("P0.csv")
qis = pd.read_csv("QIS Locations.csv")

# Convert coordinates to numbers
p0["Latitude"] = pd.to_numeric(p0["Latitude"], errors="coerce")
p0["Longitude"] = pd.to_numeric(p0["Longitude"], errors="coerce")

qis["Lat"] = pd.to_numeric(qis["Lat"], errors="coerce")
qis["Long"] = pd.to_numeric(qis["Long"], errors="coerce")

# Remove rows with missing coordinates
p0 = p0.dropna(subset=["Latitude", "Longitude"])
qis = qis.dropna(subset=["Lat", "Long"])

lat = st.number_input("Enter Latitude", format="%.6f")
lon = st.number_input("Enter Longitude", format="%.6f")

if st.button("Check Location"):

    input_point = (lat, lon)

    p0_results = []
    qis_results = []

    # Check P0 locations
    for _, row in p0.iterrows():

        p0_point = (row["Latitude"], row["Longitude"])
        distance = geodesic(input_point, p0_point).km

        if distance <= 1.5:
            p0_results.append({
                "P0 Location": row["Location"],
                "Distance (km)": round(distance,2)
            })

    # Check QIS stations
    for _, row in qis.iterrows():

        qis_point = (row["Lat"], row["Long"])
        distance = geodesic(input_point, qis_point).km

        if 3 <= distance <= 4:
            qis_results.append({
                "QIS Station": row["QIS Name"],
                "Distance (km)": round(distance,2)
            })

    st.subheader("P0 locations within 1.5 km")

    if p0_results:
        st.dataframe(pd.DataFrame(p0_results))
    else:
        st.write("No P0 locations nearby")

    st.subheader("QIS stations between 3–4 km")

    if qis_results:
        st.dataframe(pd.DataFrame(qis_results))
    else:
        st.write("No QIS stations in this range")
