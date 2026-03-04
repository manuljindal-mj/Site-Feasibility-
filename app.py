import streamlit as st
import pandas as pd
from geopy.distance import geodesic

# Page Title
st.title("Site Feasibility Tool")

# Load datasets
p0_data = pd.read_csv("P0.csv")
qis_data = pd.read_csv("QIS Locations.csv")

# Convert coordinates to numeric values
p0_data["Latitude"] = pd.to_numeric(p0_data["Latitude"], errors="coerce")
p0_data["Longitude"] = pd.to_numeric(p0_data["Longitude"], errors="coerce")

qis_data["Lat"] = pd.to_numeric(qis_data["Lat"], errors="coerce")
qis_data["Long"] = pd.to_numeric(qis_data["Long"], errors="coerce")

# Remove rows with missing coordinates
p0_data = p0_data.dropna(subset=["Latitude", "Longitude"])
qis_data = qis_data.dropna(subset=["Lat", "Long"])

# User inputs
latitude = st.number_input("Enter Latitude", format="%.6f")
longitude = st.number_input("Enter Longitude", format="%.6f")

# Run check
if st.button("Check Location"):

    input_point = (latitude, longitude)

    nearby_p0 = []
    nearby_qis = []

    # Check P0 locations within 1.5 km radius
    for _, row in p0_data.iterrows():

        p0_point = (row["Latitude"], row["Longitude"])
        distance = geodesic(input_point, p0_point).km

        if distance <= 1.5:

            nearby_p0.append({
                "P0 Location": row["Location"],
                "Distance (km)": round(distance, 3)
            })

    # Check QIS stations between 3–4 km
    for _, row in qis_data.iterrows():

        qis_point = (row["Lat"], row["Long"])
        distance = geodesic(input_point, qis_point).km

        if 3 <= distance <= 4:

            nearby_qis.append({
                "QIS Station": row["QIS Name"],
                "Distance (km)": round(distance, 3)
            })

    # Display P0 results
    st.subheader("P0 locations within 1.5 km")

    if nearby_p0:
        st.dataframe(pd.DataFrame(nearby_p0))
    else:
        st.write("No P0 locations nearby")

    # Display QIS results
    st.subheader("QIS stations between 3–4 km")

    if nearby_qis:
        st.dataframe(pd.DataFrame(nearby_qis))
    else:
        st.write("No QIS stations in this range")
