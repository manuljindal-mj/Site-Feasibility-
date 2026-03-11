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
# SESSION STATE
# ------------------------------------------------

for key in ["lat","lon","fetch_location","run"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ------------------------------------------------
# COORDINATE UTILITIES
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


def valid_coord(lat, lon):

    if pd.isna(lat) or pd.isna(lon):
        return False

    try:
        lat = float(lat)
        lon = float(lon)
    except:
        return False

    if lat < -90 or lat > 90:
        return False

    if lon < -180 or lon > 180:
        return False

    return True


def safe_distance(point, lat, lon):

    if not valid_coord(lat,lon):
        return None

    try:
        return geodesic(point,(lat,lon)).km
    except:
        return None


# ------------------------------------------------
# LOAD KMZ
# ------------------------------------------------

def load_kmz(file):

    rows = []

    try:

        with zipfile.ZipFile(file,'r') as z:

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

                                try:

                                    lon,lat,_ = coord.split(",")

                                    lat = float(lat)
                                    lon = float(lon)

                                    if valid_coord(lat,lon):

                                        rows.append({
                                            "Name":current_name,
                                            "Latitude":lat,
                                            "Longitude":lon
                                        })

                                except:
                                    continue

    except:
        st.warning("KMZ loading failed")

    return pd.DataFrame(rows)


# ------------------------------------------------
# LOAD DATA
# ------------------------------------------------

@st.cache_data
def load_data():

    p0 = pd.read_csv("P0.csv")
    qis = pd.read_csv("QIS Locations.csv")
    deals = pd.read_csv("deals.csv")

    darkstores = load_kmz("darkstores.kmz")

    p0.columns = p0.columns.str.strip()
    qis.columns = qis.columns.str.strip()
    deals.columns = deals.columns.str.strip()

    p0["Latitude"] = pd.to_numeric(p0["Latitude"],errors="coerce")
    p0["Longitude"] = pd.to_numeric(p0["Longitude"],errors="coerce")

    qis["Lat"] = pd.to_numeric(qis["Lat"],errors="coerce")
    qis["Long"] = pd.to_numeric(qis["Long"],errors="coerce")

    deals["Latitude"] = pd.to_numeric(deals["Latitude"],errors="coerce")
    deals["Longitude"] = pd.to_numeric(deals["Longitude"],errors="coerce")

    p0 = p0.dropna(subset=["Latitude","Longitude"])
    qis = qis.dropna(subset=["Lat","Long"])
    deals = deals.dropna(subset=["Latitude","Longitude"])

    return p0,qis,deals,darkstores


p0,qis,deals,darkstores = load_data()


# ------------------------------------------------
# SCORING FUNCTIONS
# ------------------------------------------------

def score_distance(d):

    if d is None:
        return 1

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
# SIDEBAR
# ------------------------------------------------

st.sidebar.header("Site Inputs")

if st.sidebar.button("Get My Location 📍"):
    st.session_state.fetch_location = True

if st.session_state.fetch_location:

    loc = get_geolocation()

    if loc:

        st.session_state.lat = str(loc["coords"]["latitude"])
        st.session_state.lon = str(loc["coords"]["longitude"])
        st.session_state.fetch_location = False
        st.sidebar.success("Location captured")

lat_input = st.sidebar.text_input("Latitude",value=st.session_state.lat)
lon_input = st.sidebar.text_input("Longitude",value=st.session_state.lon)

arterial_distance = st.sidebar.selectbox(
    "Distance from Arterial Road",
    [">1km","<1km","<500m","<250m","<100m"]
)

access_width = st.sidebar.selectbox(
    "Access Road Width",
    ["<10ft","10-20ft","20-30ft","30-40ft",">40ft"]
)

open_24 = st.sidebar.selectbox("24x7 Possible",["No","Yes"])
parking = st.sidebar.selectbox("Parking Available",["No","Yes"])

if st.sidebar.button("Run Feasibility"):
    st.session_state.run = True


# ------------------------------------------------
# RUN ANALYSIS
# ------------------------------------------------

if st.session_state.run:

    lat = convert_coord(lat_input)
    lon = convert_coord(lon_input)

    if lat is None or lon is None:

        st.error("Invalid coordinates")
        st.stop()

    input_point = (lat,lon)

    # ---------------- P0 ----------------

    p0_results = []
    p0_count = 0

    for _,row in p0.iterrows():

        dist = safe_distance(input_point,row["Latitude"],row["Longitude"])

        if dist and dist <= 1.5:

            p0_count += 1

            p0_results.append({
                "Location":row.get("Location",""),
                "Distance_km":round(dist,2)
            })


    # ---------------- QIS ----------------

    qis_results = []
    existing_qis = 0
    nearest_qis = None

    for _,row in qis.iterrows():

        dist = safe_distance(input_point,row["Lat"],row["Long"])

        if dist is None:
            continue

        if dist <= 1.5:
            existing_qis += 1

        if nearest_qis is None or dist < nearest_qis:
            nearest_qis = dist

        qis_results.append({
            "QIS":row.get("QIS Name",""),
            "Distance_km":round(dist,2)
        })

    qis_table = pd.DataFrame(qis_results).sort_values("Distance_km").head(10)


    # ---------------- DARKSTORES ----------------

    nearest_dark = None
    nearest_dark_name = "Unknown"

    for _,row in darkstores.iterrows():

        dist = safe_distance(input_point,row["Latitude"],row["Longitude"])

        if dist is None:
            continue

        if nearest_dark is None or dist < nearest_dark:

            nearest_dark = dist
            nearest_dark_name = row.get("Name","Unknown")


    # ---------------- DEALS ----------------

    deal_results = []

    for _,row in deals.iterrows():

        dist = safe_distance(input_point,row["Latitude"],row["Longitude"])

        if dist and dist <= 2:

            deal_results.append({
                "Deal":row.get("Deal Name",""),
                "Distance":round(dist,2)
            })

    deal_table = pd.DataFrame(deal_results)


    # ---------------- SCORING ----------------

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


    # ------------------------------------------------
    # RESULTS
    # ------------------------------------------------

    st.header("Feasibility Result")

    st.metric("Score",round(normalized_score,2))

    if normalized_score > 0.6:
        st.success("Approved")
    elif normalized_score >= 0.3:
        st.warning("Feasible")
    else:
        st.error("Not Feasible")


    # ---------------- QIS Planning ----------------

    recommended_qis = suggested_qis(p0_count)

    st.subheader("QIS Planning")

    col1,col2,col3 = st.columns(3)

    col1.metric("P0 Demand Points",p0_count)
    col2.metric("Existing QIS",existing_qis)
    col3.metric("Suggested QIS",recommended_qis)


    # ---------------- TABLES ----------------

    colA,colB = st.columns(2)

    with colA:

        st.subheader("P0 within 1.5km")
        st.dataframe(pd.DataFrame(p0_results))

        st.subheader("Nearest QIS")
        st.dataframe(qis_table)

    with colB:

        st.subheader("Nearby Deals")

        if deal_table.empty:
            st.write("No deals nearby")
        else:
            st.dataframe(deal_table)

        if nearest_dark:
            st.write(
                f"Nearest Darkstore: {nearest_dark_name} | {round(nearest_dark,2)} km"
            )


    # ------------------------------------------------
    # MAP
    # ------------------------------------------------

    st.subheader("Map")

    m = folium.Map(location=[lat,lon],zoom_start=13)

    folium.Marker(
        [lat,lon],
        popup="Input Site",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    folium.Circle(
        [lat,lon],
        radius=1500,
        color="blue",
        fill=True,
        fill_opacity=0.1
    ).add_to(m)

    for _,row in p0.iterrows():
        folium.CircleMarker(
            [row["Latitude"],row["Longitude"]],
            radius=5,
            color="green"
        ).add_to(m)

    for _,row in qis.iterrows():
        folium.CircleMarker(
            [row["Lat"],row["Long"]],
            radius=4,
            color="orange"
        ).add_to(m)

    for _,row in darkstores.iterrows():
        folium.CircleMarker(
            [row["Latitude"],row["Longitude"]],
            radius=4,
            color="purple",
            popup=row.get("Name","Unknown")
        ).add_to(m)

    for _,row in deals.iterrows():
        folium.CircleMarker(
            [row["Latitude"],row["Longitude"]],
            radius=5,
            color="red"
        ).add_to(m)

    st_folium(m,width=900,height=600)


st.markdown("---")
st.markdown("Created by Manul 🚀")
