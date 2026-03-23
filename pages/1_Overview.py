import streamlit as st
from utils.load_data import load_data

st.set_page_config(page_title="Overview", layout="wide")

df, last_updated = load_data()

st.markdown("## Portfolio Overview")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

if df.empty:
    st.warning("No data available.")
    st.stop()

# ---- KPI Metrics ----
total_properties = df["Property Name"].nunique()
total_spend = df["$ Amount"].sum()
total_usage = df["Usage"].sum()
avg_days_billed = df["Number Days Billed"].mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Properties", total_properties)
col2.metric("Total Spend ($)", f"${total_spend:,.2f}")
col3.metric("Total Usage", f"{total_usage:,.0f}")
col4.metric("Avg Days Billed", f"{avg_days_billed:.1f}")

st.write("---")

# ---- Monthly Spend Trend ----
monthly = df.groupby(["Year", "Month"])["$ Amount"].sum().reset_index()
monthly["Period"] = monthly["Month"].astype(str) + "-" + monthly["Year"].astype(str)

st.markdown("### Monthly Spend Trend")
st.line_chart(monthly.set_index("Period")["$ Amount"])
