import streamlit as st
import pandas as pd
import altair as alt

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

# Ensure Year / Month_Num exist
if "Year" not in df.columns and "Billing Date" in df.columns:
    df["Year"] = df["Billing Date"].dt.year
if "Month_Num" not in df.columns and "Billing Date" in df.columns:
    df["Month_Num"] = df["Billing Date"].dt.month

st.title("Portfolio Benchmarking Platform")

# -----------------------------
# INFO / LEGEND
# -----------------------------
with st.expander("ℹ️ Benchmarking Definitions"):
    st.markdown("""
### **Key Benchmarking Metrics**

**CPOR (Cost per Occupied Room)** – Lower is better  
**CPAR (Cost per Available Room)** – Normalizes for property size  
**Cost per Unit** – Spend ÷ Usage  
**Usage per Occupied Room** – Efficiency of consumption  
**YOY Change** – Year-over-year percent change  
**Outlier** – A statistically unusual value (high Z-score)
""")

# -----------------------------
# FILTERS
# -----------------------------
col_f1, col_f2, col_f3 = st.columns(3)

years = sorted(df["Year"].dropna().unique())
selected_year = col_f1.selectbox("Benchmark Year", years)

utilities = ["All"] + sorted(df["Utility"].unique())
selected_utility = col_f2.selectbox("Utility Filter", utilities)

metric_category = col_f3.selectbox(
    "Metric Category",
    [
        "Cost Efficiency",
        "Usage Efficiency",
        "Rate Efficiency",
        "Occupancy-Normalized",
    ],
)

f = df[df["Year"] == selected_year].copy()
if selected_utility != "All":
    f = f[f["Utility"] == selected_utility]

if f.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# -----------------------------
# EXECUTIVE KPIs (FIRST)
# -----------------------------
st.subheader("Executive Benchmarking KPIs")

total_spend = f["$ Amount"].sum() if "$ Amount" in f.columns else None
total_usage = f["Usage"].sum() if "Usage" in f.columns else None
avg_cpor = f["CPOR"].mean() if "CPOR" in f.columns else None
avg_cpar = f["CPAR"].mean() if "CPAR" in f.columns else None

# YOY comparison
prev_year = selected_year - 1
prev = df[df["Year"] == prev_year]

def safe_yoy(curr, prev):
    if prev in (0, None) or curr is None:
        return None
    return (curr - prev) / prev * 100

yoy_spend = safe_yoy(total_spend, prev["$ Amount"].sum() if "$ Amount" in prev.columns else None)
yoy_usage = safe_yoy(total_usage, prev["Usage"].sum() if "Usage" in prev.columns else None)
yoy_cpor = safe_yoy(avg_cpor, prev["CPOR"].mean() if "CPOR" in prev.columns else None)
yoy_cpar = safe_yoy(avg_cpar, prev["CPAR"].mean() if "CPAR" in prev.columns else None)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Spend", f"${total_spend:,.0f}" if total_spend else "N/A")
k2.metric("Total Usage", f"{total_usage:,.0f}" if total_usage else "N/A")
k3.metric("Avg CPOR", f"${avg_cpor:,.2f}" if avg_cpor else "N/A")
k4.metric("Avg CPAR", f"${avg_cpar:,.2f}" if avg_cpar else "N/A")

k5, k6, k7, k8 = st.columns(4)
k5.metric("YOY Spend Change", f"{yoy_spend:.1f}%" if yoy_spend else "N/A")
k6.metric("YOY Usage Change", f"{yoy_usage:.1f}%" if yoy_usage else "N/A")
k7.metric("YOY CPOR Change", f"{yoy_cpor:.1f}%" if yoy_cpor else "N/A")
k8.metric("YOY CPAR Change", f"{yoy_cpar:.1f}%" if yoy_cpar else "N/A")

st.markdown("""
**What these KPIs show:**  
These metrics summarize the overall performance of the portfolio for the selected year.  
They highlight total spend, total usage, and average efficiency, along with year‑over‑year changes that reveal improvement or decline.
""")

# -----------------------------
# METRIC SELECTION
# -----------------------------
if metric_category == "Cost Efficiency":
    metric_options = ["CPOR", "CPAR", "Cost_per_Unit"]
elif metric_category == "Usage Efficiency":
    metric_options = ["Usage_per_Occupied_Room"]
elif metric_category == "Rate Efficiency":
    metric_options = ["Cost_per_Unit"]
else:
    metric_options = ["CPOR", "Usage_per_Occupied_Room"]

available_metrics = [m for m in metric_options if m in f.columns]
selected_metric = st.selectbox("Benchmark Metric", available_metrics)

# -----------------------------
# RANK DF (used in summary + ranking)
# -----------------------------
rank_df = (
    f.groupby("Property Name", as_index=False)[selected_metric]
    .mean()
    .dropna(subset=[selected_metric])
)

if not rank_df.empty:
    rank_df = rank_df.sort_values(selected_metric, ascending=True)
    rank_df["Rank"] = range(1, len(rank_df) + 1)

# -----------------------------
# OUTLIER DETECTION (used in summary + outlier section)
# -----------------------------
outlier_rows = []
outlier_metrics = [
    ("CPOR", "CPOR"),
    ("CPAR", "CPAR"),
    ("Cost_per_Unit", "Cost per Unit"),
    ("Usage_per_Occupied_Room", "Usage per Occ Room"),
]

for col_name, label in outlier_metrics:
    if col_name in f.columns:
        agg = (
            f.groupby("Property Name", as_index=False)[col_name]
            .mean()
            .dropna(subset=[col_name])
        )
        if not agg.empty:
            mean = agg[col_name].mean()
            std = agg[col_name].std()
            if std and std > 0:
                agg["Z"] = (agg[col_name] - mean) / std
                for _, row in agg.iterrows():
                    if abs(row["Z"]) >= 2:
                        outlier_rows.append(
                            {
                                "Property Name": row["Property Name"],
                                "Metric": label,
                                "Value": round(row[col_name], 3),
                                "Z-Score": round(row["Z"], 2),
                            }
                        )

# -----------------------------
# BENCHMARKING SUMMARY (SECOND)
# -----------------------------
st.subheader("Benchmarking Summary")

summary_lines = []

if not rank_df.empty:
    summary_lines.append(f"- **Top performer:** {rank_df.iloc[0]['Property Name']}")
    summary_lines.append(f"- **Lowest performer:** {rank_df.iloc[-1]['Property Name']}")

if outlier_rows:
    summary_lines.append(f"- **{len(outlier_rows)} properties** show unusual efficiency patterns.")
else:
    summary_lines.append("- No strong outliers detected.")

if yoy_cpor:
    summary_lines.append(f"- CPOR changed **{yoy_cpor:.1f}%** vs last year.")
if yoy_cpar:
    summary_lines.append(f"- CPAR changed **{yoy_cpar:.1f}%** vs last year.")

st.markdown("\n".join(summary_lines))

# -----------------------------
# OUTLIERS (THIRD)
# -----------------------------
st.subheader("Properties Requiring Attention")

if outlier_rows:
    st.dataframe(pd.DataFrame(outlier_rows))
    st.markdown("""
**What this table shows:**  
These properties have efficiency values that fall far outside the portfolio’s normal range.  
High Z‑scores indicate unusual behavior that may require investigation, such as leaks, equipment issues, or billing anomalies.
""")
else:
    st.info("No strong outliers detected.")

# -----------------------------
# UTILITY-LEVEL BENCHMARKING (FOURTH — LINE GRAPH)
# -----------------------------
st.subheader("Utility-Level Benchmarking (Line Trends)")

if {"Utility", "Month_Num", selected_metric}.issubset(f.columns):
    util_df = (
        f.groupby(["Utility", "Month_Num"], as_index=False)[selected_metric]
        .mean()
        .dropna(subset=[selected_metric])
    )

    if not util_df.empty:
        chart_util_line = (
            alt.Chart(util_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("Month_Num:O", title="Month"),
                y=alt.Y(f"{selected_metric}:Q", title=selected_metric.replace("_", " ")),
                color=alt.Color("Utility:N", title="Utility"),
                tooltip=["Utility", "Month_Num", selected_metric],
            )
            .properties(height=350)
        )
        st.altair_chart(chart_util_line, use_container_width=True)

        st.markdown("""
**What this graph shows:**  
This line chart compares how each utility’s efficiency changes month‑to‑month across the selected year.  
It highlights seasonal patterns, spikes, or dips in performance and helps identify which utilities are driving cost or usage changes across the portfolio.
""")
    else:
        st.info("No utility-level data available for line benchmarking.")
else:
    st.info("Utility-level benchmarking requires Utility, Month_Num, and the selected metric.")

# -----------------------------
# PORTFOLIO EFFICIENCY TREND (LINE GRAPH)
# -----------------------------
st.subheader("Portfolio Efficiency Trend (All Properties)")

if {"Property Name", "Month_Num", selected_metric}.issubset(f.columns):

    trend_df = (
        f.groupby(["Property Name", "Month_Num"], as_index=False)[selected_metric]
        .mean()
        .dropna(subset=[selected_metric])
    )

    if not trend_df.empty:
        chart_trend = (
            alt.Chart(trend_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("Month_Num:O", title="Month"),
                y=alt.Y(f"{selected_metric}:Q", title=selected_metric.replace("_", " ")),
                color=alt.Color("Property Name:N", title="Property"),
                tooltip=["Property Name", "Month_Num", selected_metric],
            )
            .properties(height=400)
        )
        st.altair_chart(chart_trend, use_container_width=True)

        st.markdown("""
**What this graph shows:**  
Each line represents a property’s performance for the selected metric across all months of the year.  
This makes it easy to see which properties trend together, which diverge, and where efficiency improves or declines over time.
""")
    else:
        st.info("No data available to build the portfolio trend line chart.")
else:
    st.info("Portfolio trend chart requires Property Name, Month_Num, and the selected metric.")

# -----------------------------
# SCORECARDS
# -----------------------------
st.subheader("Efficiency Scorecards")

metrics_to_grade = [
    ("CPOR", "CPOR"),
    ("CPAR", "CPAR"),
    ("Cost_per_Unit", "Cost per Unit"),
    ("Usage_per_Occupied_Room", "Usage per Occ Room"),
]

score_rows = []

for prop_name, group in f.groupby("Property Name"):
    row = {"Property Name": prop_name}
    for col_name, label in metrics_to_grade:
        if col_name in f.columns:
            prop_val = group[col_name].mean()
            port_val = f[col_name].mean()
            if pd.notna(prop_val) and pd.notna(port_val) and port_val != 0:
                diff_pct = (prop_val - port_val) / port_val * 100
                if diff_pct <= -20:
                    grade = "A"
                elif diff_pct <= -10:
                    grade = "B"
                elif abs(diff_pct) <= 10:
                    grade = "C"
                elif diff_pct <= 25:
                    grade = "D"
                else:
                    grade = "F"
                row[label + " Grade"] = grade
            else:
                row[label + " Grade"] = "N/A"
        else:
            row[label + " Grade"] = "N/A"
    score_rows.append(row)

st.dataframe(pd.DataFrame(score_rows))

st.markdown("""
**What this table shows:**  
Each property receives a grade for every major efficiency metric.  
Grades are based on how the property compares to the portfolio average.  
This creates a simple, intuitive performance profile for each asset.
""")

# -----------------------------
# SCATTERPLOTS
# -----------------------------
st.subheader("Benchmarking Scatterplots")

scatter_cols = st.columns(2)

with scatter_cols[0]:
    st.markdown("**Spend vs Usage**")
    if {"$ Amount", "Usage", "Property Name"}.issubset(f.columns):
        agg_scatter = (
            f.groupby("Property Name", as_index=False)[["$ Amount", "Usage"]]
            .sum()
            .rename(columns={"$ Amount": "Spend"})
        )
        chart_scatter1 = (
            alt.Chart(agg_scatter)
            .mark_circle(size=120)
            .encode(
                x=alt.X("Usage:Q"),
                y=alt.Y("Spend:Q"),
                tooltip=["Property Name", "Usage", "Spend"],
            )
            .properties(height=350)
        )
        st.altair_chart(chart_scatter1, use_container_width=True)

        st.markdown("""
**What this graph shows:**  
This scatterplot compares total usage to total spend for each property.  
Properties in the upper‑right corner use more and spend more, while those lower‑left use less and spend less.  
Outliers may indicate inefficiencies, leaks, or unusually high utility rates.
""")
    else:
        st.info("Spend vs Usage scatterplot unavailable.")

with scatter_cols[1]:
    st.markdown("**CPOR vs CPAR**")
    if {"CPOR", "CPAR", "Property Name"}.issubset(f.columns):
        agg_eff = (
            f.groupby("Property Name", as_index=False)[["CPOR", "CPAR"]]
            .mean()
            .dropna(subset=["CPOR", "CPAR"])
        )
        chart_scatter2 = (
            alt.Chart(agg_eff)
            .mark_circle(size=120)
            .encode(
                x=alt.X("CPOR:Q"),
                y=alt.Y("CPAR:Q"),
                tooltip=["Property Name", "CPOR", "CPAR"],
            )
            .properties(height=350)
        )
        st.altair_chart(chart_scatter2, use_container_width=True)

        st.markdown("""
**What this graph shows:**  
This chart compares two key efficiency metrics: CPOR (cost per occupied room) and CPAR (cost per available room).  
Properties toward the top‑right are less efficient, while those toward the bottom‑left are more efficient.  
Clusters show similar performance groups; outliers highlight properties needing attention.
""")
    else:
        st.info("CPOR/CPAR scatterplot unavailable.")

# -----------------------------
# HEATMAP
# -----------------------------
st.subheader("Portfolio Efficiency Heatmap")

heat_metrics = [
    ("CPOR", "CPOR"),
    ("CPAR", "CPAR"),
    ("Cost_per_Unit", "Cost per Unit"),
    ("Usage_per_Occupied_Room", "Usage per Occ Room"),
]

heat_rows = []

for prop_name, group in f.groupby("Property Name"):
    for col_name, label in heat_metrics:
        if col_name in f.columns:
            val = group[col_name].mean()
            if pd.notna(val):
                heat_rows.append(
                    {"Property Name": prop_name, "Metric": label, "Value": val}
                )

if heat_rows:
    heat_df = pd.DataFrame(heat_rows)
    chart_heat = (
        alt.Chart(heat_df)
        .mark_rect()
        .encode(
            x=alt.X("Metric:N"),
            y=alt.Y("Property Name:N"),
            color=alt.Color("Value:Q", scale=alt.Scale(scheme="redyellowgreen", reverse=True)),
            tooltip=["Property Name", "Metric", "Value"],
        )
        .properties(height=500)
    )
    st.altair_chart(chart_heat, use_container_width=True)

    st.markdown("""
**What this graph shows:**  
This heatmap compares all properties across multiple efficiency metrics at once.  
Green indicates better performance; red indicates worse performance.  
It provides a quick, at‑a‑glance view of which properties are strong performers and which ones may require deeper investigation.
""")
else:
    st.info("Not enough data for heatmap.")

