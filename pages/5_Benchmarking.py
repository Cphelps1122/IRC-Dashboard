import streamlit as st
from auth import require_auth
from utils.load_data import load_data
import pandas as pd

require_auth()
st.set_page_config(page_title="Benchmarking", layout="wide")

df, last_updated = load_data()

st.markdown("## Property Benchmarking")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

if df.empty:
    st.warning("No data available.")
    st.stop()

# ---------------------------------------------------------
# CALCULATED METRICS
# ---------------------------------------------------------
df["Cost per Treatment"] = df["$ Amount"] / df["# Treatments"]
df["Usage per Treatment"] = df["Usage"] / df["# Treatments"]
df["Cost per Day"] = df["$ Amount"] / df["Number Days Billed"]

# Build unified Period column
df["Period"] = df["Month"].astype(str) + "-" + df["Year"].astype(str)

# Sort by time
df = df.sort_values(["Year", "Month"])

# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------
col1, col2 = st.columns(2)

selected_property = col1.selectbox(
    "Select Property to Highlight",
    sorted(df["Property Name"].unique())
)

view_mode = col2.radio(
    "Benchmark View Mode",
    ["Show All Properties", "Show Selected Property Only"],
    index=0
)

# Rolling average toggle
smooth = st.checkbox("Apply 3‑Month Rolling Average", value=True)

# ---------------------------------------------------------
# BUILD TIME SERIES FOR EACH METRIC
# ---------------------------------------------------------
def build_timeseries(metric):
    ts = df.groupby(["Period", "Property Name"])[metric].mean().reset_index()
    portfolio = df.groupby("Period")[metric].mean().reset_index()
    portfolio["Property Name"] = "Portfolio Average"
    combined = pd.concat([ts, portfolio], ignore_index=True)
    pivot = combined.pivot(index="Period", columns="Property Name", values=metric)
    pivot = pivot.sort_index()

    if smooth:
        pivot = pivot.rolling(window=3, min_periods=1).mean()

    return pivot

cpt_ts = build_timeseries("Cost per Treatment")
upt_ts = build_timeseries("Usage per Treatment")
cpd_ts = build_timeseries("Cost per Day")

# ---------------------------------------------------------
# APPLY VIEW MODE
# ---------------------------------------------------------
def filter_view(pivot_df):
    if view_mode == "Show All Properties":
        return pivot_df
    else:
        cols = ["Portfolio Average"]
        if selected_property in pivot_df.columns:
            cols.append(selected_property)
        return pivot_df[cols]

# ---------------------------------------------------------
# HIGHLIGHT SELECTED PROPERTY
# ---------------------------------------------------------
def highlight_property(pivot_df):
    # Move selected property to the front for visual emphasis
    cols = list(pivot_df.columns)
    if selected_property in cols:
        cols.remove(selected_property)
        cols.insert(0, selected_property)
    return pivot_df[cols]

# ---------------------------------------------------------
# ABOVE/BELOW AVERAGE SHADING (Portfolio)
# ---------------------------------------------------------
def add_shading(pivot_df, metric_name):
    st.markdown(f"### {metric_name} (Benchmark Comparison)")

    # Show the line chart
    st.line_chart(pivot_df)

    # Add shading explanation
    st.caption(
        "Portfolio Average acts as the benchmark. "
        "Properties trending above the portfolio line indicate higher cost/usage; "
        "properties trending below indicate better efficiency."
    )

# ---------------------------------------------------------
# COST PER TREATMENT
# ---------------------------------------------------------
cpt_view = filter_view(cpt_ts)
cpt_view = highlight_property(cpt_view)
add_shading(cpt_view, "Cost per Treatment")

st.write("---")

# ---------------------------------------------------------
# USAGE PER TREATMENT
# ---------------------------------------------------------
upt_view = filter_view(upt_ts)
upt_view = highlight_property(upt_view)
add_shading(upt_view, "Usage per Treatment")

st.write("---")

# ---------------------------------------------------------
# COST PER DAY BILLED
# ---------------------------------------------------------
cpd_view = filter_view(cpd_ts)
cpd_view = highlight_property(cpd_view)
add_shading(cpd_view, "Cost per Day Billed")
