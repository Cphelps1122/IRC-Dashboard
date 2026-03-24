import streamlit as st
from auth import require_auth
from utils.load_data import load_data
import pandas as pd
import pydeck as pdk
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

require_auth()
st.set_page_config(page_title="Property Map", layout="wide")

st.markdown("## Property Map")
st.write("Visualizing all properties using City + State geocoding.")

df, last_updated = load_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

# ---------------------------------------------------------
# BUILD FULL ADDRESS FOR GEOCODING
# ---------------------------------------------------------
df["Full Address"] = df["Property Name"] + ", " + df["City"] + ", " + df["State"]

# ---------------------------------------------------------
# GEOCODER (with caching)
# ---------------------------------------------------------
@st.cache_data(show_spinner=True)
def geocode_addresses(address_list):
    geolocator = Nominatim(user_agent="irc_dashboard")
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

unique_addresses = df["Full Address"].unique()
coords = geocode_addresses(unique_addresses)

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
# MAP LAYER
# ---------------------------------------------------------
layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_df,
    get_position=["Longitude", "Latitude"],
    get_radius=30000,
    get_color=[0, 122, 255, 160],
    pickable=True,
)

highlight_layer = pdk.Layer(
    "ScatterplotLayer",
    data=highlight_df,
    get_position=["Longitude", "Latitude"],
    get_radius=60000,
    get_color=[255, 0, 0, 200],
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=map_df["Latitude"].mean(),
    longitude=map_df["Longitude"].mean(),
    zoom=4,
    pitch=0,
)

tooltip = {
    "html": "<b>{Property Name}</b><br/>{City}, {State}",
    "style": {"backgroundColor": "steelblue", "color": "white"},
}

st.pydeck_chart(
    pdk.Deck(
        layers=[layer, highlight_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v9",
    )
)

st.caption("Blue = all properties, Red = highlighted property.")
