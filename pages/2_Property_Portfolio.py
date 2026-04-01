import streamlit as st
import pandas as pd
import numpy as np

from utils.load_data import load_data


# ---------------------------------------------------------
# Helper: Format currency
# ---------------------------------------------------------
def fmt_currency(x):
    if pd.isna(x):
        return "$0"
    return f"${x:,.0f}"


# ---------------------------------------------------------
# Compute YoY % change
# ---------------------------------------------------------
def compute_yoy(df, start_date, end_date):
    curr = df[(df["Billing Date"] >= start_date) & (df["Billing Date"] <= end_date)]["$ Amount"].sum()

    prev_start = start_date - pd.DateOffset(years=1)
    prev_end = end_date - pd.DateOffset(years=1)

    prev = df[(df["Billing Date"] >= prev_start) & (df["Billing Date"] <= prev_end)]["$ Amount"].sum()

    if prev == 0:
        return np.nan

    return ((curr - prev) / prev) * 100


# ---------------------------------------------------------
# Property Card Component
# ---------------------------------------------------------
def property_card(df_prop, start_date, end_date):
    df_period = df_prop[
        (df_prop["Billing Date"] >= start_date) &
        (df_prop["Billing Date"] <= end_date)
    ]

    total_cost = df_period["$ Amount"].sum()
    yoy = compute_yoy(df_prop, start_date, end_date)

    utilities = df_period.groupby("Utility")["$ Amount"].sum().to_dict()

    # Color logic
    if pd.isna(yoy):
        color = "gray"
        arrow = ""
    elif yoy > 0:
        color = "red"
        arrow = "↑"
    elif yoy < 0:
        color = "green"
        arrow = "↓"
    else:
        color = "gray"
        arrow = ""

    st.markdown(
        f"""
        <div style="
            padding: 16px;
            border-radius: 10px;
            background-color: #f7f7f7;
            border: 1px solid #e0e0e0;
            height: 220px;
        ">
            <div style="font-size: 18px; font-weight: 700; margin-bottom: 8px;">
                {df_prop['Property Name'].iloc[0]}
            </div>

            <div style="font-size: 22px; font-weight: 700;">
                {fmt_currency(total_cost)}
            </div>

            <div style="font-size: 14px; color:{color}; font-weight:600; margin-bottom: 8px;">
                {arrow} {"" if pd.isna(yoy) else f"{yoy:+.0f}% YoY"}
            </div>

            <div style="font-size: 14px;">
                {"".join([f"<div>{u}: {fmt_currency(v)}</div>" for u, v in utilities.items()])}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# Main Page
# ---------------------------------------------------------
st.title("Property Portfolio Overview")

df, last_updated = load_data()
df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

# Build month/year selector
years = sorted(df["Billing Date"].dt.year.unique())
months = {
    1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
    7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"
}

col1, col2 = st.columns(2)

with col1:
    start_year = st.selectbox("Start Year", years)
    start_month = st.selectbox("Start Month", sorted(df[df["Billing Date"].dt.year == start_year]["Billing Date"].dt.month.unique()), format_func=lambda x: months[x])

with col2:
    end_year = st.selectbox("End Year", years, index=len(years)-1)
    end_month = st.selectbox("End Month", sorted(df[df["Billing Date"].dt.year == end_year]["Billing Date"].dt.month.unique()), format_func=lambda x: months[x])

start_date = pd.Timestamp(start_year, start_month, 1)
end_date = pd.Timestamp(end_year, end_month, 28) + pd.offsets.MonthEnd(0)

properties = sorted(df["Property Name"].unique())

# Render grid
cols = st.columns(3)

for i, prop in enumerate(properties):
    df_prop = df[df["Property Name"] == prop]
    with cols[i % 3]:
        property_card(df_prop, start_date, end_date)
