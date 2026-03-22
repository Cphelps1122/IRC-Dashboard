import streamlit as st

# Require uploaded file BEFORE anything else
if "uploaded_file" not in st.session_state or st.session_state["uploaded_file"] is None:
    st.title("📄 Upload Your Utility Ledger")
    st.write("Please upload your McNeill Excel file in the sidebar.")
    st.stop()

import altair as alt
from prophet import Prophet
from utils.load_data import load_property_ledger

df, month_order = load_property_ledger()

st.title("📈 Forecasting Center")

col1, col2, col3 = st.columns(3)
prop = col1.selectbox("Property", ["All"] + sorted(df["Property Name"].unique()))
util = col2.selectbox("Utility", ["All"] + sorted(df["Utility"].unique()))
target = col3.selectbox("Forecast Target", ["Spend ($ Amount)", "Usage", "Usage per HDD"])

f = df.copy()
if prop != "All":
    f = f[f["Property Name"] == prop]
if util != "All":
    f = f[f["Utility"] == util]

if target == "Spend ($ Amount)":
    ts = f.groupby("Billing Date", as_index=False)["$ Amount"].sum().rename(columns={"Billing Date": "ds", "$ Amount": "y"})
elif target == "Usage":
    ts = f.groupby("Billing Date", as_index=False)["Usage"].sum().rename(columns={"Billing Date": "ds", "Usage": "y"})
else:
    ts = f.groupby("Billing Date", as_index=False)["Usage_per_HDD"].mean().rename(columns={"Billing Date": "ds", "Usage_per_HDD": "y"})

if len(ts) < 5:
    st.warning("Not enough data to forecast.")
else:
    model = Prophet()
    model.fit(ts)
    future = model.make_future_dataframe(periods=180)
    forecast = model.predict(future)

    base = alt.Chart(forecast).encode(x="ds:T")
    line = base.mark_line(color="#1F618D").encode(y="yhat:Q")
    band = base.mark_area(opacity=0.2).encode(y="yhat_lower:Q", y2="yhat_upper:Q")

    st.altair_chart((band + line), use_container_width=True)