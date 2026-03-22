import pandas as pd
import numpy as np
import pydeck as pdk
import streamlit as st

# -----------------------------
# BUILD PROPERTY COORDINATES
# -----------------------------
def build_property_coordinates(df):
    required = ["Property Name", "City", "State"]
    for col in required:
        if col not in df.columns:
            return pd.DataFrame()

    props = df[["Property Name", "City", "State"]].drop_duplicates()

    # Fake geocoding (stable placeholder)
    def fake_latlon(name):
        seed = abs(hash(name)) % 10000
        lat = 30 + (seed % 1000) / 1000
        lon = -97 - (seed % 1000) / 1000
        return lat, lon

    props["Latitude"], props["Longitude"] = zip(*props["Property Name"].apply(fake_latlon))

    # Occupancy ratio
    if "Occupied Rooms" in df.columns and "# Units" in df.columns:
        occ = df.groupby("Property Name").agg({
            "Occupied Rooms": "mean",
            "# Units": "first"
        }).reset_index()
        occ["Occ_Ratio"] = occ["Occupied Rooms"] / occ["# Units"]
        props = props.merge(occ[["Property Name", "Occ_Ratio"]], on="Property Name", how="left")
    else:
        props["Occ_Ratio"] = 0.5

    # Color + radius
    def occupancy_color(r):
        if pd.isna(r):
            return [200, 200, 200]
        if r < 0.4:
            return [200, 60, 60]
        if r < 0.7:
            return [230, 180, 60]
        return [60, 160, 90]

    props["Color"] = props["Occ_Ratio"].apply(occupancy_color)
    props["Radius"] = (props["Occ_Ratio"].fillna(0.5) * 3000) + 800

    return props


# -----------------------------
# PROPERTY SUMMARY
# -----------------------------
def build_property_summary(df):
    required = ["Property Name", "Usage", "$ Amount", "Occupied Rooms"]
    for col in required:
        if col not in df.columns:
            return pd.DataFrame()

    df["CPOR"] = df["$ Amount"] / df["Occupied Rooms"].replace(0, pd.NA)

    summary = df.groupby("Property Name").agg({
        "Usage": "sum",
        "$ Amount": "sum",
        "CPOR": "mean"
    }).reset_index()

    return summary


# -----------------------------
# RENDER MAP
# -----------------------------
def render_property_map(props):
    if props.empty:
        st.warning("No property coordinates available to display on the map.")
        return

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=props,
        get_position=["Longitude", "Latitude"],
        get_radius="Radius",
        get_fill_color="Color",
        pickable=True,
        auto_highlight=True
    )

    view_state = pdk.ViewState(
        latitude=props["Latitude"].mean(),
        longitude=props["Longitude"].mean(),
        zoom=8
    )

    tooltip = {
        "html": "<b>{Property Name}</b><br/>"
                "Occupancy: {Occ_Ratio}<br/>"
                "Lat: {Latitude}<br/>Lon: {Longitude}",
        "style": {"color": "white"}
    }

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip
    ))
