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

st.title("Property Energy Detail")

# -----------------------------
# INFO POPUP (KEY / LEGEND)
# -----------------------------
with st.expander("ℹ️ Key / Definitions"):
    st.markdown("""
### **Metric Definitions**

**MoM% (Month-over-Month Percent Change)**  
How much a metric changed compared to the previous month.  
- Positive = increase  
- Negative = decrease  
- Large swings (>30%) may indicate issues or seasonal patterns.

**Z-Score (Statistical Outlier Score)**  
Measures how unusual a value is compared to the property's normal pattern.  
- 0 = normal  
- ±1 = mild deviation  
- ±2 = significant anomaly  
- ±3 = extreme anomaly  

**CPOR (Cost per Occupied Room)**  
Spend divided by occupied rooms. Measures efficiency.

**CPAR (Cost per Available Room)**  
Spend divided by total rooms. Good for comparing properties of different sizes.

**Cost per Unit**  
Spend divided by usage. Shows utility rate efficiency.

**Usage per Occupied Room**  
How much utility is consumed per room actually used.

**Billing Health Terms**  
- **Missing Month**: No bill recorded for that month  
- **Duplicate Bill**: More than one bill for the same utility/month  
- **Zero Usage**: Bill shows usage = 0 (possible meter issue)  
- **Zero Spend**: Bill shows cost = 0 (possible billing error)
""")

# -----------------------------
# FILTERS
# -----------------------------
col1, col2 = st.columns(2)

properties = sorted(df["Property Name"].unique())
years = sorted(df["Year"].dropna().unique()) if "Year" in df.columns else []

prop = col1.selectbox("Select Property", properties)
selected_years = col2.multiselect("Years", years, default=years)

f = df[df["Property Name"] == prop].copy()
if selected_years:
    f = f[f["Year"].isin(selected_years)]

if f.empty:
    st.warning("No data available for this property and year selection.")
    st.stop()

# -----------------------------
# YOY KPIs
# -----------------------------
total_spend = f["$ Amount"].sum() if "$ Amount" in f.columns else None
total_usage = f["Usage"].sum() if "Usage" in f.columns else None

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

    cy_cpor = f[f["Year"] == current_year]["CPOR"].mean() if "CPOR" in f.columns else None
    py_cpor = f[f["Year"] == prev_year]["CPOR"].mean() if "CPOR" in f.columns else None
    yoy_cpor = (
        (cy_cpor - py_cpor) / py_cpor * 100
        if py_cpor not in (0, None) and cy_cpor is not None
        else None
    )
else:
    yoy_spend = yoy_usage = yoy_cpor = None

colA, colB, colC = st.columns(3)
colA.metric("Total Spend", f"${total_spend:,.0f}" if total_spend is not None else "N/A")
colB.metric("Total Usage", f"{total_usage:,.0f}" if total_usage is not None else "N/A")
colC.metric(
    "YOY Spend Change",
    f"{yoy_spend:.1f}%" if yoy_spend is not None else "N/A",
)

colD, colE = st.columns(2)
colD.metric(
    "YOY Usage Change",
    f"{yoy_usage:.1f}%" if yoy_usage is not None else "N/A",
)
colE.metric(
    "YOY CPOR Change",
    f"{yoy_cpor:.1f}%" if yoy_cpor is not None else "N/A",
)

# -----------------------------
# UTILITY MIX DONUTS
# -----------------------------
st.subheader("Utility Mix for This Property")

if {"Utility", "$ Amount"}.issubset(f.columns):
    spend_mix = (
        f.groupby("Utility", as_index=False)["$ Amount"]
        .sum()
        .rename(columns={"$ Amount": "Spend"})
    )
    spend_mix = spend_mix[spend_mix["Spend"] > 0]

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("**Spend Mix**")
        if not spend_mix.empty:
            chart_spend_mix = (
                alt.Chart(spend_mix)
                .mark_arc(innerRadius=50)
                .encode(
                    theta=alt.Theta("Spend:Q", stack=True),
                    color=alt.Color("Utility:N", title="Utility"),
                    tooltip=["Utility", "Spend"],
                )
                .properties(height=300)
            )
            st.altair_chart(chart_spend_mix, use_container_width=True)
        else:
            st.info("No spend data available for utility mix.")

    with col_m2:
        st.markdown("**Usage Mix**")
        if {"Utility", "Usage"}.issubset(f.columns):
            usage_mix = (
                f.groupby("Utility", as_index=False)["Usage"]
                .sum()
                .rename(columns={"Usage": "UsageTotal"})
            )
            usage_mix = usage_mix[usage_mix["UsageTotal"] > 0]
            if not usage_mix.empty:
                chart_usage_mix = (
                    alt.Chart(usage_mix)
                    .mark_arc(innerRadius=50)
                    .encode(
                        theta=alt.Theta("UsageTotal:Q", stack=True),
                        color=alt.Color("Utility:N", title="Utility"),
                        tooltip=["Utility", "UsageTotal"],
                    )
                    .properties(height=300)
                )
                st.altair_chart(chart_usage_mix, use_container_width=True)
            else:
                st.info("No usage data available for utility mix.")
        else:
            st.info("Usage column not available for utility mix.")
else:
    st.info("Utility-level data not available for mix charts.")

# -----------------------------
# BILLING HEALTH CHECK
# -----------------------------
st.subheader("Billing Health Check")

health_msgs = []

if {"Billing Date", "Year", "Month_Num"}.issubset(f.columns):
    bh = f.dropna(subset=["Billing Date", "Year", "Month_Num"]).copy()
    if not bh.empty:
        years_in_scope = sorted(bh["Year"].unique())
        missing_by_year = {}
        duplicate_months = []
        zero_usage_months = []
        zero_spend_months = []

        for y in years_in_scope:
            sub = bh[bh["Year"] == y]
            months_present = sorted(sub["Month_Num"].unique())
            expected = set(range(1, 13))
            missing = sorted(expected - set(months_present))
            if missing:
                missing_by_year[y] = missing

            dup = (
                sub.groupby(["Year", "Month_Num", "Utility"])
                .size()
                .reset_index(name="count")
            )
            duplicate_months.extend(
                dup[dup["count"] > 1][["Year", "Month_Num", "Utility"]].to_dict("records")
            )

            if "Usage" in sub.columns:
                zero_usage = sub[sub["Usage"] == 0][["Year", "Month_Num", "Utility"]]
                zero_usage_months.extend(zero_usage.to_dict("records"))

            if "$ Amount" in sub.columns:
                zero_spend = sub[sub["$ Amount"] == 0][["Year", "Month_Num", "Utility"]]
                zero_spend_months.extend(zero_spend.to_dict("records"))

        if not missing_by_year and not duplicate_months and not zero_usage_months and not zero_spend_months:
            st.success("Billing health looks good. No missing, duplicate, or zero-activity months detected.")
        else:
            if missing_by_year:
                for y, miss in missing_by_year.items():
                    health_msgs.append(f"Missing months in {y}: {', '.join(str(m) for m in miss)}")
            if duplicate_months:
                health_msgs.append(f"Duplicate bills detected: {len(duplicate_months)} month-utility combinations.")
            if zero_usage_months:
                health_msgs.append(f"Months with zero usage: {len(zero_usage_months)}.")
            if zero_spend_months:
                health_msgs.append(f"Months with zero spend: {len(zero_spend_months)}.")

            for msg in health_msgs:
                st.warning(msg)
    else:
        st.info("Not enough billing data to assess health.")
else:
    st.info("Billing date/year/month information not sufficient for health check.")

# -----------------------------
# ANOMALY DETECTION + SUMMARY
# -----------------------------
st.subheader("Anomaly Detection (Spend & Usage)")

anomaly_rows = []
anomaly_summary = {
    "spend_spikes": 0,
    "usage_spikes": 0,
    "spend_drops": 0,
    "usage_drops": 0,
}

if {"Billing Date", "Year", "Month_Num"}.issubset(f.columns):
    agg_cols = []
    if "$ Amount" in f.columns:
        agg_cols.append("$ Amount")
    if "Usage" in f.columns:
        agg_cols.append("Usage")

    if agg_cols:
        monthly = (
            f.groupby(["Year", "Month_Num"], as_index=False)[agg_cols]
            .sum()
            .sort_values(["Year", "Month_Num"])
        )

        # Z-score anomalies
        for col in agg_cols:
            series = monthly[col]
            mean = series.mean()
            std = series.std()
            if std and std > 0:
                monthly[f"{col}_z"] = (series - mean) / std
            else:
                monthly[f"{col}_z"] = 0

        # MoM percent change
        monthly["date_key"] = pd.to_datetime(
            monthly["Year"].astype(str) + "-" + monthly["Month_Num"].astype(str) + "-01",
            errors="coerce",
        )
        monthly = monthly.sort_values("date_key")

        for col in agg_cols:
            monthly[f"{col}_mom_pct"] = monthly[col].pct_change()

        # Flag anomalies + build summary
        for _, row in monthly.iterrows():
            for col in agg_cols:
                z = row.get(f"{col}_z", 0)
                mom = row.get(f"{col}_mom_pct", 0)

                is_anomaly = abs(z) >= 2 or (pd.notna(mom) and abs(mom) >= 0.3)

                if is_anomaly:
                    anomaly_rows.append(
                        {
                            "Year": int(row["Year"]),
                            "Month": int(row["Month_Num"]),
                            "Metric": col,
                            "Value": row[col],
                            "Z-Score": round(z, 2),
                            "MoM %": round(mom * 100, 1) if pd.notna(mom) else None,
                        }
                    )

                    # Build summary counts
                    if col == "$ Amount":
                        if mom and mom > 0.3:
                            anomaly_summary["spend_spikes"] += 1
                        elif mom and mom < -0.3:
                            anomaly_summary["spend_drops"] += 1
                    if col == "Usage":
                        if mom and mom > 0.3:
                            anomaly_summary["usage_spikes"] += 1
                        elif mom and mom < -0.3:
                            anomaly_summary["usage_drops"] += 1

# -----------------------------
# ANOMALY SUMMARY NARRATIVE
# -----------------------------
if anomaly_rows:
    st.markdown("### Summary of Detected Anomalies")

    summary_text = []

    if anomaly_summary["spend_spikes"] > 0:
        summary_text.append(f"- **Spend spikes detected:** {anomaly_summary['spend_spikes']} months")

    if anomaly_summary["usage_spikes"] > 0:
        summary_text.append(f"- **Usage spikes detected:** {anomaly_summary['usage_spikes']} months")

    if anomaly_summary["spend_drops"] > 0:
        summary_text.append(f"- **Spend drops detected:** {anomaly_summary['spend_drops']} months")

    if anomaly_summary["usage_drops"] > 0:
        summary_text.append(f"- **Usage drops detected:** {anomaly_summary['usage_drops']} months")

    if not summary_text:
        summary_text.append("- Anomalies detected, but no major spikes or drops.")

    st.markdown("\n".join(summary_text))

    st.write("### Detailed Anomaly Table")
    st.dataframe(pd.DataFrame(anomaly_rows))
else:
    st.info("No significant anomalies detected based on current thresholds.")

# -----------------------------
# EFFICIENCY SCORECARD
# -----------------------------
st.subheader("Efficiency Scorecard")

metrics_to_grade = [
    ("CPOR", "Cost per Occupied Room"),
    ("CPAR", "Cost per Available Room"),
    ("Cost_per_Unit", "Cost per Unit"),
    ("Usage_per_Occupied_Room", "Usage per Occupied Room"),
]

score_rows = []

df_portfolio = df.copy()
if selected_years and "Year" in df_portfolio.columns:
    df_portfolio = df_portfolio[df_portfolio["Year"].isin(selected_years)]

for col_name, label in metrics_to_grade:
    if col_name in f.columns and col_name in df_portfolio.columns:
        prop_val = f[col_name].mean()
        port_val = df_portfolio[col_name].mean()
        if pd.notna(prop_val) and pd.notna(port_val) and port_val != 0:
            diff_pct = (prop_val - port_val) / port_val * 100

            # Grade thresholds (lower is better for cost/usage metrics)
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

            score_rows.append(
                {
                    "Metric": label,
                    "Property Value": round(prop_val, 3),
                    "Portfolio Avg": round(port_val, 3),
                    "Diff %": round(diff_pct, 1),
                    "Grade": grade,
                }
            )

if score_rows:
    st.dataframe(pd.DataFrame(score_rows))
else:
    st.info("Not enough data to compute efficiency scorecard for this property.")

# -----------------------------
# RAW TABLE
# -----------------------------
st.subheader("Raw Data")
st.dataframe(f)

