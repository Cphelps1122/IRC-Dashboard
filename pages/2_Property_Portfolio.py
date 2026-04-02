"""
IRC-Dashboard  ·  Property Portfolio
Drop-in file: pages/2_Property_Portfolio.py
Dependencies : streamlit, pandas, numpy  (no matplotlib)
"""

import streamlit as st
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from utils.load_data import load_data

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Property Portfolio", page_icon="🏢", layout="wide")

# ── constants ────────────────────────────────────────────────────────────────
UTILITY_OPTIONS = ["Select All", "Water", "Electric", "Gas", "Sewage"]

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12,
}

# ── helpers ──────────────────────────────────────────────────────────────────

def detect_column(df: pd.DataFrame, candidates: list) -> Optional[str]:
    """Return the first column name that exists (case-insensitive)."""
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for c in candidates:
        if c.lower().strip() in cols_lower:
            return cols_lower[c.lower().strip()]
    return None


def _parse_month(val) -> Optional[int]:
    """Convert any plausible month value to 1-12 or None."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, (int, float)):
        v = int(val)
        return v if 1 <= v <= 12 else None
    s = str(val).strip().lower()
    if s in MONTH_MAP:
        return MONTH_MAP[s]
    try:
        v = int(s)
        return v if 1 <= v <= 12 else None
    except ValueError:
        return None


def ensure_year_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Guarantee Year (int) and Month_Num (int 1-12) columns exist.
    Priority: explicit Year/Month columns → Billing Date fallback.
    """
    df = df.copy()

    # ── Year ──
    year_col = detect_column(df, ["Year"])
    bill_col = detect_column(df, ["Billing Date", "BillingDate"])

    if year_col:
        df["Year"] = pd.to_numeric(df[year_col], errors="coerce")
    elif bill_col:
        bd = pd.to_datetime(df[bill_col], errors="coerce")
        df["Year"] = bd.dt.year
    else:
        df["Year"] = np.nan

    # ── Month_Num ──
    month_col = detect_column(df, ["Month_Num", "Month Num"])
    if month_col:
        df["Month_Num"] = pd.to_numeric(df[month_col], errors="coerce")
    else:
        month_name_col = detect_column(df, ["Month"])
        if month_name_col:
            df["Month_Num"] = df[month_name_col].apply(_parse_month)
        elif bill_col:
            bd = pd.to_datetime(df[bill_col], errors="coerce")
            df["Month_Num"] = bd.dt.month
        else:
            df["Month_Num"] = np.nan

    # Fill any remaining NaN from Billing Date if available
    if bill_col:
        bd = pd.to_datetime(df[bill_col], errors="coerce")
        mask_y = df["Year"].isna()
        df.loc[mask_y, "Year"] = bd.loc[mask_y].dt.year
        mask_m = df["Month_Num"].isna()
        df.loc[mask_m, "Month_Num"] = bd.loc[mask_m].dt.month

    return df


def fmt_dollar(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "$0.00"
    return f"${v:,.2f}"


def fmt_number(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "0"
    if isinstance(v, float) and v == int(v):
        return f"{int(v):,}"
    return f"{v:,.1f}"


def fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "N/A"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.1f}%"


# ── pure SVG sparkline (no matplotlib) ───────────────────────────────────────

def make_sparkline(data: list, width: int = 200, height: int = 48) -> str:
    """Return an inline SVG sparkline string. Zero external dependencies."""
    if not data or len(data) < 2:
        return ""
    mn, mx = min(data), max(data)
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
    # green if cost went down or flat, red if cost went up
    trend_clr = "#34d399" if data[-1] <= data[0] else "#f87171"
    last_x = width
    last_y = pad + uh - ((data[-1] - mn) / rng) * uh
    grad_id = f"sg{abs(hash(tuple(data))) % 99999}"
    return (
        f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:{width}px;height:{height}px;">'
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


# ── dataclass ────────────────────────────────────────────────────────────────

@dataclass
class PropertyCard:
    name: str
    total_cost: float = 0.0
    avg_monthly: float = 0.0
    total_usage: float = 0.0
    yoy_change: float = np.nan
    months_active: int = 0
    last_year: int = 0
    last_month: int = 0
    status: str = "Active"
    value_history: list = field(default_factory=list)


# ── build portfolio list ─────────────────────────────────────────────────────

def build_portfolio(df: pd.DataFrame) -> List[PropertyCard]:
    prop_col = detect_column(df, ["Property Name", "PropertyName", "Property"])
    amt_col  = detect_column(df, ["$ Amount", "$Amount", "Amount"])
    usg_col  = detect_column(df, ["Usage"])

    if not prop_col or not amt_col:
        st.error("Required columns not found in data.")
        return []

    cards: List[PropertyCard] = []

    for name, grp in df.groupby(prop_col):
        try:
            card = PropertyCard(name=str(name))

            # ── totals ──
            amounts = pd.to_numeric(grp[amt_col], errors="coerce").dropna()
            card.total_cost = float(amounts.sum())

            if usg_col and usg_col in grp.columns:
                usage_vals = pd.to_numeric(grp[usg_col], errors="coerce").dropna()
                card.total_usage = float(usage_vals.sum())

            # ── year / month logic ──
            valid = grp.dropna(subset=["Year", "Month_Num"]).copy()
            valid["Year"]      = valid["Year"].astype(int)
            valid["Month_Num"] = valid["Month_Num"].astype(int)

            if valid.empty:
                card.status = "No Date Info"
                cards.append(card)
                continue

            card.last_year  = int(valid["Year"].max())
            card.last_month = int(
                valid.loc[valid["Year"] == card.last_year, "Month_Num"].max()
            )

            # months active = distinct (year, month) combos
            combos = valid.groupby(["Year", "Month_Num"]).ngroups
            card.months_active = combos
            card.avg_monthly = card.total_cost / combos if combos else 0.0

            # ── YoY change ──
            years = sorted(valid["Year"].unique())
            if len(years) >= 2:
                cur_yr  = years[-1]
                prev_yr = years[-2]
                cur_amt  = pd.to_numeric(
                    valid.loc[valid["Year"] == cur_yr, amt_col], errors="coerce"
                ).sum()
                prev_amt = pd.to_numeric(
                    valid.loc[valid["Year"] == prev_yr, amt_col], errors="coerce"
                ).sum()
                if prev_amt and prev_amt != 0:
                    card.yoy_change = ((cur_amt - prev_amt) / prev_amt) * 100

            # ── sparkline data (monthly totals in chronological order) ──
            monthly = (
                valid.assign(**{amt_col: pd.to_numeric(valid[amt_col], errors="coerce")})
                .groupby(["Year", "Month_Num"])[amt_col]
                .sum()
                .reset_index()
                .sort_values(["Year", "Month_Num"])
            )
            card.value_history = monthly[amt_col].tolist()

            # ── active / inactive ──
            now_year  = 2026
            now_month = 4
            last_period = card.last_year * 12 + card.last_month
            curr_period = now_year * 12 + now_month
            months_since = curr_period - last_period
            card.status = "Active" if months_since <= 3 else "Inactive"

            cards.append(card)
        except Exception:
            cards.append(PropertyCard(name=str(name), status="Error"))

    # sort: Active first, then alphabetical
    cards.sort(key=lambda c: (0 if c.status == "Active" else 1, c.name))
    return cards


# ── CSS ──────────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    /* summary bar */
    .summary-bar {
        display: flex; gap: 1.5rem; flex-wrap: wrap;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; border-radius: 14px;
        padding: 1.4rem 2rem; margin-bottom: 1.8rem;
    }
    .summary-kpi {
        flex: 1; min-width: 150px; text-align: center;
    }
    .summary-kpi .label {
        font-size: .75rem; color: #94a3b8; text-transform: uppercase;
        letter-spacing: .06em; margin-bottom: .25rem;
    }
    .summary-kpi .value {
        font-size: 1.35rem; font-weight: 700; color: #f1f5f9;
    }

    /* property card */
    .prop-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; border-radius: 14px;
        padding: 2rem; margin-top: .5rem;
    }
    .prop-card h2 {
        margin: 0 0 .25rem 0; font-size: 1.5rem; color: #f1f5f9;
    }
    .badge {
        display: inline-block; font-size: .7rem; font-weight: 600;
        padding: .15rem .55rem; border-radius: 9999px;
        text-transform: uppercase; letter-spacing: .04em;
    }
    .badge-active  { background: #065f46; color: #34d399; }
    .badge-inactive { background: #7f1d1d; color: #fca5a5; }
    .badge-nodata  { background: #44403c; color: #a8a29e; }

    .kpi-grid {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 1.2rem; margin: 1.5rem 0;
    }
    .kpi-box {
        background: rgba(255,255,255,.04); border-radius: 10px;
        padding: 1rem 1.2rem; text-align: center;
    }
    .kpi-box .kpi-label {
        font-size: .72rem; color: #94a3b8; text-transform: uppercase;
        letter-spacing: .05em; margin-bottom: .3rem;
    }
    .kpi-box .kpi-value {
        font-size: 1.3rem; font-weight: 700; color: #e2e8f0;
    }
    .sparkline-wrap {
        margin-top: .8rem;
    }
    .sparkline-title {
        font-size: .72rem; color: #94a3b8; text-transform: uppercase;
        letter-spacing: .05em; margin-bottom: .4rem;
    }
    .yoy-up   { color: #f87171; }
    .yoy-down { color: #34d399; }
    .yoy-na   { color: #94a3b8; }
    </style>
    """, unsafe_allow_html=True)


# ── render functions ─────────────────────────────────────────────────────────

def render_summary_bar(cards: List[PropertyCard]):
    total   = sum(c.total_cost for c in cards)
    avg     = np.mean([c.avg_monthly for c in cards]) if cards else 0
    usage   = sum(c.total_usage for c in cards)
    active  = sum(1 for c in cards if c.status == "Active")
    st.markdown(f"""
    <div class="summary-bar">
        <div class="summary-kpi">
            <div class="label">Properties</div>
            <div class="value">{len(cards)}</div>
        </div>
        <div class="summary-kpi">
            <div class="label">Active</div>
            <div class="value">{active}</div>
        </div>
        <div class="summary-kpi">
            <div class="label">Total Cost</div>
            <div class="value">{fmt_dollar(total)}</div>
        </div>
        <div class="summary-kpi">
            <div class="label">Avg Monthly (per prop)</div>
            <div class="value">{fmt_dollar(avg)}</div>
        </div>
        <div class="summary-kpi">
            <div class="label">Total Usage</div>
            <div class="value">{fmt_number(usage)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_property_card(card: PropertyCard):
    # badge
    if card.status == "Active":
        badge = '<span class="badge badge-active">Active</span>'
    elif card.status == "Inactive":
        badge = '<span class="badge badge-inactive">Inactive</span>'
    else:
        badge = f'<span class="badge badge-nodata">{card.status}</span>'

    # yoy
    if pd.isna(card.yoy_change):
        yoy_html = '<span class="yoy-na">N/A</span>'
    elif card.yoy_change > 0:
        yoy_html = f'<span class="yoy-up">▲ {fmt_pct(card.yoy_change)}</span>'
    else:
        yoy_html = f'<span class="yoy-down">▼ {fmt_pct(card.yoy_change)}</span>'

    # sparkline
    spark_svg = make_sparkline(card.value_history)
    spark_html = ""
    if spark_svg:
        spark_html = f"""
        <div class="sparkline-wrap">
            <div class="sparkline-title">Monthly Cost Trend</div>
            {spark_svg}
        </div>
        """

    st.markdown(f"""
    <div class="prop-card">
        <h2>{card.name}</h2>
        {badge}
        <div class="kpi-grid">
            <div class="kpi-box">
                <div class="kpi-label">Total Cost</div>
                <div class="kpi-value">{fmt_dollar(card.total_cost)}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">Avg Monthly</div>
                <div class="kpi-value">{fmt_dollar(card.avg_monthly)}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">Total Usage</div>
                <div class="kpi-value">{fmt_number(card.total_usage)}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">YoY Change</div>
                <div class="kpi-value">{yoy_html}</div>
            </div>
        </div>
        {spark_html}
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

st.title("🏢 Property Portfolio")

# ── load data ────────────────────────────────────────────────────────────────
try:
    df, last_updated = load_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

if df is None or df.empty:
    st.warning("No data returned from the Google Sheet.")
    st.stop()

# ── ensure Year & Month_Num ─────────────────────────────────────────────────
df = ensure_year_month(df)

# ── detect key columns ──────────────────────────────────────────────────────
prop_col    = detect_column(df, ["Property Name", "PropertyName", "Property"])
utility_col = detect_column(df, ["Utility", "Utility Type", "UtilityType"])

if not prop_col:
    st.error("Cannot find a 'Property Name' column in the data.")
    st.stop()

# ── filters ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    selected_utility = st.selectbox("Utility Type", UTILITY_OPTIONS, index=0)

# apply utility filter
if selected_utility == "Select All" or not utility_col:
    df_filtered = df.copy()
else:
    df_filtered = df[
        df[utility_col].str.strip().str.lower() == selected_utility.strip().lower()
    ].copy()

if df_filtered.empty:
    st.info("No records match the selected utility filter.")
    st.stop()

# property dropdown (populated after utility filter)
property_names = sorted(df_filtered[prop_col].dropna().unique().tolist())

with col2:
    selected_property = st.selectbox("Select Property", property_names)

# ── build cards for ALL filtered properties (for summary bar) ────────────────
ALL_CARDS = build_portfolio(df_filtered)

# ── summary bar (aggregates across all filtered properties) ──────────────────
inject_css()
render_summary_bar(ALL_CARDS)

# ── render selected property card ────────────────────────────────────────────
selected_card = next((c for c in ALL_CARDS if c.name == selected_property), None)

if selected_card:
    render_property_card(selected_card)

    # "View Full Details" button
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    if st.button("View Full Details →", key="detail_nav"):
        st.session_state["selected_property"] = selected_property
        st.switch_page("pages/3_Property_Detail.py")
else:
    st.warning(f"No data found for **{selected_property}**.")

# ── footer ───────────────────────────────────────────────────────────────────
st.caption(f"Last updated: {last_updated}")
