import streamlit as st
from utils.load_data import load_data
import pandas as pd
from auth import require_auth
require_auth()

st.set_page_config(page_title="Dashboard", layout="wide")

df, last_updated = load_data()

st.markdown("## Property Performance Dashboard")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

if df.empty:
    st.warning("No data available.")
    st.stop()

# ---------------------------------------------------------
# CALCULATED METRICS
# ---------------------------------------------------------
df["Cost per Treatment"] = df["$ Amount"] / df["# Treatments"]
df["Usage per Treatment"] = df["Usage"] / df["# Treatments"]
df["Cost per Day"] = df["$ Amount"] / df["Number Days Billed"]

# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------
col1, col2 = st.columns(2)

property_filter = col1.multiselect(
    "Property",
    sorted(df["Property Name"].unique()),
)

year_filter = col2.multiselect(
    "Year",
    sorted(df["Year"].unique()),
)

filtered = df.copy()

if property_filter:
    filtered = filtered[filtered["Property Name"].isin(property_filter)]

if year_filter:
    filtered = filtered[filtered["Year"].isin(year_filter)]

st.write("---")

# ---------------------------------------------------------
# COST PER TREATMENT (BAR)
# ---------------------------------------------------------
cpt = (
    filtered.groupby("Property Name")["Cost per Treatment"]
    .mean()
    .sort_values(ascending=False)
)

st.markdown("### Cost per Treatment by Property")
st.bar_chart(cpt)

# ---------------------------------------------------------
# USAGE PER TREATMENT (BAR)
# ---------------------------------------------------------
upt = (
    filtered.groupby("Property Name")["Usage per Treatment"]
    .mean()
    .sort_values(ascending=False)
)

st.markdown("### Usage per Treatment by Property")
st.bar_chart(upt)

# ---------------------------------------------------------
# COST PER DAY BILLED (BAR)
# ---------------------------------------------------------
cpd = (
    filtered.groupby("Property Name")["Cost per Day"]
    .mean()
    .sort_values(ascending=False)
)

st.markdown("### Cost per Day Billed by Property")
st.bar_chart(cpd)

st.write("---")

# ---------------------------------------------------------
# USAGE VS COST SCATTER (EFFICIENCY)
# ---------------------------------------------------------
scatter_df = filtered.groupby("Property Name").agg({
    "Usage": "sum",
    "$ Amount": "sum"
})

st.markdown("### Usage vs Cost (Efficiency View)")
st.scatter_chart(scatter_df)
