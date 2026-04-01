import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.load_data import load_data

# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(
    page_title="Property Portfolio",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================================================================
# LOAD LIVE DATA FROM GOOGLE SHEETS
# ================================================================
df, last_updated = load_data()

if df.empty:
    st.error("No data returned from Google Sheets.")
    st.stop()

# ================================================================
# COLUMN DETECTION
# ================================================================
_prop_candidates = [
    "Property Name", "Property", "Account", "Location",
    "Site", "Address", "Building", "Facility", "Name",
]
PROP_COL = None
for candidate in _prop_candidates:
    match = [c for c in df.columns if c.strip().lower() == candidate.lower()]
    if match:
        PROP_COL = match[0]
        break

if PROP_COL is None:
    st.error(
        f"⚠️ Could not auto-detect the property name column.\n\n"
        f"**Your columns:** {list(df.columns)}\n\n"
        f"Add your property column name to the `_prop_candidates` list near line 30."
    )
    st.stop()

_util_candidates = ["Utility", "Utility Type", "Service", "Type", "Service Type"]
UTIL_COL = None
for candidate in _util_candidates:
    match = [c for c in df.columns if c.strip().lower() == candidate.lower()]
    if match:
        UTIL_COL = match[0]
        break

# ================================================================
# AGGREGATE BILLING DATA → One summary dict per property
# ================================================================
now = pd.Timestamp.now()
twelve_months_ago = now - pd.DateOffset(months=12)
twentyfour_months_ago = now - pd.DateOffset(months=24)

PORTFOLIO = []

for prop_name, grp in df.groupby(PROP_COL):
    grp = grp.sort_values("Billing Date")

    total_cost = grp["$ Amount"].sum() if "$ Amount" in grp.columns else 0
    total_usage = grp["Usage"].sum() if "Usage" in grp.columns else 0
    bill_count = len(grp)

    recent = grp[grp["Billing Date"] >= twelve_months_ago] if "Billing Date" in grp.columns else grp
    cost_12m = recent["$ Amount"].sum() if "$ Amount" in recent.columns else 0
    avg_monthly = cost_12m / max(len(recent), 1)

    prior = grp[
        (grp["Billing Date"] >= twentyfour_months_ago)
        & (grp["Billing Date"] < twelve_months_ago)
    ] if "Billing Date" in grp.columns else pd.DataFrame()
    cost_prior = prior["$ Amount"].sum() if not prior.empty and "$ Amount" in prior.columns else 0

    if cost_prior > 0:
        yoy_change = round(((cost_12m - cost_prior) / cost_prior) * 100, 1)
    else:
        yoy_change = 0.0

    cost_history = []
    if "Billing Date" in grp.columns and "$ Amount" in grp.columns:
        recent_data = grp[grp["Billing Date"] >= twelve_months_ago].copy()
        if not recent_data.empty:
            recent_data["month"] = recent_data["Billing Date"].dt.to_period("M")
            monthly = recent_data.groupby("month")["$ Amount"].sum().sort_index()
            cost_history = monthly.tolist()
    if len(cost_history) < 2 and "$ Amount" in grp.columns:
        grp_copy = grp.copy()
        if "Billing Date" in grp_copy.columns:
            grp_copy["month"] = grp_copy["Billing Date"].dt.to_period("M")
            monthly = grp_copy.groupby("month")["$ Amount"].sum().sort_index()
            cost_history = monthly.tolist()

    last_bill = grp["Billing Date"].max() if "Billing Date" in grp.columns else None
    if pd.notna(last_bill):
        days_since = (now - last_bill).days
        if days_since <= 90:
            status = "Active"
        elif days_since <= 180:
            status = "Pending"
        else:
            status = "Inactive"
        last_bill_str = last_bill.strftime("%Y-%m-%d")
    else:
        status = "Unknown"
        last_bill_str = "N/A"

    utilities = []
    if UTIL_COL and UTIL_COL in grp.columns:
        utilities = grp[UTIL_COL].dropna().unique().tolist()

    PORTFOLIO.append({
        "id": prop_name.lower().replace(" ", "-").replace("/", "-"),
        "name": str(prop_name),
        "status": status,
        "total_cost": round(total_cost, 2),
        "avg_monthly": round(avg_monthly, 2),
        "total_usage": round(total_usage, 1),
        "bill_count": bill_count,
        "yoy_change": yoy_change,
        "cost_history": cost_history,
        "last_updated": last_bill_str,
        "utilities": utilities,
    })

status_order = {"Active": 0, "Pending": 1, "Inactive": 2, "Unknown": 3}
PORTFOLIO.sort(key=lambda p: (status_order.get(p["status"], 9), -p["total_cost"]))


# ================================================================
# GLOBAL CSS
# ================================================================
GLOBAL_CSS = """
<style>
.block-container { padding-top: 1.5rem !important; }

.summary-bar {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 12px;
    background: linear-gradient(135deg, #1a1d27 0%, #252839 100%);
    border: 1px solid #2a2d3a;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,.4);
}
.summary-metric {
    display: flex;
    flex-direction: column;
    gap: 3px;
    position: relative;
    padding-right: 14px;
}
.summary-metric:not(:last-child)::after {
    content: '';
    position: absolute;
    right: 0; top: 4px; bottom: 4px;
    width: 1px;
    background: #2a2d3a;
}
.sum-label {
    font-size: .7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: #6b7280;
}
.sum-value {
    font-size: 1.45rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.2;
}
.sum-delta {
    font-size: .76rem;
    font-weight: 600;
}
.sum-delta.up   { color: #34d399; }
.sum-delta.down { color: #f87171; }

.prop-card {
    background: #1e2130;
    border: 1px solid #2a2d3a;
    border-radius: 14px;
    padding: 28px 32px 24px;
    display: flex;
    flex-direction: column;
    gap: 18px;
    position: relative;
    overflow: hidden;
    max-width: 720px;
    margin: 0 auto;
    transition: all .25s ease;
}
.prop-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: #3d8bfd;
}

.card-hdr {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}
.card-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.3;
}
.card-addr {
    font-size: .8rem;
    color: #6b7280;
    margin-top: 2px;
}

.badge {
    font-size: .7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    padding: 5px 12px;
    border-radius: 20px;
    white-space: nowrap;
    flex-shrink: 0;
}
.badge-active   { background: rgba(52,211,153,.12); color: #34d399; }
.badge-pending  { background: rgba(251,191,36,.12);  color: #fbbf24; }
.badge-inactive { background: rgba(248,113,113,.12); color: #f87171; }
.badge-unknown  { background: rgba(107,114,128,.12); color: #6b7280; }

.kpi-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    padding: 16px 0;
    border-top: 1px solid #2a2d3a;
    border-bottom: 1px solid #2a2d3a;
}
.kpi-label {
    font-size: .7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #6b7280;
}
.kpi-val {
    font-size: 1.2rem;
    font-weight: 700;
    color: #e8eaed;
}
.kpi-val.pos { color: #34d399; }
.kpi-val.neg { color: #f87171; }

.spark-row {
    display: flex;
    align-items: center;
    gap: 14px;
}
.spark-lbl {
    font-size: .76rem;
    color: #6b7280;
    white-space: nowrap;
    flex-shrink: 0;
}
.spark-chart {
    flex: 1;
    height: 48px;
    min-width: 0;
}
.spark-chart svg { width: 100%; height: 100%; }

.card-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 4px;
}
.card-updated {
    font-size: .74rem;
    color: #6b7280;
}
.util-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 2px;
}
.util-tag {
    font-size: .66rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 4px;
    background: rgba(61,139,253,.1);
    color: #3d8bfd;
    text-transform: uppercase;
    letter-spacing: .04em;
}

@media (max-width: 540px) {
    .summary-bar { grid-template-columns: repeat(2, 1fr); }
    .kpi-strip { grid-template-columns: repeat(2, 1fr); }
    .prop-card { padding: 20px; }
}
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ================================================================
# SPARKLINE SVG GENERATOR
# ================================================================
def make_sparkline(data: list, width: int = 200, height: int = 48) -> str:
    if not data or len(data) < 2:
        return ""
    mn = min(data)
    mx = max(data)
    rng = mx - mn if mx != mn else 1
    pad = 4
    uh = height - pad * 2

    pts = []
    for i, v in enumerate(data):
        x = (i / (len(data) - 1)) * width
        y = pad + uh - ((v - mn) / rng) * uh
        pts.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(pts)
    fill_poly = f"0,{height} {polyline} {width},{height}"
    trend_clr = "#34d399" if data[-1] <= data[0] else "#f87171"
    last_x = width
    last_y = pad + uh - ((data[-1] - mn) / rng) * uh
    grad_id = f"sg{abs(hash(tuple(data))) % 99999}"

    return (
        f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{trend_clr}" stop-opacity=".25"/>'
        f'<stop offset="100%" stop-color="{trend_clr}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<polygon points="{fill_poly}" fill="url(#{grad_id})"/>'
        f'<polyline points="{polyline}" fill="none" stroke="{trend_clr}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{last_x}" cy="{last_y:.1f}" r="3" fill="{trend_clr}"/>'
        f'</svg>'
    )


# ================================================================
# FORMATTERS
# ================================================================
def fmt_currency(v):
    if abs(v) >= 1000:
        return f"${v/1000:,.1f}K"
    return f"${v:,.2f}"

def fmt_currency_full(v):
    return f"${v:,.2f}"

def fmt_usage(v):
    if abs(v) >= 1000:
        return f"{v/1000:,.1f}K"
    return f"{v:,.0f}"


# ================================================================
# SUMMARY BAR
# ================================================================
total_spend     = sum(p["total_cost"] for p in PORTFOLIO)
total_usage_all = sum(p["total_usage"] for p in PORTFOLIO)
active_count    = sum(1 for p in PORTFOLIO if p["status"] == "Active")
prop_count      = len(PORTFOLIO)
avg_monthly_all = sum(p["avg_monthly"] for p in PORTFOLIO)

spend_props = [p for p in PORTFOLIO if p["total_cost"] > 0]
if spend_props and sum(p["total_cost"] for p in spend_props) > 0:
    weighted_yoy = (
        sum(p["yoy_change"] * p["total_cost"] for p in spend_props)
        / sum(p["total_cost"] for p in spend_props)
    )
else:
    weighted_yoy = 0.0

yoy_cls = "down" if weighted_yoy > 0 else "up"
yoy_arrow = "▲" if weighted_yoy > 0 else "▼"

summary_html = f"""
<div class="summary-bar">
    <div class="summary-metric">
        <span class="sum-label">Properties</span>
        <span class="sum-value">{prop_count}</span>
        <span class="sum-delta up">{active_count} Active</span>
    </div>
    <div class="summary-metric">
        <span class="sum-label">Total Spend (12 mo)</span>
        <span class="sum-value">{fmt_currency_full(total_spend)}</span>
        <span class="sum-delta {yoy_cls}">{yoy_arrow} {abs(weighted_yoy):.1f}% YoY</span>
    </div>
    <div class="summary-metric">
        <span class="sum-label">Avg Monthly / Property</span>
        <span class="sum-value">{fmt_currency(avg_monthly_all / max(prop_count, 1))}</span>
    </div>
    <div class="summary-metric">
        <span class="sum-label">Total Usage</span>
        <span class="sum-value">{fmt_usage(total_usage_all)}</span>
    </div>
    <div class="summary-metric">
        <span class="sum-label">Total Bills</span>
        <span class="sum-value">{sum(p['bill_count'] for p in PORTFOLIO):,}</span>
    </div>
    <div class="summary-metric">
        <span class="sum-label">Last Updated</span>
        <span class="sum-value" style="font-size:1rem">{last_updated}</span>
    </div>
</div>
"""
st.markdown(summary_html, unsafe_allow_html=True)


# ================================================================
# PROPERTY DROPDOWN SELECTOR
# ================================================================
property_names = [p["name"] for p in PORTFOLIO]
selected_name = st.selectbox(
    "Select a Property",
    options=property_names,
    index=0,
    key="portfolio_property_selector",
)

# Find the selected property
prop = next(p for p in PORTFOLIO if p["name"] == selected_name)


# ================================================================
# RENDER: SELECTED PROPERTY CARD
# ================================================================
status_lower = prop["status"].lower()
badge_cls = (
    "badge-active" if status_lower == "active"
    else "badge-pending" if status_lower == "pending"
    else "badge-inactive" if status_lower == "inactive"
    else "badge-unknown"
)

yoy_sign = "+" if prop["yoy_change"] > 0 else ""
yoy_color = "#34d399" if prop["yoy_change"] <= 0 else "#f87171"

spark_svg = make_sparkline(prop["cost_history"])

util_tags = ""
if prop["utilities"]:
    tags = "".join(
        f'<span class="util-tag">{u}</span>' for u in prop["utilities"][:6]
    )
    util_tags = f'<div class="util-tags">{tags}</div>'

card_html = f"""
<div class="prop-card">
    <div class="card-hdr">
        <div>
            <div class="card-title">{prop['name']}</div>
            {util_tags}
        </div>
        <span class="badge {badge_cls}">{prop['status']}</span>
    </div>
    <div class="kpi-strip">
        <div>
            <div class="kpi-label">Total Cost</div>
            <div class="kpi-val">{fmt_currency(prop['total_cost'])}</div>
        </div>
        <div>
            <div class="kpi-label">Avg Monthly</div>
            <div class="kpi-val">{fmt_currency(prop['avg_monthly'])}</div>
        </div>
        <div>
            <div class="kpi-label">Usage</div>
            <div class="kpi-val">{fmt_usage(prop['total_usage'])}</div>
        </div>
        <div>
            <div class="kpi-label">YoY Change</div>
            <div class="kpi-val" style="color:{yoy_color}">{yoy_sign}{prop['yoy_change']}%</div>
        </div>
    </div>
    <div class="spark-row">
        <span class="spark-lbl">12-mo cost trend</span>
        <div class="spark-chart">{spark_svg}</div>
    </div>
    <div class="card-foot">
        <span class="card-updated">Last bill {prop['last_updated']}</span>
        <span class="card-updated">{prop['bill_count']} bills</span>
    </div>
</div>
"""
st.markdown(card_html, unsafe_allow_html=True)

# --- Centered nav button below the card ---
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    if st.button("View Full Details →", key=f"nav_{prop['id']}", use_container_width=True):
        st.session_state["selected_property"] = prop["name"]
        st.switch_page("pages/3_Property_Detail.py")
