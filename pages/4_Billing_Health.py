import streamlit as st
from auth import require_auth
from utils.load_data import load_data
import pandas as pd

require_auth()
st.set_page_config(page_title="Billing Health", layout="wide")

df, last_updated = load_data()

st.markdown("## Billing Cycle Health")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

if df.empty:
    st.warning("No data available.")
    st.stop()

df["Period"] = pd.to_datetime(df["Billing Date"], errors="coerce")
df["Cost per Treatment"] = df["$ Amount"] / df["# Treatments"]
df["Cost per Day"] = df["$ Amount"] / df["Number Days Billed"]

properties = sorted(df["Property Name"].unique())
selected_property = st.selectbox("Select Property", properties)

prop_df = df[df["Property Name"] == selected_property].copy()
prop_df = prop_df.sort_values("Period")

short_threshold = 25
long_threshold = 35

prop_df["Short Cycle"] = prop_df["Number Days Billed"] < short_threshold
prop_df["Long Cycle"] = prop_df["Number Days Billed"] > long_threshold
prop_df["Zero Usage"] = prop_df["Usage"] <= 0
prop_df["Zero Treatments"] = prop_df["# Treatments"] <= 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Short Cycles", int(prop_df["Short Cycle"].sum()))
c2.metric("Long Cycles", int(prop_df["Long Cycle"].sum()))
c3.metric("Zero Usage Bills", int(prop_df["Zero Usage"].sum()))
c4.metric("Zero Treatment Bills", int(prop_df["Zero Treatments"].sum()))

st.write("---")

st.markdown("### Days Billed per Cycle")
st.bar_chart(prop_df.set_index("Period")["Number Days Billed"])

st.markdown("### Cost per Day Billed Over Time")
st.line_chart(prop_df.set_index("Period")["Cost per Day"])

st.write("---")

st.markdown("### Potential Anomalies (Visual Flags)")

flags = prop_df.set_index("Period")[["Short Cycle", "Long Cycle", "Zero Usage", "Zero Treatments"]]
flags = flags.astype(int)

st.line_chart(flags)
