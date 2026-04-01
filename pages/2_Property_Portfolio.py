import streamlit as st
import pandas as pd
import numpy as np

from utils.load_data import load_data


# ---------------------------------------------------------
# Formatting Helpers
# ---------------------------------------------------------
def fmt_currency(x):
    if pd.isna(x):
        return "$0"
    return f"${x:,.0f}"


def fmt_pct(x):
    if pd.isna(x):
        return "—"
    return f"{x:+.0f}%"


# ---------------------------------------------------------
# YoY Calculation
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
# Property Card (Hybrid Style)
# ---------------------------------------------------------
def property_card(df_prop, start_date, end_date):
    df_period = df_prop[
        (df_prop["Billing Date"] >= start_date) &
        (df_prop["Billing Date"] <= end_date)
    ]

    total_cost = df_period["$ Amount"].sum()
    yoy = compute_yoy(df_prop, start_date, end_date)

    utilities = (
        df_period.groupby("Utility")["$ Amount"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )

    # YoY badge styling
    if pd.isna(yoy):
        yoy_color = "#6c757d"
        yoy_bg = "#e9ecef"
        yoy_arrow = ""
        yoy_text = "No YoY Data"
    elif yoy > 0:
        yoy_color = "#d9534f"
        yoy_bg = "#f8d7da"
        yoy_arrow = "▲"
        yoy_text = f"+{yoy:.0f}%"
    elif yoy < 0:
        yoy_color = "#5cb85c"
        yoy_bg = "#d4edda"
        yoy_arrow = "▼"
        yoy_text = f"{yoy:.0f}%"
    else:
        yoy_color = "#6c757d"
        yoy_bg = "#e9ecef"
        yoy_arrow = ""
        yoy_text = "0%"

    # Utility rows
    util_html = "".join(
        f"""
        <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
            <span style="color:#444; font-weight:500;">{u}</span>
            <span style="font-weight:600;">{fmt_currency(v)}</span>
        </div>
        """
        for u, v in utilities.items()
    )

    # Card HTML
    st.markdown(
        f"""
        <div style="
            background: #ffffff;
            border-radius: 14px;
            border: 1px solid #e2e2e2;
            padding: 20px;
            height: 280px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        ">

            <!-- Property Name -->
            <div style="font-size: 18px; font-weight: 700; color:#222; margin-bottom: 4px;">
                {df_prop['Property Name'].iloc[0]}
            </div>

            <!-- Total Cost -->
            <div style="font-size: 30px; font-weight: 800; color:#000; margin-bottom: 6px;">
                {fmt_currency(total_cost)}
            </div>

            <!-- YoY Badge -->
            <div style="
                display:inline-block;
                padding: 4px 12px;
                border-radius: 8px;
                background: {yoy_bg};
                color: {yoy_color};
                font-size: 13px;
                font-weight: 700;
                width: fit-content;
                margin-bottom: 10px;
            ">
                {yoy_arrow} {yoy_text} YoY
            </div>

            <!-- Utility Breakdown -->
            <div style="font-size: 14px; line-height: 1.4; margin-top: 6px;">
                {util_html}
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

# Date selectors
years = sorted(df["Billing Date"].dt.year.unique())
months = {
    1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
    7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"
}

col1, col2 = st.columns(2)

with col1:
    start_year = st.selectbox("Start Year", years)
    start_month = st.selectbox(
        "Start Month",
        sorted(df[df["Billing Date"].dt.year == start_year]["Billing Date"].dt.month.unique()),
        format_func=lambda x: months[x]
    )

with col2:
    end_year = st.selectbox("End Year", years, index=len(years)-1)
    end_month = st.selectbox(
        "End Month",
        sorted(df[df["Billing Date"].dt.year == end_year]["Billing Date"].dt.month.unique()),
        format_func=lambda x: months[x]
    )

start_date = pd.Timestamp(start_year, start_month, 1)
end_date = pd.Timestamp(end_year, end_month, 28) + pd.offsets.MonthEnd(0)

properties = sorted(df["Property Name"].unique())

# Render grid
cols = st.columns(3)

for i, prop in enumerate(properties):
    df_prop = df[df["Property Name"] == prop]
    with cols[i % 3]:
        property_card(df_prop, start_date, end_date)
