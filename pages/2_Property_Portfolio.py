"""
IRC-Dashboard  –  pages/2_Property_Portfolio.py
Property Portfolio: dropdown-driven single-card view with utility filter,
per-utility summary KPI bar, SVG chart with axes, and nav to detail page.

DARK-THEMED CARDS  –  CSS injection on native Streamlit components.
Safe imports only (streamlit, pandas, numpy, base64, dataclasses, typing, datetime).
NO matplotlib.
"""

import streamlit as st
import pandas as pd
import numpy as np
import base64
import math
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from utils.load_data import load_data

# =========================================================================
# 0.  DARK-CARD CSS
# =========================================================================

DARK_CARD_CSS = """
<style>
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
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricValue"] > div {
    color: #f1f5f9 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] p,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] label,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] div {
    color: #94a3b8 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stSubheader"],
div[data-testid="stVerticalBlockBorderWrapper"] h3,
div[data-testid="stVerticalBlockBorderWrapper"] h2 {
    color: #f1f5f9 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] .stCaption,
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"],
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p,
div[data-testid="stVerticalBlockBorderWrapper"] small {
    color: #94a3b8 !important;
}
div[data-testid="stHorizontalBlock"] [data-testid="stMetricValue"] {
    font-weight: 700;
}
section[data-testid="stMain"] {
    background-color: #0b1120 !important;
}
section[data-testid="stMain"] > div {
    background-color: #0b1120 !important;
}
header[data-testid="stHeader"] {
    background-color: #0b1120 !important;
}
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
section[data-testid="stMain"] [data-testid="stSelectbox"] label {
    color: #94a3b8 !important;
}
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
# 0b.  UTILITY UNIT-OF-MEASURE MAP
# =========================================================================

UTILITY_UOM = {
    "water":    "Gal",
    "electric": "kWh",
    "gas":      "Therms",
    "trash":    "",
}


def _uom_for_utilities(utility_series: pd.Series) -> str:
    if utility_series is None or utility_series.empty:
        return ""
    unique = utility_series.str.strip().str.lower().dropna().unique()
    if len(unique) == 1:
        return UTILITY_UOM.get(unique[0], "")
    return ""


# =========================================================================
# 1.  COLUMN DETECTION
# =========================================================================

def detect_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


# =========================================================================
# 2.  ENSURE Year / Month_Num COLUMNS
# =========================================================================

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12,
    "01": 1, "02": 2, "03": 3, "04": 4, "05": 5, "06": 6,
    "07": 7, "08": 8, "09": 9,
    "1.0": 1, "2.0": 2, "3.0": 3, "4.0": 4, "5.0": 5, "6.0": 6,
    "7.0": 7, "8.0": 8, "9.0": 9, "10.0": 10, "11.0": 11, "12.0": 12,
}


def _parse_month(val) -> Optional[int]:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, (int, float)):
        v = int(val)
        return v if 1 <= v <= 12 else None
    s = str(val).strip().lower()
    return MONTH_MAP.get(s)


def ensure_year_month(df: pd.DataFrame) -> pd.DataFrame:
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
    mom_change: Optional[float] = None        # month-over-month percent
    status: str = "Inactive"
    last_billing: str = "N/A"
    value_history: List[float] = field(default_factory=list)
    month_labels: List[int] = field(default_factory=list)
    sparkline_color: str = "#10b981"
    status_color: str = "#ef4444"
    uom: str = ""


# =========================================================================
# 4.  BUILD PORTFOLIO
# =========================================================================

def build_portfolio(df: pd.DataFrame) -> List[PropertyCard]:
    prop_col = detect_column(df, ["Property Name", "Property"])
    amt_col  = detect_column(df, ["$ Amount", "Amount", "Cost"])
    use_col  = detect_column(df, ["Usage"])
    bill_col = detect_column(df, ["Billing Date"])
    util_col = detect_column(df, ["Utility"])

    if not prop_col:
        return []

    now       = datetime.now()
    now_year  = now.year
    now_month = now.month
    cards: List[PropertyCard] = []

    for name, grp in df.groupby(prop_col):
        try:
            card = PropertyCard(name=str(name))

            if util_col and util_col in grp.columns:
                card.uom = _uom_for_utilities(grp[util_col])

            if amt_col and amt_col in grp.columns:
                vals = pd.to_numeric(grp[amt_col], errors="coerce")
                card.total_cost = float(vals.sum())

            if use_col and use_col in grp.columns:
                vals = pd.to_numeric(grp[use_col], errors="coerce")
                card.total_usage = float(vals.sum())

            # ── Monthly cost history (for chart + avg + MoM) ────────────
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
                    card.month_labels  = monthly["Month_Num"].astype(int).tolist()

                    # ── Month-over-Month change ─────────────────────────
                    if len(card.value_history) >= 2:
                        prev_val = card.value_history[-2]
                        curr_val = card.value_history[-1]
                        if prev_val and prev_val != 0:
                            card.mom_change = ((curr_val - prev_val) / abs(prev_val)) * 100

            n_months = len(card.value_history) if card.value_history else 1
            card.avg_monthly = card.total_cost / max(n_months, 1)

            # ── Status (active if billed within last 3 months) ──────────
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

            if card.mom_change is not None and card.mom_change > 0:
                card.sparkline_color = "#f87171"

            cards.append(card)
        except Exception:
            continue

    cards.sort(key=lambda c: (0 if c.status == "Active" else 1, c.name))
    return cards


# =========================================================================
# 5.  SVG CHART WITH AXES  (base64 <img> — Streamlit-safe)
# =========================================================================

MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]


def _nice_ticks(max_val: float, num_ticks: int = 5) -> List[float]:
    """Generate clean round Y-axis tick values from 0 to max_val."""
    if max_val <= 0:
        return [0]
    raw_step = max_val / num_ticks
    magnitude = 10 ** math.floor(math.log10(raw_step)) if raw_step > 0 else 1
    nice_steps = [1, 2, 2.5, 5, 10]
    step = magnitude
    for ns in nice_steps:
        candidate = ns * magnitude
        if candidate >= raw_step:
            step = candidate
            break
    ticks = []
    val = 0.0
    while val <= max_val * 1.05:
        ticks.append(val)
        val += step
        if len(ticks) > 20:
            break
    if not ticks or ticks[-1] < max_val:
        ticks.append(val)
    return ticks


def _fmt_axis_dollar(v: float) -> str:
    """Short dollar format for axis labels."""
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    if v == 0:
        return "$0"
    return f"${v:,.0f}"


def chart_img(data: List[float], months: List[int],
              color: str = "#10b981") -> str:
    """Full SVG chart with Y-axis (cost from $0) and X-axis (Jan-Dec).
    Returns a base64-encoded <img> tag."""

    if not data or len(data) < 1:
        return ""

    # ── Chart dimensions ────────────────────────────────────────────────
    total_w   = 560
    total_h   = 200
    margin_l  = 60       # left margin for Y-axis labels
    margin_r  = 15
    margin_t  = 15
    margin_b  = 30       # bottom margin for X-axis labels
    chart_w   = total_w - margin_l - margin_r
    chart_h   = total_h - margin_t - margin_b

    # ── Y-axis scale (always starts at 0) ───────────────────────────────
    max_val = max(data) if data else 0
    if max_val <= 0:
        max_val = 100
    y_ticks = _nice_ticks(max_val)
    y_max   = y_ticks[-1] if y_ticks else max_val

    def to_y(v: float) -> float:
        return margin_t + chart_h - (v / y_max * chart_h) if y_max > 0 else margin_t + chart_h

    # ── X positions: one slot per month (Jan=1 .. Dec=12) ───────────────
    # Build a dict of month_num → cost for the data we have
    month_cost = {}
    for m, v in zip(months, data):
        month_cost[m] = month_cost.get(m, 0) + v

    # X positions for all 12 months
    def to_x(month_num: int) -> float:
        return margin_l + (month_num - 1) / 11 * chart_w

    # ── Build SVG ───────────────────────────────────────────────────────
    parts: list[str] = []
    parts.append(
        f'<svg viewBox="0 0 {total_w} {total_h}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;max-width:{total_w}px;height:{total_h}px;'
        f'font-family:sans-serif;">'
    )

    # ── Gradient definition ─────────────────────────────────────────────
    grad_id = f"cg{abs(hash(tuple(data))) % 100000}"
    parts.append(
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity=".20"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
    )

    # ── Y-axis gridlines + labels ───────────────────────────────────────
    for tick in y_ticks:
        y = round(to_y(tick), 1)
        # gridline
        parts.append(
            f'<line x1="{margin_l}" y1="{y}" x2="{total_w - margin_r}" y2="{y}" '
            f'stroke="#334155" stroke-width="0.5" stroke-dasharray="3,3"/>'
        )
        # label
        parts.append(
            f'<text x="{margin_l - 6}" y="{y + 4}" '
            f'text-anchor="end" fill="#94a3b8" font-size="10">'
            f'{_fmt_axis_dollar(tick)}</text>'
        )

    # ── X-axis labels (all 12 months) ───────────────────────────────────
    for m in range(1, 13):
        x = round(to_x(m), 1)
        parts.append(
            f'<text x="{x}" y="{total_h - 6}" '
            f'text-anchor="middle" fill="#94a3b8" font-size="10">'
            f'{MONTH_ABBR[m - 1]}</text>'
        )

    # ── Plot line + fill (only months that have data) ───────────────────
    plot_months = sorted(month_cost.keys())
    if plot_months:
        pts_xy: list[tuple[float, float]] = []
        for m in plot_months:
            x = round(to_x(m), 1)
            y = round(to_y(month_cost[m]), 1)
            pts_xy.append((x, y))

        pts_str = " ".join(f"{x},{y}" for x, y in pts_xy)

        # filled area polygon
        bottom_y = round(to_y(0), 1)
        poly_pts = (
            f"{pts_xy[0][0]},{bottom_y} "
            + pts_str
            + f" {pts_xy[-1][0]},{bottom_y}"
        )
        parts.append(f'<polygon points="{poly_pts}" fill="url(#{grad_id})"/>')

        # line
        parts.append(
            f'<polyline points="{pts_str}" fill="none" stroke="{color}" '
            f'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
        )

        # dots at each data point
        for x, y in pts_xy:
            parts.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{color}"/>')

    # ── Axis lines ──────────────────────────────────────────────────────
    axis_y_bottom = round(to_y(0), 1)
    # bottom axis
    parts.append(
        f'<line x1="{margin_l}" y1="{axis_y_bottom}" '
        f'x2="{total_w - margin_r}" y2="{axis_y_bottom}" '
        f'stroke="#475569" stroke-width="1"/>'
    )
    # left axis
    parts.append(
        f'<line x1="{margin_l}" y1="{margin_t}" '
        f'x2="{margin_l}" y2="{axis_y_bottom}" '
        f'stroke="#475569" stroke-width="1"/>'
    )

    parts.append('</svg>')
    svg = "".join(parts)

    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return (
        f'<img src="data:image/svg+xml;base64,{b64}" '
        f'style="width:100%;max-width:{total_w}px;height:{total_h}px;" />'
    )


# =========================================================================
# 6.  NUMBER FORMATTERS
# =========================================================================

def fmt_dollar(v: float) -> str:
    return f"${v:,.2f}"

def fmt_number(v: float) -> str:
    if v == int(v):
        return f"{int(v):,}"
    return f"{v:,.1f}"

def fmt_usage(v: float, uom: str = "") -> str:
    num = fmt_number(v)
    if uom:
        return f"{num} {uom}"
    return num

def fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.1f}%"


# =========================================================================
# 7.  RENDER FUNCTIONS
# =========================================================================

UTILITY_COLORS = {
    "Water":    "#38bdf8",
    "Electric": "#facc15",
    "Gas":      "#fb923c",
    "Trash":    "#a78bfa",
}


def render_summary_bar(df_filtered: pd.DataFrame, cards: List[PropertyCard]):
    util_col = detect_column(df_filtered, ["Utility"])
    amt_col  = detect_column(df_filtered, ["$ Amount", "Amount", "Cost"])
    use_col  = detect_column(df_filtered, ["Usage"])

    total_props  = len(cards)
    active_count = sum(1 for c in cards if c.status == "Active")

    ov1, ov2 = st.columns(2)
    ov1.metric("Properties", total_props)
    ov2.metric("Active", active_count)

    st.markdown("")

    UTILITY_TYPES = ["Water", "Electric", "Gas", "Trash"]
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
                    udf = df_filtered[
                        df_filtered[util_col]
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

            uom = UTILITY_UOM.get(utype.lower(), "")
            st.metric("Total Cost",  fmt_dollar(total_cost))
            st.metric("Avg Monthly", fmt_dollar(avg_monthly))
            st.metric("Total Usage", fmt_usage(total_usage, uom))


def render_property_card(card: PropertyCard, selected_utility: str = "Select All"):
    with st.container(border=True):

        hdr_left, hdr_right = st.columns([4, 1])
        with hdr_left:
            st.subheader(card.name)

            if selected_utility and selected_utility != "Select All":
                badge_color = UTILITY_COLORS.get(selected_utility, "#94a3b8")
                badge_bg    = badge_color + "22"
                utility_badge = (
                    f'<span style="display:inline-flex;align-items:center;gap:5px;'
                    f'padding:3px 12px;border-radius:999px;font-size:.78rem;'
                    f'font-weight:600;background:{badge_bg};color:{badge_color};'
                    f'margin-top:-8px;">'
                    f'<span style="width:7px;height:7px;border-radius:50%;'
                    f'background:{badge_color};display:inline-block;"></span>'
                    f'{selected_utility}</span>'
                )
                st.markdown(utility_badge, unsafe_allow_html=True)

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

        # ── KPI row ────────────────────────────────────────────────────
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.metric("Total Cost", fmt_dollar(card.total_cost))
        with k2:
            st.metric("Avg Monthly", fmt_dollar(card.avg_monthly))
        with k3:
            st.metric("Total Usage", fmt_usage(card.total_usage, card.uom))
        with k4:
            if card.mom_change is not None:
                arrow = "▲" if card.mom_change > 0 else "▼"
                mom_display = f"{arrow} {fmt_pct(card.mom_change)}"
                st.metric("MoM Change", mom_display)
            else:
                st.metric("MoM Change", "N/A")

        # ── Chart with axes ────────────────────────────────────────────
        chart = chart_img(card.value_history, card.month_labels, card.sparkline_color)
        if chart:
            st.caption("Monthly Cost Trend")
            st.markdown(chart, unsafe_allow_html=True)

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

    UTILITY_OPTIONS = ["Select All", "Water", "Electric", "Gas", "Trash"]

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

    st.markdown("---")
    render_summary_bar(df, all_cards)
    st.markdown("---")

    selected_card = next((c for c in all_cards if c.name == sel_property), None)

    if selected_card:
        render_property_card(selected_card, sel_utility)
    else:
        st.warning(f"No data found for **{sel_property}**.")

    if last_updated:
        st.caption(f"Data last updated: {last_updated}")


main()
