import streamlit as st
import pandas as pd
import altair as alt
from prophet import Prophet

from utils.load_data import load_property_ledger
from components.header import render_header   # ← NEW IMPORT

# -----------------------------
# HEADER (centered full-width logo)
# -----------------------------
render_header()                               # ← NEW HEADER

# -----------------------------
# LOAD DATA
# -----------------------------
df, month_order = load_property_ledger()

if df is None or df.empty:
    st.error("No Excel file found in /data. Please add one.")
    st.stop()

if "Billing Date" in df.columns:
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

st.title("Forecasting Center")

# -----------------------------
# FILTERS
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

properties = ["All"] + sorted(df["Property Name"].unique())
utilities = ["All"] + sorted(df["Utility"].unique())
years = sorted(df["Year"].dropna().unique()) if "Year" in df.columns else []

prop = col1.selectbox("Property", properties)
util = col2.selectbox("Utility", utilities)
selected_years = col3.multiselect("Years", years, default=years)
target = col4.selectbox("Forecast Target", ["Spend ($ Amount)", "Usage"])

f = df.copy()
if prop != "All":
    f = f[f["Property Name"] == prop]
if util != "All":
    f = f[f["Utility"] == util]
if selected_years:
    f = f[f["Year"].isin(selected_years)]

if f.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# -----------------------------
# BUILD TIME SERIES
# -----------------------------
if target == "Spend ($ Amount)":
    ts = (
        f.groupby("Billing Date", as_index=False)["$ Amount"]
        .sum()
        .rename(columns={"Billing Date": "ds", "$ Amount": "y"})
    )
else:
    ts = (
        f.groupby("Billing Date", as_index=False)["Usage"]
        .sum()
        .rename(columns={"Billing Date": "ds", "Usage": "y"})
    )

ts = ts.dropna()

if ts.empty:
    st.warning("Not enough data to build a forecast.")
    st.stop()

# -----------------------------
# RUN PROPHET
# -----------------------------
m = Prophet()
m.fit(ts)

future = m.make_future_dataframe(periods=12, freq="MS")
forecast = m.predict(future)

# -----------------------------
# HISTORICAL + FORECAST CHART
# -----------------------------
st.subheader("Historical + Forecast")

hist = ts.copy()
hist["type"] = "Actual"
fc = forecast[["ds", "yhat"]].copy()
fc["type"] = "Forecast"
fc = fc[fc["ds"] > hist["ds"].max()]

combined = pd.concat(
    [
        hist.rename(columns={"y": "value"}),
        fc.rename(columns={"yhat": "value"}),
    ],
    ignore_index=True,
)

chart = (
    alt.Chart(combined)
    .mark_line(point=True)
    .encode(
        x=alt.X("ds:T", title="Date"),
        y=alt.Y("value:Q", title=target),
        color=alt.Color("type:N", title="Series"),
        tooltip=["ds", "value", "type"],
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)

