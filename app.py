import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.title("Site Feasibility Tool")

p0 = pd.read_csv("P0.csv")
qis = pd.read_csv("QIS Locations.csv")

lat = st.number_input("Enter Latitude", format="%.6f")
lon = st.number_input("Enter Longitude", format="%.6f")

if st.button("Check Location"):

    input_point = (lat, lon)

    p0_results = []
    qis_results = []

    for _, row in p0.iterrows():

        p0_point = (row["lat"], row["lon"])
        distance = geodesic(input_point, p0_point).km

        if distance <= 1.5:

            p0_results.append({
                "P0 Location": row["location_name"],
                "Distance (km)": round(distance,2)
            })

    for _, row in qis.iterrows():

        qis_point = (row["lat"], row["lon"])
        distance = geodesic(input_point, qis_point).km

        if 3 <= distance <= 4:

            qis_results.append({
                "QIS Station": row["station_name"],
                "Distance (km)": round(distance,2)
            })

    st.subheader("P0 locations within 1.5 km")

    if p0_results:
        st.dataframe(pd.DataFrame(p0_results))
    else:
        st.write("No P0 locations nearby")

    st.subheader("QIS stations within 3–4 km")

    if qis_results:
        st.dataframe(pd.DataFrame(qis_results))
    else:
        st.write("No QIS stations in this range")
