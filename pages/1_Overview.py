import streamlit as st
from utils.load_data import load_data
import pandas as pd
from auth import require_auth
require_auth()

st.set_page_config(page_title="Overview", layout="wide")

df, last_updated = load_data()

st.markdown("## Portfolio Overview")
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

total_treatments = df["# Treatments"].sum()
total_spend = df["$ Amount"].sum()
total_usage = df["Usage"].sum()

avg_cost_per_treatment = df["Cost per Treatment"].mean()
avg_usage_per_treatment = df["Usage per Treatment"].mean()
avg_cost_per_day = df["Cost per Day"].mean()

# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Treatments", f"{total_treatments:,.0f}")
col2.metric("Total Spend ($)", f"${total_spend:,.2f}")
col3.metric("Total Usage (gal)", f"{total_usage:,.0f}")
col4.metric("Avg Cost per Treatment", f"${avg_cost_per_treatment:,.2f}")
col5.metric("Avg Usage per Treatment", f"{avg_usage_per_treatment:,.0f} gal")

st.write("---")

# ---------------------------------------------------------
# MONTHLY TRENDS
# ---------------------------------------------------------
monthly = df.groupby(["Year", "Month"]).agg({
    "$ Amount": "sum",
    "Usage": "sum",
    "# Treatments": "sum"
}).reset_index()

monthly["Period"] = monthly["Month"].astype(str) + "-" + monthly["Year"].astype(str)

st.markdown("### Monthly Spend Trend")
st.line_chart(monthly.set_index("Period")["$ Amount"])

st.markdown("### Monthly Usage Trend")
st.line_chart(monthly.set_index("Period")["Usage"])

st.write("---")

# ---------------------------------------------------------
# TOP 5 MOST EXPENSIVE PROPERTIES (Cost per Treatment)
# ---------------------------------------------------------
top5 = (
    df.groupby("Property Name")["Cost per Treatment"]
    .mean()
    .sort_values(ascending=False)
    .head(5)
)

st.markdown("### Highest Cost per Treatment (Top 5 Properties)")
st.bar_chart(top5)
