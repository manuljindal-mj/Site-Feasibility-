import streamlit as st
import pandas as pd
from geopy.distance import geodesic

# ------------------------------

# Page Title

# ------------------------------

st.title("Site Feasibility Tool")

# ------------------------------

# Load Data

# ------------------------------

p0_df = pd.read_csv("P0.csv")
qis_df = pd.read_csv("QIS Locations.csv")

# ------------------------------

# Clean Coordinates

# ------------------------------

p0_df["Latitude"] = pd.to_numeric(p0_df["Latitude"], errors="coerce")
p0_df["Longitude"] = pd.to_numeric(p0_df["Longitude"], errors="coerce")

qis_df["Lat"] = pd.to_numeric(qis_df["Lat"], errors="coerce")
qis_df["Long"] = pd.to_numeric(qis_df["Long"], errors="coerce")

# Remove rows with invalid coordinates

p0_df = p0_df.dropna(subset=["Latitude", "Longitude"])
qis_df = qis_df.dropna(subset=["Lat", "Long"])

# ------------------------------

# User Inputs

# ------------------------------

input_lat = st.number_input("Enter Latitude", format="%.6f")
input_lon = st.number_input("Enter Longitude", format="%.6f")

# ------------------------------

# Run Calculation

# ------------------------------

if st.button("Check Location"):

```
input_point = (float(input_lat), float(input_lon))

p0_results = []
qis_results = []

# ------------------------------
# Calculate distance to P0 sites
# ------------------------------
for _, row in p0_df.iterrows():

    p0_point = (float(row["Latitude"]), float(row["Longitude"]))
    distance = geodesic(input_point, p0_point).km

    p0_results.append({
        "Location": row["Location"],
        "Latitude": row["Latitude"],
        "Longitude": row["Longitude"],
        "Distance_km": round(distance, 3)
    })

p0_results_df = pd.DataFrame(p0_results)
p0_results_df = p0_results_df.sort_values("Distance_km")

# ------------------------------
# Calculate distance to QIS sites
# ------------------------------
for _, row in qis_df.iterrows():

    qis_point = (float(row["Lat"]), float(row["Long"]))
    distance = geodesic(input_point, qis_point).km

    qis_results.append({
        "QIS Name": row["QIS Name"],
        "Latitude": row["Lat"],
        "Longitude": row["Long"],
        "Distance_km": round(distance, 3)
    })

qis_results_df = pd.DataFrame(qis_results)
qis_results_df = qis_results_df.sort_values("Distance_km")

# ------------------------------
# Display nearest locations
# ------------------------------
st.subheader("Nearest P0 Locations")
st.dataframe(p0_results_df.head(10))

st.subheader("Nearest QIS Stations")
st.dataframe(qis_results_df.head(10))

# ------------------------------
# Radius Filters
# ------------------------------
st.subheader("P0 Locations within 1.5 km")
p0_radius = p0_results_df[p0_results_df["Distance_km"] <= 1.5]

if not p0_radius.empty:
    st.dataframe(p0_radius)
else:
    st.write("No P0 locations within 1.5 km")

st.subheader("QIS Stations between 3 km and 4 km")

qis_radius = qis_results_df[
    (qis_results_df["Distance_km"] >= 3) &
    (qis_results_df["Distance_km"] <= 4)
]

if not qis_radius.empty:
    st.dataframe(qis_radius)
else:
    st.write("No QIS stations in this range")
```
