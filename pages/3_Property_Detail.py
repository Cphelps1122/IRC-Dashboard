import streamlit as st
from auth import require_auth
from utils.load_data import load_data
import pandas as pd
from components.property_summary import render_property_summary

render_property_summary(df, selected_property)


require_auth()
st.set_page_config(page_title="Property Detail", layout="wide")

df, last_updated = load_data()

st.markdown("## Property Detail")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

if df.empty:
    st.warning("No data available.")
    st.stop()

# Calculated fields
df["Cost per Treatment"] = df["$ Amount"] / df["# Treatments"]
df["Usage per Treatment"] = df["Usage"] / df["# Treatments"]
df["Cost per Day"] = df["$ Amount"] / df["Number Days Billed"]

properties = sorted(df["Property Name"].unique())
selected_property = st.selectbox("Select Property", properties)

prop_df = df[df["Property Name"] == selected_property].copy()
prop_df = prop_df.sort_values(["Year", "Month"])

total_treatments = prop_df["# Treatments"].sum()
total_spend = prop_df["$ Amount"].sum()
total_usage = prop_df["Usage"].sum()
avg_cpt = prop_df["Cost per Treatment"].mean()
avg_upt = prop_df["Usage per Treatment"].mean()
avg_cpd = prop_df["Cost per Day"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Treatments", f"{total_treatments:,.0f}")
c2.metric("Total Spend ($)", f"${total_spend:,.2f}")
c3.metric("Total Usage (gal)", f"{total_usage:,.0f}")
c4.metric("Avg Cost/Treatment", f"${avg_cpt:,.2f}")
c5.metric("Avg Usage/Treatment", f"{avg_upt:,.0f} gal")

st.write("---")

prop_df["Period"] = prop_df["Month"].astype(str) + "-" + prop_df["Year"].astype(str)

st.markdown("### Cost per Treatment Over Time")
st.line_chart(prop_df.set_index("Period")["Cost per Treatment"])

st.markdown("### Usage per Treatment Over Time")
st.line_chart(prop_df.set_index("Period")["Usage per Treatment"])

st.markdown("### Cost per Day Billed Over Time")
st.line_chart(prop_df.set_index("Period")["Cost per Day"])

st.write("---")

st.markdown("### Billing Cycle Timeline (Days Billed)")
st.bar_chart(prop_df.set_index("Period")["Number Days Billed"])
