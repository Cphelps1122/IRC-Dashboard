import streamlit as st
from auth import require_auth
from utils.load_data import load_data
import pandas as pd

require_auth()
st.set_page_config(page_title="Benchmarking", layout="wide")

df, last_updated = load_data()

st.markdown("## Property Benchmarking")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

if df.empty:
    st.warning("No data available.")
    st.stop()

df["Cost per Treatment"] = df["$ Amount"] / df["# Treatments"]
df["Usage per Treatment"] = df["Usage"] / df["# Treatments"]
df["Cost per Day"] = df["$ Amount"] / df["Number Days Billed"]

bench = df.groupby("Property Name").agg({
    "Cost per Treatment": "mean",
    "Usage per Treatment": "mean",
    "Cost per Day": "mean"
})

portfolio_cpt = bench["Cost per Treatment"].mean()
portfolio_upt = bench["Usage per Treatment"].mean()
portfolio_cpd = bench["Cost per Day"].mean()

c1, c2, c3 = st.columns(3)
c1.metric("Portfolio Avg Cost/Treatment", f"${portfolio_cpt:,.2f}")
c2.metric("Portfolio Avg Usage/Treatment", f"{portfolio_upt:,.0f} gal")
c3.metric("Portfolio Avg Cost/Day", f"${portfolio_cpd:,.2f}")

st.write("---")

st.markdown("### Cost per Treatment vs Portfolio Average")
st.bar_chart(bench["Cost per Treatment"].sort_values(ascending=False))

st.markdown("### Usage per Treatment vs Portfolio Average")
st.bar_chart(bench["Usage per Treatment"].sort_values(ascending=False))

st.markdown("### Cost per Day vs Portfolio Average")
st.bar_chart(bench["Cost per Day"].sort_values(ascending=False))
