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
# VERIFY REQUIRED COLUMNS EXIST
# ---------------------------------------------------------
required_cols = ["Street", "City", "State", "Zip Code", "Property Name"]
missing = [c for c in required_cols if c not in df.columns]

if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# ---------------------------------------------------------
# BUILD FULL ADDRESS FOR GEOCODING
# ---------------------------------------------------------
df["Full Address"] = (
    df["Street"].astype(str) + ", " +
    df["City"].astype(str) + ", " +
    df["State"].astype(str) + " " +
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
        except Exception:
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
    radius_scale=1,
    radius_min_pixels=3,           # shrinks when zoomed in
    radius_max_pixels=40,          # grows when zoomed out
    get_color=[0, 122, 255, 160],
    pickable=True,
)

highlight_layer = pdk.Layer(
    "ScatterplotLayer",
    data=highlight_df,
    get_position=["Longitude", "Latitude"],
    get_radius=4000,               # highlight radius
    radius_scale=1,
    radius_min_pixels=5,
    radius_max_pixels=60,
    get_color=[255, 0, 0, 200],
    pickable=True,
)

# ---------------------------------------------------------
# TOOLTIP
# ---------------------------------------------------------
tooltip = {
    "html": "<b>{Property Name}</b><br/>{Street}<br/>{City}, {State} {Zip Code}",
    "style": {"backgroundColor": "steelblue", "color": "white"},
}

# ---------------------------------------------------------
# RENDER MAP (CARTO BASEMAP — FREE)
# ---------------------------------------------------------
st.pydeck_chart(
    pdk.Deck(
        layers=[layer, highlight_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    )
)

st.caption("Blue = all properties, Red = highlighted property. Marker size adapts to zoom level.")
