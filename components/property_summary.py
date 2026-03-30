import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# Helper: Format currency
# ---------------------------------------------------------
def fmt_currency(x):
    if pd.isna(x):
        return "$0"
    return f"${x:,.0f}"

# ---------------------------------------------------------
# Helper: Format percent change
# ---------------------------------------------------------
def fmt_pct(x):
    if pd.isna(x):
        return "—"
    return f"{x:+.0f}%"

# ---------------------------------------------------------
# Helper: Metric card component
# ---------------------------------------------------------
def metric_card(label, cost, yoy):
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
            padding: 12px;
            border-radius: 8px;
            background-color: #f7f7f7;
            border: 1px solid #e0e0e0;
            text-align: center;
        ">
            <div style="font-size: 16px; font-weight: 600; margin-bottom: 6px;">
                {label}
            </div>
            <div style="font-size: 22px; font-weight: 700;">
                {fmt_currency(cost)}
            </div>
            <div style="font-size: 16px; color:{color}; font-weight:600;">
                {arrow} {fmt_pct(yoy)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# Compute YoY % change
# ---------------------------------------------------------
def compute_yoy(df, utility, start_date, end_date):
    # Current period
    df_curr = df[
        (df["Utility"] == utility) &
        (df["Billing Date"] >= start_date) &
        (df["Billing Date"] <= end_date)
    ]

    curr_total = df_curr["$ Amount"].sum()

    # Previous year period
    prev_start = start_date - pd.DateOffset(years=1)
    prev_end = end_date - pd.DateOffset(years=1)

    df_prev = df[
        (df["Utility"] == utility) &
        (df["Billing Date"] >= prev_start) &
        (df["Billing Date"] <= prev_end)
    ]

    prev_total = df_prev["$ Amount"].sum()

    if prev_total == 0:
        return np.nan

    return ((curr_total - prev_total) / prev_total) * 100

# ---------------------------------------------------------
# Main Component
# ---------------------------------------------------------
def render_property_summary(df, property_name):

    st.subheader(f"Property Summary — {property_name}")

    # Filter to selected property
    df_prop = df[df["Property Name"] == property_name].copy()

    # Ensure Billing Date is datetime
    df_prop["Billing Date"] = pd.to_datetime(df_prop["Billing Date"])

    # Build month/year dropdowns from actual data
    df_prop["Year"] = df_prop["Billing Date"].dt.year
    df_prop["Month"] = df_prop["Billing Date"].dt.month

    years = sorted(df_prop["Year"].unique())
    months = {
        1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
        7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"
    }

    col1, col2 = st.columns(2)

    with col1:
        start_year = st.selectbox("Start Year", years)
        start_month = st.selectbox("Start Month", sorted(df_prop[df_prop["Year"] == start_year]["Month"].unique()), format_func=lambda x: months[x])

    with col2:
        end_year = st.selectbox("End Year", years, index=len(years)-1)
        end_month = st.selectbox("End Month", sorted(df_prop[df_prop["Year"] == end_year]["Month"].unique()), format_func=lambda x: months[x])

    # Build date range
    start_date = pd.Timestamp(start_year, start_month, 1)
    end_date = pd.Timestamp(end_year, end_month, 28) + pd.offsets.MonthEnd(0)

    # Filter to selected period
    df_period = df_prop[
        (df_prop["Billing Date"] >= start_date) &
        (df_prop["Billing Date"] <= end_date)
    ]

    # Total cost
    total_cost = df_period["$ Amount"].sum()

    # YoY for total
    prev_start = start_date - pd.DateOffset(years=1)
    prev_end = end_date - pd.DateOffset(years=1)

    df_prev = df_prop[
        (df_prop["Billing Date"] >= prev_start) &
        (df_prop["Billing Date"] <= prev_end)
    ]

    prev_total = df_prev["$ Amount"].sum()
    total_yoy = np.nan if prev_total == 0 else ((total_cost - prev_total) / prev_total) * 100

    # Render total card
    st.markdown("### Total Cost")
    metric_card("Total Cost", total_cost, total_yoy)

    # Auto-detect utilities
    utilities = sorted(df_period["Utility"].unique())

    st.markdown("### Utility Breakdown")

    cols = st.columns(3)

    for i, util in enumerate(utilities):
        util_cost = df_period[df_period["Utility"] == util]["$ Amount"].sum()
        util_yoy = compute_yoy(df_prop, util, start_date, end_date)

        with cols[i % 3]:
            metric_card(util, util_cost, util_yoy)
