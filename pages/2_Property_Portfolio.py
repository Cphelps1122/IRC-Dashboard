"""
IRC-Dashboard  –  pages/2_Property_Portfolio.py
Property Portfolio: dropdown-driven single-card view with utility filter,
per-utility summary KPI bar, SVG sparkline (base64-encoded), and nav to detail page.

DARK-THEMED CARDS  –  CSS injection on native Streamlit components.
Safe imports only (streamlit, pandas, numpy, base64, dataclasses, typing, datetime).
NO matplotlib.
"""

import streamlit as st
import pandas as pd
import numpy as np
import base64
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

# ── data loader (same one used by other pages) ──────────────────────────
from utils.load_data import load_data

# =========================================================================
# 0.  DARK-CARD CSS  (injected once at top of page)
# =========================================================================

DARK_CARD_CSS = """
<style>
/* ── Dark card container ────────────────────────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
    padding: 4px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,.35) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: transparent !important;
}

/* ── Metric values → white ──────────────────────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricValue"] > div {
    color: #f1f5f9 !important;
}

/* ── Metric labels → slate-400 ──────────────────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] p,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] label,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] div {
    color: #94a3b8 !important;
}

/* ── Subheader (property name) → white ──────────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stSubheader"],
div[data-testid="stVerticalBlockBorderWrapper"] h3,
div[data-testid="stVerticalBlockBorderWrapper"] h2 {
    color: #f1f5f9 !important;
}

/* ── Captions → slate-400 ───────────────────────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] .stCaption,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"],
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p,
div[data-testid="stVerticalBlockBorderWrapper"] small {
    color: #94a3b8 !important;
}

/* ── Summary KPI bar → dark slate bg ────────────────────────────────── */
div[data-testid="stHorizontalBlock"] [data-testid="stMetricValue"] {
    font-weight: 700;
}

/* ── Page background alignment ──────────────────────────────────────── */
section[data-testid="stMain"] {
    background-color: #0b1120 !important;
}
section[data-testid="stMain"] > div {
    background-color: #0b1120 !important;
}
header[data-testid="stHeader"] {
    background-color: #0b1120 !important;
}

/* ── Page-level text colors ─────────────────────────────────────────── */
section[data-testid="stMain"] h1,
section[data-testid="stMain"] h2,
section[data-testid="stMain"] h3 {
    color: #f1f5f9 !important;
}
section[data-testid="stMain"] p,
section[data-testid="stMain"] span,
section[data-testid="stMain"] label {
    color: #cbd5e1 !important;
}
section[data-testid="stMain"] hr {
    border-color: #1e293b !important;
}

/* ── Selectbox / dropdown dark styling ──────────────────────────────── */
section[data-testid="stMain"] [data-testid="stSelectbox"] label {
    color: #94a3b8 !important;
}

/* ── Button styling ─────────────────────────────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {
    background: linear-gradient(135deg, #334155, #1e293b) !important;
    color: #f1f5f9 !important;
    border: 1px solid #475569 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover {
    background: linear-gradient(135deg, #475569, #334155) !important;
    border-color: #64748b !important;
    box-shadow: 0 2px 12px rgba(100,116,139,.3) !important;
}

/* ── Summary-bar metrics (outside cards) → light ────────────────────── */
section[data-testid="stMain"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
}
section[data-testid="stMain"] [data-testid="stMetricValue"] > div {
    color: #f1f5f9 !important;
}
section[data-testid="stMain"] [data-testid="stMetricLabel"] p,
section[data-testid="stMain"] [data-testid="stMetricLabel"] div {
    color: #94a3b8 !important;
}
</style>
"""


# =========================================================================
# 1.  COLUMN DETECTION  (case-insensitive, first-match)
# =========================================================================

def detect_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first column name in *df* that matches any candidate
    (case-insensitive).  Returns None if nothing matches."""
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


# =========================================================================
# 2.  ENSURE Year / Month / Month_Num COLUMNS
# =========================================================================

MONTH_MAP = {
    # full names (lower)
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    # 3-letter abbreviations (lower)
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    # numeric strings
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12,
    # zero-padded
    "01": 1, "02": 2, "03": 3, "04": 4, "05": 5, "06": 6,
    "07": 7, "08": 8, "09": 9,
    # float strings that pandas sometimes produces
    "1.0": 1, "2.0": 2, "3.0": 3, "4.0": 4, "5.0": 5, "6.0": 6,
    "7.0": 7, "8.0": 8, "9.0": 9, "10.0": 10, "11.0": 11, "12.0": 12,
}


def _parse_month(val) -> Optional[int]:
    """Convert any reasonable month representation to 1-12 or None."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, (int, float)):
        v = int(val)
        return v if 1 <= v <= 12 else None
    s = str(val).strip().lower()
    return MONTH_MAP.get(s)


def ensure_year_month(df: pd.DataFrame) -> pd.DataFrame:
    """Guarantee that *df* has usable Year, Month_Num columns.
    Priority: existing Year / Month columns  →  Billing Date fallback.
    Operates on a copy; never mutates the caller's frame."""
    df = df.copy()

    year_col  = detect_column(df, ["Year"])
    month_col = detect_column(df, ["Month", "Month_Num"])
    bill_col  = detect_column(df, ["Billing Date"])

    has_year  = False
    has_month = False

    if year_col:
        df["Year"] = pd.to_numeric(df[year_col], errors="coerce")
        if df["Year"].notna().any():
            has_year = True

    if month_col:
        df["Month_Num"] = df[month_col].apply(_parse_month)
        if df["Month_Num"].notna().any():
            has_month = True

    if bill_col and (not has_year or not has_month):
        bd = pd.to_datetime(df[bill_col], errors="coerce")
        if not has_year:
            df["Year"] = bd.dt.year
        if not has_month:
            df["Month_Num"] = bd.dt.month

    if "Year" not in df.columns:
        df["Year"] = np.nan
    if "Month_Num" not in df.columns:
        df["Month_Num"] = np.nan

    return df


# =========================================================================
# 3.  DATA CLASS
# =========================================================================

@dataclass
class PropertyCard:
    name: str
    total_cost: float = 0.0
    avg_monthly: float = 0.0
    total_usage: float = 0.0
    yoy_change: Optional[float] = None
    status: str = "Inactive"
    last_billing: str = "N/A"
    value_history: List[float] = field(default_factory=list)
    sparkline_color: str = "#10b981"
    status_color: str = "#ef4444"


# =========================================================================
# 4.  BUILD PORTFOLIO  (one card per property)
# =========================================================================

def build_portfolio(df: pd.DataFrame) -> List[PropertyCard]:
    prop_col = detect_column(df, ["Property Name", "Property"])
    amt_col  = detect_column(df, ["$ Amount", "Amount", "Cost"])
    use_col  = detect_column(df, ["Usage"])
    bill_col = detect_column(df, ["Billing Date"])

    if not prop_col:
        return []

    now       = datetime.now()
    now_year  = now.year
    now_month = now.month

    cards: List[PropertyCard] = []

    for name, grp in df.groupby(prop_col):
        try:
            card = PropertyCard(name=str(name))

            if amt_col and amt_col in grp.columns:
                vals = pd.to_numeric(grp[amt_col], errors="coerce")
                card.total_cost = float(vals.sum())

            if use_col and use_col in grp.columns:
                vals = pd.to_numeric(grp[use_col], errors="coerce")
                card.total_usage = float(vals.sum())

            if amt_col and "Year" in grp.columns and "Month_Num" in grp.columns:
                tmp = grp.dropna(subset=["Year", "Month_Num"]).copy()
                if not tmp.empty:
                    tmp["_amt"] = pd.to_numeric(tmp[amt_col], errors="coerce")
                    monthly = (
                        tmp.groupby(["Year", "Month_Num"])["_amt"]
                        .sum()
                        .reset_index()
                        .sort_values(["Year", "Month_Num"])
                    )
                    card.value_history = monthly["_amt"].tolist()

            n_months = len(card.value_history) if card.value_history else 1
            card.avg_monthly = card.total_cost / max(n_months, 1)

            if amt_col and "Year" in grp.columns:
                yr_totals = (
                    grp.assign(_amt=pd.to_numeric(grp[amt_col], errors="coerce"))
                    .dropna(subset=["Year"])
                    .groupby("Year")["_amt"]
                    .sum()
                )
                sorted_years = yr_totals.sort_index()
                if len(sorted_years) >= 2:
                    prev = sorted_years.iloc[-2]
                    curr = sorted_years.iloc[-1]
                    if prev and prev != 0:
                        card.yoy_change = ((curr - prev) / abs(prev)) * 100

            if "Year" in grp.columns and "Month_Num" in grp.columns:
                tmp2 = grp.dropna(subset=["Year", "Month_Num"])
                if not tmp2.empty:
                    last_year_val  = tmp2["Year"].max()
                    last_month_val = tmp2["Month_Num"].max()
                    if not pd.isna(last_year_val) and not pd.isna(last_month_val):
                        ly = int(last_year_val)
                        lm = int(last_month_val)
                        months_since = (now_year - ly) * 12 + (now_month - lm)
                        if months_since <= 3:
                            card.status = "Active"

            if bill_col and bill_col in grp.columns:
                dates = pd.to_datetime(grp[bill_col], errors="coerce").dropna()
                if not dates.empty:
                    card.last_billing = dates.max().strftime("%b %d, %Y")

            if card.status == "Active":
                card.status_color   = "#10b981"
                card.sparkline_color = "#10b981"
            else:
                card.status_color   = "#ef4444"
                card.sparkline_color = "#f87171"

            if card.yoy_change is not None and card.yoy_change > 0:
                card.sparkline_color = "#f87171"

            cards.append(card)

        except Exception:
            continue

    cards.sort(key=lambda c: (0 if c.status == "Active" else 1, c.name))
    return cards


# =========================================================================
# 5.  SVG SPARKLINE  (base64-encoded <img> — Streamlit-safe)
# =========================================================================

def sparkline_img(data: List[float], color: str = "#10b981",
                  width: int = 200, height: int = 48) -> str:
    if not data or len(data) < 2:
        return ""

    mn, mx = min(data), max(data)
    rng = mx - mn if mx != mn else 1.0
    pad = 4

    n = len(data)
    pts: list[str] = []
    for i, v in enumerate(data):
        x = round(i * width / (n - 1), 1)
        y = round(pad + (1 - (v - mn) / rng) * (height - 2 * pad), 1)
        pts.append(f"{x},{y}")

    points_str = " ".join(pts)
    grad_id    = f"sg{abs(hash(tuple(data))) % 100000}"
    poly = f"0,{height} {points_str} {width},{height}"

    svg = (
        f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:{width}px;height:{height}px;">'
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity=".25"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<polygon points="{poly}" fill="url(#{grad_id})"/>'
        f'<polyline points="{points_str}" fill="none" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{pts[-1].split(",")[0]}" cy="{pts[-1].split(",")[1]}" '
        f'r="3" fill="{color}"/>'
        f'</svg>'
    )

    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64}" style="width:100%;max-width:{width}px;height:{height}px;" />'


# =========================================================================
# 6.  NUMBER FORMATTERS  (full amounts — NO "K" abbreviation)
# =========================================================================

def fmt_dollar(v: float) -> str:
    return f"${v:,.2f}"

def fmt_number(v: float) -> str:
    if v == int(v):
        return f"{int(v):,}"
    return f"{v:,.1f}"

def fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.1f}%"


# =========================================================================
# 7.  RENDER FUNCTIONS  (native Streamlit components — no complex HTML)
# =========================================================================

UTILITY_COLORS = {
    "Water":    "#38bdf8",   # sky-400
    "Electric": "#facc15",   # yellow-400
    "Gas":      "#fb923c",   # orange-400
    "Sewage":   "#a78bfa",   # violet-400
}


def render_summary_bar(df_full: pd.DataFrame, cards: List[PropertyCard]):
    """Top-level KPI bar: overall counts + per-utility breakdowns.

    Always receives the FULL (unfiltered) df so all four utilities
    show totals even when a single utility is selected in the dropdown.
    """

    util_col = detect_column(df_full, ["Utility"])
    amt_col  = detect_column(df_full, ["$ Amount", "Amount", "Cost"])
    use_col  = detect_column(df_full, ["Usage"])

    # ── Overall counts ──────────────────────────────────────────────────
    total_props  = len(cards)
    active_count = sum(1 for c in cards if c.status == "Active")

    ov1, ov2 = st.columns(2)
    ov1.metric("Properties", total_props)
    ov2.metric("Active", active_count)

    st.markdown("")

    # ── Per-utility KPI columns ─────────────────────────────────────────
    UTILITY_TYPES = ["Water", "Electric", "Gas", "Sewage"]
    cols = st.columns(len(UTILITY_TYPES))

    for col, utype in zip(cols, UTILITY_TYPES):
        with col:
            dot_color = UTILITY_COLORS.get(utype, "#94a3b8")
            st.markdown(
                f'<span style="display:inline-flex;align-items:center;gap:6px;">'
                f'<span style="width:10px;height:10px;border-radius:50%;'
                f'background:{dot_color};display:inline-block;"></span>'
                f'<span style="font-weight:700;font-size:1rem;color:#f1f5f9;">'
                f'{utype}</span></span>',
                unsafe_allow_html=True,
            )

            total_cost  = 0.0
            avg_monthly = 0.0
            total_usage = 0.0

            try:
                if util_col and amt_col:
                    udf = df_full[
                        df_full[util_col]
                        .str.strip()
                        .str.lower()
                        == utype.lower()
                    ]
                    if not udf.empty:
                        cost_vals = pd.to_numeric(udf[amt_col], errors="coerce")
                        total_cost = float(cost_vals.sum())

                        if use_col and use_col in udf.columns:
                            usage_vals = pd.to_numeric(udf[use_col], errors="coerce")
                            total_usage = float(usage_vals.sum())

                        if "Year" in udf.columns and "Month_Num" in udf.columns:
                            tmp = udf.dropna(subset=["Year", "Month_Num"])
                            n_months = len(
                                tmp.drop_duplicates(subset=["Year", "Month_Num"])
                            )
                            n_months = max(n_months, 1)
                        else:
                            n_months = max(len(udf), 1)
                        avg_monthly = total_cost / n_months
            except Exception:
                total_cost  = 0.0
                avg_monthly = 0.0
                total_usage = 0.0

            st.metric("Total Cost",  fmt_dollar(total_cost))
            st.metric("Avg Monthly", fmt_dollar(avg_monthly))
            st.metric("Total Usage", fmt_number(total_usage))


def render_property_card(card: PropertyCard):
    with st.container(border=True):

        hdr_left, hdr_right = st.columns([4, 1])
        with hdr_left:
            st.subheader(card.name)
        with hdr_right:
            badge_bg = card.status_color + "22"
            badge_html = (
                f'<div style="text-align:right;padding-top:8px;">'
                f'<span style="display:inline-flex;align-items:center;gap:6px;'
                f'padding:4px 14px;border-radius:999px;font-size:.82rem;'
                f'font-weight:600;background:{badge_bg};color:{card.status_color};">'
                f'<span style="width:8px;height:8px;border-radius:50%;'
                f'background:{card.status_color};display:inline-block;"></span>'
                f'{card.status}</span></div>'
            )
            st.markdown(badge_html, unsafe_allow_html=True)

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Total Cost", fmt_dollar(card.total_cost))
        with k2:
            st.metric("Avg Monthly", fmt_dollar(card.avg_monthly))
        with k3:
            st.metric("Total Usage", fmt_number(card.total_usage))
        with k4:
            if card.yoy_change is not None:
                arrow = "▲" if card.yoy_change > 0 else "▼"
                yoy_display = f"{arrow} {fmt_pct(card.yoy_change)}"
                st.metric("YoY Change", yoy_display)
            else:
                st.metric("YoY Change", "N/A")

        spark = sparkline_img(card.value_history, card.sparkline_color)
        if spark:
            st.caption("Monthly Cost Trend")
            st.markdown(spark, unsafe_allow_html=True)

        st.caption(f"Last Billed: {card.last_billing}")

        if st.button("View Full Details →", key=f"nav_{card.name}"):
            st.session_state["selected_property"] = card.name
            st.switch_page("pages/3_Property_Detail.py")


# =========================================================================
# 8.  MAIN
# =========================================================================

def main():
    st.set_page_config(page_title="Property Portfolio", layout="wide")

    st.markdown(DARK_CARD_CSS, unsafe_allow_html=True)

    st.markdown(
        "<h1 style='text-align:center;margin-bottom:.2rem;color:#f1f5f9;'>"
        "Property Portfolio</h1>"
        "<p style='text-align:center;color:#64748b;margin-top:0;'>"
        "Select a property to view its performance card.</p>",
        unsafe_allow_html=True,
    )

    df, last_updated = load_data()
    if df is None or df.empty:
        st.warning("No data available. Check the Google Sheet connection.")
        return

    df = ensure_year_month(df)

    prop_col = detect_column(df, ["Property Name", "Property"])
    util_col = detect_column(df, ["Utility"])

    if not prop_col:
        st.error("Cannot find a 'Property Name' column in the data.")
        return

    fcol1, fcol2 = st.columns(2)

    UTILITY_OPTIONS = ["Select All", "Water", "Electric", "Gas", "Sewage"]

    with fcol1:
        sel_utility = st.selectbox("Utility Type", UTILITY_OPTIONS, index=0)

    df_filtered = df.copy()
    if sel_utility != "Select All" and util_col:
        df_filtered = df_filtered[
            df_filtered[util_col].str.strip().str.lower()
            == sel_utility.strip().lower()
        ]

    properties = sorted(df_filtered[prop_col].dropna().unique().tolist())
    if not properties:
        with fcol2:
            st.selectbox("Select Property", ["No properties found"], disabled=True)
        st.info("No properties match the selected utility type.")
        return

    with fcol2:
        sel_property = st.selectbox("Select Property", properties, index=0)

    all_cards = build_portfolio(df_filtered)

    # ── SUMMARY BAR — always uses full df for per-utility totals ────────
    st.markdown("---")
    render_summary_bar(df, all_cards)
    st.markdown("---")

    selected_card = next((c for c in all_cards if c.name == sel_property), None)

    if selected_card:
        render_property_card(selected_card)
    else:
        st.warning(f"No data found for **{sel_property}**.")

    if last_updated:
        st.caption(f"Data last updated: {last_updated}")


# ── entry point ─────────────────────────────────────────────────────────
main()
