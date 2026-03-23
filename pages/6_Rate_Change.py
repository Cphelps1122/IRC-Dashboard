import streamlit as st
from auth import require_auth
from utils.load_data import load_data
import pandas as pd

require_auth()
st.set_page_config(page_title="Rate Change Detector", layout="wide")

df, last_updated = load_data()

st.markdown("## Rate Change Detector")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

if df.empty:
    st.warning("No data available.")
    st.stop()

df["Period"] = pd.to_datetime(df["Billing Date"], errors="coerce")
df["Cost per Gallon"] = df["$ Amount"] / df["Usage"]

properties = sorted(df["Property Name"].unique())
selected_property = st.selectbox("Select Property", properties)

prop_df = df[df["Property Name"] == selected_property].copy()
prop_df = prop_df.sort_values("Period")

st.markdown("### Cost per Gallon Over Time")
st.line_chart(prop_df.set_index("Period")["Cost per Gallon"])

prop_df["Rate Change"] = prop_df["Cost per Gallon"].diff()
prop_df["Rate Spike"] = prop_df["Rate Change"] > (prop_df["Rate Change"].mean() + 2 * prop_df["Rate Change"].std())

st.write("---")

st.markdown("### Rate Change Flags (1 = Spike)")
flags = prop_df.set_index("Period")[["Rate Spike"]].astype(int)
st.line_chart(flags)

st.write("---")

st.markdown("### Portfolio Cost per Gallon Trend")
portfolio = df.sort_values("Period").groupby("Period")["Cost per Gallon"].mean()
st.line_chart(portfolio)
