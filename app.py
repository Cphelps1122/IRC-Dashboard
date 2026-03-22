import streamlit as st
import altair as alt
import pandas as pd

from utils.load_data import load_property_ledger
from utils.metrics import portfolio_metrics
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
    last_dt = df["Billing Date"].max()
    last_updated = last_dt.strftime("%b %d, %Y") if pd.notna(last_dt) else "N/A"
else:
    last_updated = "N/A"

# -----------------------------
# HEADER
# -----------------------------
st.title("Portfolio Energy & Utility Dashboard")
st.markdown(f"**Last Updated:** {last_updated}")

# -----------------------------
# FILTERS
# -----------------------------
col_f1, col_f2, col_f3 = st.columns(3)

properties = ["All"] + sorted(df["Property Name"].unique())
utilities = ["All"] + sorted(df["Utility"].unique())
years = sorted(df["Year"].dropna().unique()) if "Year" in df.columns else []

selected_property = col_f1.selectbox("Property", properties)
selected_utility = col_f2.selectbox("Utility", utilities)
selected_years = col_f3.multiselect("Years", years, default=years)

f = df.copy()
if selected_property != "All":
    f = f[f["Property Name"] == selected_property]
if selected_utility != "All":
    f = f[f["Utility"] == selected_utility]
if selected_years:
    f = f[f["Year"].isin(selected_years)]

if f.empty:
    st.warning("No data for selected filters.")
    st.stop()

# -----------------------------
# EXECUTIVE KPIs
# -----------------------------
metrics = portfolio_metrics(f)

# YOY calculations (guarded)
if "Year" in f.columns:
    current_year = max(selected_years) if selected_years else f["Year"].max()
    prev_year = current_year - 1

    cy_spend = f[f["Year"] == current_year]["$ Amount"].sum() if "$ Amount" in f.columns else None
    py_spend = f[f["Year"] == prev_year]["$ Amount"].sum() if "$ Amount" in f.columns else None
    yoy_spend = (
        (cy_spend - py_spend) / py_spend * 100
        if py_spend not in (0, None) and cy_spend is not None
        else None
    )

    cy_usage = f[f["Year"] == current_year]["Usage"].sum() if "Usage" in f.columns else None
    py_usage = f[f["Year"] == prev_year]["Usage"].sum() if "Usage" in f.columns else None
    yoy_usage = (
        (cy_usage - py_usage) / py_usage * 100
        if py_usage not in (0, None) and cy_usage is not None
        else None
    )

    # Efficiency (CPOR / CPAR) if available
    cy_cpor = f[f["Year"] == current_year]["CPOR"].mean() if "CPOR" in f.columns else None
    py_cpor = f[f["Year"] == prev_year]["CPOR"].mean() if "CPOR" in f.columns else None
    yoy_cpor = (
        (cy_cpor - py_cpor) / py_cpor * 100
        if py_cpor not in (0, None) and cy_cpor is not None
        else None
    )

    cy_cpar = f[f["Year"] == current_year]["CPAR"].mean() if "CPAR" in f.columns else None
    py_cpar = f[f["Year"] == prev_year]["CPAR"].mean() if "CPAR" in f.columns else None
    yoy_cpar = (
        (cy_cpar - py_cpar) / py_cpar * 100
        if py_cpar not in (0, None) and cy_cpar is not None
        else None
    )
else:
    yoy_spend = yoy_usage = yoy_cpor = yoy_cpar = None

colA, colB, colC, colD = st.columns(4)
colA.metric("Years", metrics["years"])
colB.metric(
    "Total Spend",
    f"${metrics['total_spend']:,.0f}" if metrics["total_spend"] is not None else "N/A",
)
colC.metric(
    "Total Usage",
    f"{metrics['total_usage']:,.0f}" if metrics["total_usage"] is not None else "N/A",
)
colD.metric(
    "YOY Spend Change",
    f"{yoy_spend:.1f}%" if yoy_spend is not None else "N/A",
)

colE, colF = st.columns(2)
colE.metric(
    "YOY CPOR Change",
    f"{yoy_cpor:.1f}%" if yoy_cpor is not None else "N/A",
)
colF.metric(
    "YOY CPAR Change",
    f"{yoy_cpar:.1f}%" if yoy_cpar is not None else "N/A",
)

# -----------------------------
# PROPERTY RANKING (EFFICIENCY)
# -----------------------------
st.subheader("Property Efficiency Ranking (CPOR)")

if "CPOR" in f.columns:
    rank_df = (
        f.groupby("Property Name", as_index=False)["CPOR"]
        .mean()
        .dropna(subset=["CPOR"])
    )
    if "Year" in f.columns:
        # Optional: restrict to current_year for ranking
        rank_df = (
            f[f["Year"] == current_year]
            .groupby("Property Name", as_index=False)["CPOR"]
            .mean()
            .dropna(subset=["CPOR"])
        )

    rank_df = rank_df.sort_values("CPOR", ascending=True)

    chart_rank = (
        alt.Chart(rank_df)
        .mark_bar()
        .encode(
            x=alt.X("CPOR:Q", title="Cost per Occupied Room"),
            y=alt.Y("Property Name:N", sort="-x", title="Property"),
            tooltip=["Property Name", "CPOR"],
            color=alt.Color("CPOR:Q", legend=None),
        )
        .properties(height=400)
    )
    st.altair_chart(chart_rank, use_container_width=True)
else:
    st.info("CPOR metric not available in this dataset.")

# -----------------------------
# HERO EFFICIENCY TREND (CPOR YOY)
# -----------------------------
st.subheader("Year-over-Year Efficiency Trend (CPOR)")

if {"CPOR", "Month_Num", "Year"}.issubset(f.columns):
    cpor_df = (
        f.groupby(["Year", "Month_Num"], as_index=False)["CPOR"]
        .mean()
        .dropna(subset=["CPOR"])
    )

    chart_cpor = (
        alt.Chart(cpor_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Month_Num:O", title="Month"),
            y=alt.Y("CPOR:Q", title="Cost per Occupied Room"),
            color=alt.Color("Year:N", title="Year"),
            tooltip=["Year", "Month_Num", "CPOR"],
        )
        .properties(height=300)
    )
    st.altair_chart(chart_cpor, use_container_width=True)
else:
    st.info("Not enough data to build CPOR trend.")

# -----------------------------
# UTILITY SMALL MULTIPLES
# -----------------------------
st.subheader("Utility Spend & Usage by Year")

if {"Utility", "Year", "$ Amount", "Usage"}.issubset(f.columns):
    util_agg = (
        f.groupby(["Utility", "Year"], as_index=False)[["$ Amount", "Usage"]]
        .sum()
    )

    col_u1, col_u2 = st.columns(2)

    with col_u1:
        st.markdown("**Spend by Utility (by Year)**")
        chart_spend = (
            alt.Chart(util_agg)
            .mark_bar()
            .encode(
                x=alt.X("Utility:N", title="Utility"),
                y=alt.Y("$ Amount:Q", title="Spend ($)"),
                color=alt.Color("Year:N", title="Year"),
                tooltip=["Utility", "Year", "$ Amount"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_spend, use_container_width=True)

    with col_u2:
        st.markdown("**Usage by Utility (by Year)**")
        chart_usage = (
            alt.Chart(util_agg)
            .mark_bar()
            .encode(
                x=alt.X("Utility:N", title="Utility"),
                y=alt.Y("Usage:Q", title="Usage"),
                color=alt.Color("Year:N", title="Year"),
                tooltip=["Utility", "Year", "Usage"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_usage, use_container_width=True)
else:
    st.info("Utility-level breakdown not fully available for this dataset.")

