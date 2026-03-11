import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import zipfile
import xml.etree.ElementTree as ET
import re
from streamlit_js_eval import get_geolocation

st.set_page_config(layout="wide")
st.title("Site Feasibility Tool")

# ------------------------------------------------
# SESSION STATE INIT
# ------------------------------------------------

if "lat" not in st.session_state:
    st.session_state.lat = ""

if "lon" not in st.session_state:
    st.session_state.lon = ""

if "geo_requested" not in st.session_state:
    st.session_state.geo_requested = False

# ------------------------------------------------
# Coordinate Conversion
# ------------------------------------------------

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


# ------------------------------------------------
# Coordinate Validation
# ------------------------------------------------

def valid_coord(lat, lon):

    if pd.isna(lat) or pd.isna(lon):
        return False

    if lat < -90 or lat > 90:
        return False

    if lon < -180 or lon > 180:
        return False

    return True


# ------------------------------------------------
# Load Darkstore KMZ
# ------------------------------------------------

def load_kmz(file):

    rows = []

    try:

        with zipfile.ZipFile(file, 'r') as z:

            for name in z.namelist():

                if name.endswith(".kml"):

                    with z.open(name) as f:

                        root = ET.parse(f).getroot()

                        current_name = "Unknown"

                        for elem in root.iter():

                            if "name" in elem.tag:
                                current_name = elem.text or "Unknown"

                            if "coordinates" in elem.tag:

                                coord = elem.text.strip()
                                lon, lat, *_ = coord.split(",")

                                try:

                                    lat = float(lat)
                                    lon = float(lon)

                                    if valid_coord(lat, lon):

                                        rows.append({
                                            "Name": current_name,
                                            "Latitude": lat,
                                            "Longitude": lon
                                        })

                                except:
                                    continue

    except:
        st.warning("KMZ could not be loaded")

    return pd.DataFrame(rows)


# ------------------------------------------------
# Load Data
# ------------------------------------------------

@st.cache_data
def load_data():

    p0 = pd.read_csv("P0.csv")
    qis = pd.read_csv("QIS Locations.csv")
    deals = pd.read_csv("deals.csv")

    darkstores = load_kmz("darkstores.kmz")

    p0["Latitude"] = pd.to_numeric(p0["Latitude"], errors="coerce")
    p0["Longitude"] = pd.to_numeric(p0["Longitude"], errors="coerce")

    qis["Lat"] = pd.to_numeric(qis["Lat"], errors="coerce")
    qis["Long"] = pd.to_numeric(qis["Long"], errors="coerce")

    deals["Latitude"] = pd.to_numeric(deals["Latitude"], errors="coerce")
    deals["Longitude"] = pd.to_numeric(deals["Longitude"], errors="coerce")

    return p0, qis, deals, darkstores


p0, qis, deals, darkstores = load_data()

# ------------------------------------------------
# QIS Recommendation
# ------------------------------------------------

def suggested_qis(p0_count):

    if p0_count <= 1:
        return 0
    elif p0_count <= 3:
        return 1
    elif p0_count <= 6:
        return 2
    elif p0_count <= 10:
        return 3
    else:
        return 4


# ------------------------------------------------
# SCORING
# ------------------------------------------------

def score_distance(d):

    if d < 0.25:
        return 5
    elif d < 0.5:
        return 4
    elif d < 1:
        return 3
    elif d < 2:
        return 2
    else:
        return 1


def score_arterial(v):

    mapping = {
        ">1km":1,
        "<1km":2,
        "<500m":3,
        "<250m":4,
        "<100m":5
    }

    return mapping[v]


def score_access(v):

    mapping = {
        "<10ft":1,
        "10-20ft":2,
        "20-30ft":3,
        "30-40ft":4,
        ">40ft":5
    }

    return mapping[v]


def score_binary(v):
    return 4 if v == "Yes" else 2


# ------------------------------------------------
# SIDEBAR
# ------------------------------------------------

st.sidebar.header("Site Inputs")

if st.sidebar.button("Get My Location 📍"):
    st.session_state.geo_requested = True


# Fetch location
if st.session_state.geo_requested:

    loc = get_geolocation()

    if loc:

        st.session_state.lat = str(loc["coords"]["latitude"])
        st.session_state.lon = str(loc["coords"]["longitude"])

        st.session_state.geo_requested = False


st.sidebar.text_input("Latitude", key="lat")
st.sidebar.text_input("Longitude", key="lon")

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


run = st.sidebar.button("Run Feasibility")

# ------------------------------------------------
# RUN ANALYSIS
# ------------------------------------------------

if run:

    lat = convert_coord(st.session_state.lat)
    lon = convert_coord(st.session_state.lon)

    if lat is None or lon is None:
        st.error("Invalid coordinates")
        st.stop()

    input_point = (lat, lon)

    # P0
    p0_results = []
    p0_count = 0

    for _, row in p0.iterrows():

        dist = geodesic(input_point,(row["Latitude"],row["Longitude"])).km

        if dist <= 1.5:

            p0_count += 1

            p0_results.append({
                "Location":row.get("Location",""),
                "Distance_km":round(dist,2)
            })

    # QIS
    existing_qis = 0

    for _, row in qis.iterrows():

        dist = geodesic(input_point,(row["Lat"],row["Long"])).km

        if dist <= 1.5:
            existing_qis += 1

    # Darkstore
    nearest_dark = 999
    nearest_dark_name = "Unknown"

    for _, row in darkstores.iterrows():

        dist = geodesic(input_point,(row["Latitude"],row["Longitude"])).km

        if dist < nearest_dark:

            nearest_dark = dist
            nearest_dark_name = row.get("Name","Unknown")

    recommended_qis = suggested_qis(p0_count)

    # Score
    score = (
        score_distance(nearest_dark)*0.20 +
        score_arterial(arterial_distance)*0.15 +
        score_access(access_width)*0.15 +
        score_binary(open_24)*0.10 +
        score_binary(parking)*0.05
    ) / 5


    # ------------------------------------------------
    # RESULTS
    # ------------------------------------------------

    st.header("Feasibility Result")
    st.metric("Score", round(score,2))

    if score > 0.6:
        st.success("Approved")
    elif score >= 0.3:
        st.warning("Feasible")
    else:
        st.error("Not Feasible")


    st.subheader("QIS Planning")

    c1,c2,c3 = st.columns(3)

    c1.metric("P0 Demand Points", p0_count)
    c2.metric("Existing QIS", existing_qis)
    c3.metric("Suggested QIS", recommended_qis)


    # ------------------------------------------------
    # MAP
    # ------------------------------------------------

    st.subheader("Map")

    m = folium.Map(location=[lat,lon], zoom_start=13)

    folium.Marker([lat,lon], popup="Input Site", icon=folium.Icon(color="blue")).add_to(m)

    folium.Circle([lat,lon],radius=1500,color="blue",fill=True,fill_opacity=0.1).add_to(m)

    for _,row in p0.iterrows():
        folium.CircleMarker([row["Latitude"],row["Longitude"]],radius=4,color="green").add_to(m)

    for _,row in qis.iterrows():
        folium.CircleMarker([row["Lat"],row["Long"]],radius=4,color="orange").add_to(m)

    for _,row in darkstores.iterrows():
        folium.CircleMarker([row["Latitude"],row["Longitude"]],radius=4,color="purple").add_to(m)

    for _,row in deals.iterrows():
        folium.CircleMarker([row["Latitude"],row["Longitude"]],radius=4,color="red").add_to(m)

    st_folium(m,width=900,height=600)

st.markdown("---")
st.markdown("Created by Manul 🚀")
