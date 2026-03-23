import streamlit as st
from utils.load_data import load_data

st.set_page_config(page_title="Dashboard", layout="wide")

df, last_updated = load_data()

st.markdown("## Utility Dashboard")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

if df.empty:
    st.warning("No data available.")
    st.stop()

# ---- Filters ----
col1, col2, col3 = st.columns(3)

property_filter = col1.multiselect(
    "Property",
    sorted(df["Property Name"].unique()),
    default=None
)

utility_filter = col2.multiselect(
    "Utility",
    sorted(df["Utility"].unique()),
    default=None
)

year_filter = col3.multiselect(
    "Year",
    sorted(df["Year"].unique()),
    default=None
)

# Apply filters
filtered = df.copy()

if property_filter:
    filtered = filtered[filtered["Property Name"].isin(property_filter)]

if utility_filter:
    filtered = filtered[filtered["Utility"].isin(utility_filter)]

if year_filter:
    filtered = filtered[filtered["Year"].isin(year_filter)]

st.write("---")

# ---- Spend by Property ----
spend_by_property = filtered.groupby("Property Name")["$ Amount"].sum().sort_values(ascending=False)

st.markdown("### Spend by Property")
st.bar_chart(spend_by_property)

# ---- Usage by Property ----
usage_by_property = filtered.groupby("Property Name")["Usage"].sum().sort_values(ascending=False)

st.markdown("### Usage by Property")
st.bar_chart(usage_by_property)

st.write("---")

# ---- Raw Data Table ----
st.markdown("### Raw Data")
st.dataframe(filtered, use_container_width=True)
