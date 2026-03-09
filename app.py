import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import zipfile
import xml.etree.ElementTree as ET
import re

st.set_page_config(layout="wide")

st.title("EV Site Feasibility Tool")

# ---------------------------------------------------
# Coordinate conversion
# ---------------------------------------------------

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


# ---------------------------------------------------
# Validate coordinates
# ---------------------------------------------------

def valid_coord(lat, lon):

    if pd.isna(lat) or pd.isna(lon):
        return False

    if lat < -90 or lat > 90:
        return False

    if lon < -180 or lon > 180:
        return False

    return True


# ---------------------------------------------------
# Load KMZ Darkstores
# ---------------------------------------------------

def load_kmz(file):

    coords = []

    with zipfile.ZipFile(file, 'r') as z:

        for name in z.namelist():

            if name.endswith(".kml"):

                with z.open(name) as f:

                    root = ET.parse(f).getroot()

                    current_name = None

                    for elem in root.iter():

                        if "name" in elem.tag:
                            current_name = elem.text

                        if "coordinates" in elem.tag:

                            coord = elem.text.strip()

                            lon, lat, *_ = coord.split(",")

                            try:

                                lat = float(lat)
                                lon = float(lon)

                                if valid_coord(lat, lon):

                                    coords.append({
                                        "Name": current_name,
                                        "Latitude": lat,
                                        "Longitude": lon
                                    })

                            except:
                                continue

    return pd.DataFrame(coords)


# ---------------------------------------------------
# Load Data
# ---------------------------------------------------

@st.cache_data
def load_data():

    p0 = pd.read_csv("P0.csv")
    qis = pd.read_csv("QIS Locations.csv")
    deals = pd.read_csv("deals.csv")

    darkstores = load_kmz("darkstores.kmz")

    p0.columns = p0.columns.str.strip()
    qis.columns = qis.columns.str.strip()
    deals.columns = deals.columns.str.strip()

    p0["Latitude"] = pd.to_numeric(p0["Latitude"], errors="coerce")
    p0["Longitude"] = pd.to_numeric(p0["Longitude"], errors="coerce")

    qis["Lat"] = pd.to_numeric(qis["Lat"], errors="coerce")
    qis["Long"] = pd.to_numeric(qis["Long"], errors="coerce")

    deals["Latitude"] = pd.to_numeric(deals["Latitude"], errors="coerce")
    deals["Longitude"] = pd.to_numeric(deals["Longitude"], errors="coerce")

    p0 = p0[p0.apply(lambda r: valid_coord(r["Latitude"], r["Longitude"]), axis=1)]
    qis = qis[qis.apply(lambda r: valid_coord(r["Lat"], r["Long"]), axis=1)]
    deals = deals[deals.apply(lambda r: valid_coord(r["Latitude"], r["Longitude"]), axis=1)]

    return p0, qis, deals, darkstores


p0, qis, deals, darkstores = load_data()


# ---------------------------------------------------
# Scoring functions
# ---------------------------------------------------

def score_distance(distance):

    if distance < 0.25:
        return 5
    elif distance < 0.5:
        return 4
    elif distance < 1:
        return 3
    elif distance < 2:
        return 2
    else:
        return 1


def score_arterial(val):

    mapping = {
        ">1km":1,
        "<1km":2,
        "<500m":3,
        "<250m":4,
        "<100m":5
    }

    return mapping[val]


def score_access(val):

    mapping = {
        "<10ft":1,
        "10-20ft":2,
        "20-30ft":3,
        "30-40ft":4,
        ">40ft":5
    }

    return mapping[val]


def score_binary(val):

    return 4 if val == "Yes" else 2


# ---------------------------------------------------
# Sidebar Inputs
# ---------------------------------------------------

st.sidebar.header("Site Inputs")

lat_input = st.sidebar.text_input("Latitude")
lon_input = st.sidebar.text_input("Longitude")

arterial_distance = st.sidebar.selectbox(
    "Distance from Arterial Road",
    [">1km","<1km","<500m","<250m","<100m"]
)

access_width = st.sidebar.selectbox(
    "Access Road Width",
    ["<10ft","10-20ft","20-30ft","30-40ft",">40ft"]
)

open_24 = st.sidebar.selectbox("24x7 Possible", ["No","Yes"])
parking = st.sidebar.selectbox("Parking Available", ["No","Yes"])

if st.sidebar.button("Run Feasibility"):
    st.session_state["run"] = True


# ---------------------------------------------------
# Run Analysis
# ---------------------------------------------------

if "run" in st.session_state:

    lat = convert_coord(lat_input)
    lon = convert_coord(lon_input)

    if lat is None or lon is None:

        st.error("Invalid coordinates")
        st.stop()

    input_point = (lat, lon)

    # -----------------------
    # P0 nearby
    # -----------------------

    p0_results = []

    for _, row in p0.iterrows():

        dist = geodesic(input_point,(row["Latitude"],row["Longitude"])).km

        if dist <= 1.5:

            p0_results.append({
                "Location": row.get("Location",""),
                "Distance_km": round(dist,2)
            })


    # -----------------------
    # QIS nearest
    # -----------------------

    qis_results = []
    nearest_qis = 999

    for _, row in qis.iterrows():

        dist = geodesic(input_point,(row["Lat"],row["Long"])).km

        if dist < nearest_qis:
            nearest_qis = dist

        qis_results.append({
            "QIS": row.get("QIS Name",""),
            "Distance_km": round(dist,2)
        })

    qis_table = pd.DataFrame(qis_results).sort_values("Distance_km").head(10)


    # -----------------------
    # Darkstores
    # -----------------------

    nearest_dark = 999
    nearest_dark_name = None

    for _, row in darkstores.iterrows():

        dist = geodesic(input_point,(row["Latitude"],row["Longitude"])).km

        if dist < nearest_dark:

            nearest_dark = dist
            nearest_dark_name = row["Name"]


    # -----------------------
    # Deals nearby
    # -----------------------

    deal_results = []

    for _, row in deals.iterrows():

        dist = geodesic(input_point,(row["Latitude"],row["Longitude"])).km

        if dist <= 2:

            deal_results.append({
                "Deal": row.get("Deal Name",""),
                "Distance": round(dist,2)
            })

    deal_table = pd.DataFrame(deal_results)


    # -----------------------
    # Scoring
    # -----------------------

    demand_score = score_distance(nearest_dark)
    arterial_score = score_arterial(arterial_distance)
    access_score = score_access(access_width)
    open_score = score_binary(open_24)
    parking_score = score_binary(parking)

    weighted_score = (
        demand_score*0.20 +
        arterial_score*0.15 +
        access_score*0.15 +
        open_score*0.10 +
        parking_score*0.05
    )

    normalized_score = weighted_score / 5


    # -----------------------
    # Result
    # -----------------------

    st.header("Feasibility Result")

    st.metric("Score", round(normalized_score,2))

    if normalized_score > 0.5:
        st.success("Feasible")
    else:
        st.error("Not Feasible")


    # -----------------------
    # Tables
    # -----------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("P0 within 1.5km")
        st.dataframe(pd.DataFrame(p0_results))

        st.subheader("Nearest QIS")
        st.dataframe(qis_table)

    with col2:

        st.subheader("Nearby Deals")

        if deal_table.empty:
            st.write("No deals nearby")
        else:
            st.dataframe(deal_table)

        st.write(
            "Nearest Darkstore:",
            nearest_dark_name,
            "| Distance:",
            round(nearest_dark,2),
            "km"
        )


    # -----------------------
    # Map
    # -----------------------

    st.subheader("Map")

    m = folium.Map(location=[lat,lon], zoom_start=13)

    folium.Marker(
        [lat,lon],
        popup="Input Site",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    folium.Circle(location=[lat,lon],radius=1500,color="blue",fill=True,fill_opacity=0.1).add_to(m)

    for _, row in p0.iterrows():

        folium.CircleMarker(
            [row["Latitude"],row["Longitude"]],
            radius=5,
            color="green",
            popup=row.get("Location","P0")
        ).add_to(m)

    for _, row in qis.iterrows():

        folium.CircleMarker(
            [row["Lat"],row["Long"]],
            radius=4,
            color="orange",
            popup=row.get("QIS Name","QIS")
        ).add_to(m)

    for _, row in darkstores.iterrows():

        folium.CircleMarker(
            [row["Latitude"],row["Longitude"]],
            radius=4,
            color="purple",
            popup=row["Name"]
        ).add_to(m)

    for _, row in deals.iterrows():

        folium.CircleMarker(
            [row["Latitude"],row["Longitude"]],
            radius=5,
            color="red",
            popup=row.get("Deal Name","Deal")
        ).add_to(m)

    st_folium(m, width=900, height=600)


st.markdown("---")
st.markdown("Created by Manul 🚀")
