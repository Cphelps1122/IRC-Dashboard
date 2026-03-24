import streamlit as st
from auth import require_auth
from utils.load_data import load_data
import pandas as pd
import pydeck as pdk
import os
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

require_auth()
st.set_page_config(page_title="Property Map", layout="wide")

# ---------------------------------------------------------
# MAPBOX TOKEN (REQUIRED)
# ---------------------------------------------------------
os.environ["MAPBOX_API_KEY"] = st.secrets.get("MAPBOX_API_KEY", "")

st.markdown("## Property Map")
st.write("Visualizing all properties using City + State geocoding.")

df, last_updated = load_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

# Build full address
df["Full Address"] = df["Property Name"] + ", " + df["City"] + ", " + df["State"]

# ---------------------------------------------------------
# GEOCODING (cached)
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

coords = geocode_addresses(df["Full Address"].unique())

df["Latitude"] = df["Full Address"].apply(lambda x: coords[x][0])
df["Longitude"] = df["Full Address"].apply(lambda x: coords[x][1])

# Remove invalid coordinates
map_df = df.dropna(subset=["Latitude", "Longitude"]).copy()

if map_df.empty:
    st.error("No valid geocoded locations found.")
    st.stop()

# ---------------------------------------------------------
# SAFE VIEWPORT (prevents white screen)
# ---------------------------------------------------------
view_state = pdk.ViewState(
    latitude=map_df["Latitude"].mean() if not map_df.empty else 39.5,
    longitude=map_df["Longitude"].mean() if not map_df.empty else -98.35,
    zoom=4,
    pitch=0,
)

# ---------------------------------------------------------
# LAYERS
# ---------------------------------------------------------
layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_df,
    get_position=["Longitude", "Latitude"],
    get_radius=30000,
    get_color=[0, 122, 255, 160],
    pickable=True,
)

tooltip = {
    "html": "<b>{Property Name}</b><br/>{City}, {State}",
    "style": {"backgroundColor": "steelblue", "color": "white"},
}

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v9",
    )
)
