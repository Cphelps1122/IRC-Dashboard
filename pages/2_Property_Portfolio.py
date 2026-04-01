import streamlit as st
import pandas as pd
import numpy as np

from utils.load_data import load_data


# ---------------------------------------------------------
# 1️⃣ GLOBAL PREMIUM CSS (MUST BE FIRST)
# ---------------------------------------------------------
st.markdown("""
<style>

.property-card {
    background: #ffffff;
    border-radius: 14px;
    border: 1px solid #e5e5e5;
    padding: 0;
    height: 320px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 10px rgba(0,0,0,0.06);
    overflow: hidden;
    transition: all 0.15s ease;
}

.property-card:hover {
    box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    transform: translateY(-2px);
}

.property-card-header {
    background: #f5f7fa;
    padding: 14px 18px;
    border-bottom: 1px solid #e2e2e2;
    font-size: 17px;
    font-weight: 700;
    color: #1a1a1a;
}

.property-card-body {
    padding: 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.property-total {
    font-size: 30px;
    font-weight: 800;
    color: #000;
    margin-bottom: 6px;
}

.yoy-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 12px;
}

.utility-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    font-size: 14px;
    border-bottom: 1px solid #f0f0f0;
}

.utility-row:last-child {
    border-bottom: none;
}

</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# 2️⃣ Formatting Helpers
# ---------------------------------------------------------
def fmt_currency(x):
    if pd.isna(x):
        return "$0"
    return f"${x:,.0f}"


def compute_yoy(df, start_date, end_date):
    curr = df[(df["Billing Date"] >= start_date) & (df["Billing Date"] <= end_date)]["$ Amount"].sum()

    prev_start = start_date - pd.DateOffset(years=1)
    prev_end = end_date - pd.DateOffset(years=1)

    prev = df[(df["Billing Date"] >= prev_start) & (df["Billing Date"] <= prev_end)]["$ Amount"].sum()

    if prev == 0:
        return np.nan

    return ((curr - prev) / prev) * 100


# ---------------------------------------------------------
# 3️⃣ PREMIUM PROPERTY CARD
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
        <div class="utility-row">
            <span style="color:#444; font-weight:500;">{u}</span>
            <span style="font-weight:600;">{fmt_currency(v)}</span>
        </div>
        """
        for u, v in utilities.items()
    )

    # Final card HTML
    st.markdown(
        f"""
        <div class="property-card">

            <div class="property-card-header">
                {df_prop['Property Name'].iloc[0]}
            </div>

            <div class="property-card-body">

                <div>
                    <div class="property-total">{fmt_currency(total_cost)}</div>

                    <div class="yoy-badge" style="background:{yoy_bg}; color:{yoy_color};">
                        {yoy_arrow} {yoy_text} YoY
                    </div>
                </div>

                <div>
                    {util_html}
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# 4️⃣ MAIN PAGE
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
