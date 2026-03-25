import streamlit as st
from auth import require_auth
from utils.load_data import load_data
import pandas as pd
import pydeck as pdk
from geopy.geocoders import ArcGIS
from geopy.extra.rate_limiter import RateLimiter

require_auth()
st.set_page_config(page_title="Property Map", layout="wide")

st.markdown("## Property Map")
st.write("Mapping all properties using full address geocoding with adaptive marker sizes.")

df, last_updated = load_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

# ---------------------------------------------------------
# BUILD FULL ADDRESS FOR GEOCODING
# ---------------------------------------------------------
df["Full Address"] = (
    df["Street"] + ", " +
    df["City"] + ", " +
    df["State"] + " " +
    df["Zip Code"].astype(str)
)

# ---------------------------------------------------------
# ARC GIS GEOCODER (cached)
# ---------------------------------------------------------
@st.cache_data(show_spinner=True)
def geocode_arcgis(address_list):
    geolocator = ArcGIS(timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    results = {}
    for addr in address_list:
        try:
            location = geocode(addr)
            if location:
                results[addr] = (location.latitude, location.longitude)
            else:
                results[addr] = (None, None)
        except:
            results[addr] = (None, None)
    return results

coords = geocode_arcgis(df["Full Address"].unique())

df["Latitude"] = df["Full Address"].apply(lambda x: coords[x][0])
df["Longitude"] = df["Full Address"].apply(lambda x: coords[x][1])

# Drop properties that failed geocoding
map_df = df.dropna(subset=["Latitude", "Longitude"]).copy()

if map_df.empty:
    st.error("No valid geocoded locations found.")
    st.stop()

# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------
properties = sorted(map_df["Property Name"].unique())
selected_property = st.selectbox("Highlight Property", ["All Properties"] + properties)

if selected_property != "All Properties":
    highlight_df = map_df[map_df["Property Name"] == selected_property]
else:
    highlight_df = map_df

# ---------------------------------------------------------
# VIEWPORT
# ---------------------------------------------------------
view_state = pdk.ViewState(
    latitude=map_df["Latitude"].mean(),
    longitude=map_df["Longitude"].mean(),
    zoom=4,
    pitch=0,
)

# ---------------------------------------------------------
# MAP LAYERS (Zoom‑adaptive using radius_min/max_pixels)
# ---------------------------------------------------------
layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_df,
    get_position=["Longitude", "Latitude"],
    get_radius=2000,               # base radius
