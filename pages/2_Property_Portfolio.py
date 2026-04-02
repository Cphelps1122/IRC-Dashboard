"""
IRC-Dashboard  –  pages/2_Property_Portfolio.py
Property Portfolio: dropdown-driven single-card view with utility filter,
summary KPI bar, SVG sparkline (base64-encoded), and nav to detail page.

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
    # already numeric
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

    # ── Year ────────────────────────────────────────────────────────────
    if year_col:
        df["Year"] = pd.to_numeric(df[year_col], errors="coerce")
        if df["Year"].notna().any():
            has_year = True

    # ── Month_Num ───────────────────────────────────────────────────────
    if month_col:
        df["Month_Num"] = df[month_col].apply(_parse_month)
        if df["Month_Num"].notna().any():
            has_month = True

    # ── Billing Date fallback ───────────────────────────────────────────
    if bill_col and (not has_year or not has_month):
        bd = pd.to_datetime(df[bill_col], errors="coerce")
        if not has_year:
            df["Year"] = bd.dt.year
        if not has_month:
            df["Month_Num"] = bd.dt.month

    # Final safety: ensure columns exist even if all NaN
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
    yoy_change: Optional[float] = None        # percent
    status: str = "Inactive"                   # Active / Inactive
    last_billing: str = "N/A"
    value_history: List[float] = field(default_factory=list)
    sparkline_color: str = "#10b981"           # green
    status_color: str = "#ef4444"              # red


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

            # ── Total cost ──────────────────────────────────────────────
            if amt_col and amt_col in grp.columns:
                vals = pd.to_numeric(grp[amt_col], errors="coerce")
                card.total_cost = float(vals.sum())

            # ── Total usage ─────────────────────────────────────────────
            if use_col and use_col in grp.columns:
                vals = pd.to_numeric(grp[use_col], errors="coerce")
                card.total_usage = float(vals.sum())

            # ── Monthly cost history (for sparkline + avg) ──────────────
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

            # ── Avg monthly ─────────────────────────────────────────────
            n_months = len(card.value_history) if card.value_history else 1
            card.avg_monthly = card.total_cost / max(n_months, 1)

            # ── YoY change ──────────────────────────────────────────────
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

            # ── Last billing date ───────────────────────────────────────
            if bill_col and bill_col in grp.columns:
                dates = pd.to_datetime(grp[bill_col], errors="coerce").dropna()
                if not dates.empty:
                    card.last_billing = dates.max().strftime("%b %d, %Y")

            # ── Colors ──────────────────────────────────────────────────
            if card.status == "Active":
                card.status_color   = "#10b981"
                card.sparkline_color = "#10b981"
            else:
                card.status_color   = "#ef4444"
                card.sparkline_color = "#f87171"

            if card.yoy_change is not None and card.yoy_change > 0:
                card.sparkline_color = "#f87171"   # red = costs up

            cards.append(card)

        except Exception:
            # never let one bad property crash the whole page
            continue

    # sort: Active first, then alphabetical
    cards.sort(key=lambda c: (0 if c.status == "Active" else 1, c.name))
    return cards


# =========================================================================
# 5.  SVG SPARKLINE  (base64-encoded <img> — Streamlit-safe)
# =========================================================================

def sparkline_img(data: List[float], color: str = "#10b981",
                  width: int = 200, height: int = 48) -> str:
    """Return an <img> tag containing a base64-encoded SVG sparkline."""
    if not data or len(data) < 2:
        return ""

    mn, mx = min(data), max(data)
    rng = mx - mn if mx != mn else 1.0
    pad = 4  # top/bottom padding in SVG units

    n = len(data)
    pts: list[str] = []
    for i, v in enumerate(data):
        x = round(i * width / (n - 1), 1)
        y = round(pad + (1 - (v - mn) / rng) * (height - 2 * pad), 1)
        pts.append(f"{x},{y}")

    points_str = " ".join(pts)
    grad_id    = f"sg{abs(hash(tuple(data))) % 100000}"

    # polygon = filled area under the curve
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

def render_summary_bar(cards: List[PropertyCard]):
    """Top-level KPI bar aggregated across the visible card list."""
    total_props  = len(cards)
    active_count = sum(1 for c in cards if c.status == "Active")
    total_cost   = sum(c.total_cost for c in cards)
    avg_monthly  = np.mean([c.avg_monthly for c in cards]) if cards else 0
    total_usage  = sum(c.total_usage for c in cards)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Properties", total_props)
    c2.metric("Active", active_count)
    c3.metric("Total Cost", fmt_dollar(total_cost))
    c4.metric("Avg Monthly", fmt_dollar(avg_monthly))
    c5.metric("Total Usage", fmt_number(total_usage))


def render_property_card(card: PropertyCard):
    """Single property card using native Streamlit components."""

    # ── outer container ─────────────────────────────────────────────────
    with st.container(border=True):

        # ── Header row: property name + status badge ────────────────────
        hdr_left, hdr_right = st.columns([4, 1])
        with hdr_left:
            st.subheader(card.name)
        with hdr_right:
            badge_bg = card.status_color + "22"   # ~13 % opacity
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
            st.metric("Total Usage", fmt_number(card.total_usage))
        with k4:
            if card.yoy_change is not None:
                arrow = "▲" if card.yoy_change > 0 else "▼"
                yoy_display = f"{arrow} {fmt_pct(card.yoy_change)}"
                st.metric("YoY Change", yoy_display)
            else:
                st.metric("YoY Change", "N/A")

        # ── Sparkline ──────────────────────────────────────────────────
        spark = sparkline_img(card.value_history, card.sparkline_color)
        if spark:
            st.caption("Monthly Cost Trend")
            st.markdown(spark, unsafe_allow_html=True)

        # ── Footer ─────────────────────────────────────────────────────
        st.caption(f"Last Billed: {card.last_billing}")


# =========================================================================
# 8.  MAIN
# =========================================================================

def main():
    st.set_page_config(page_title="Property Portfolio", layout="wide")

    st.markdown(
        "<h1 style='text-align:center;margin-bottom:.2rem;'>Property Portfolio</h1>"
        "<p style='text-align:center;color:#64748b;margin-top:0;'>"
        "Select a property to view its performance card.</p>",
        unsafe_allow_html=True,
    )

    # ── load data ───────────────────────────────────────────────────────
    df, last_updated = load_data()
    if df is None or df.empty:
        st.warning("No data available. Check the Google Sheet connection.")
        return

    # guarantee Year / Month_Num exist
    df = ensure_year_month(df)

    # ── column references ───────────────────────────────────────────────
    prop_col = detect_column(df, ["Property Name", "Property"])
    util_col = detect_column(df, ["Utility"])

    if not prop_col:
        st.error("Cannot find a 'Property Name' column in the data.")
        return

    # ── FILTERS  (side by side) ─────────────────────────────────────────
    fcol1, fcol2 = st.columns(2)

    # ── Utility Type dropdown (hardcoded options) ───────────────────────
    UTILITY_OPTIONS = ["Select All", "Water", "Electric", "Gas", "Sewage"]

    with fcol1:
        sel_utility = st.selectbox("Utility Type", UTILITY_OPTIONS, index=0)

    # apply utility filter (case-insensitive)
    df_filtered = df.copy()
    if sel_utility != "Select All" and util_col:
        df_filtered = df_filtered[
            df_filtered[util_col].str.strip().str.lower()
            == sel_utility.strip().lower()
        ]

    # Property dropdown (repopulates based on utility filter)
    properties = sorted(df_filtered[prop_col].dropna().unique().tolist())
    if not properties:
        with fcol2:
            st.selectbox("Select Property", ["No properties found"], disabled=True)
        st.info("No properties match the selected utility type.")
        return

    with fcol2:
        sel_property = st.selectbox("Select Property", properties, index=0)

    # ── BUILD CARDS  (all properties in filtered set, for summary bar) ──
    all_cards = build_portfolio(df_filtered)

    # ── SUMMARY BAR ─────────────────────────────────────────────────────
    st.markdown("---")
    render_summary_bar(all_cards)
    st.markdown("---")

    # ── SINGLE CARD for selected property ───────────────────────────────
    selected_card = next((c for c in all_cards if c.name == sel_property), None)

    if selected_card:
        render_property_card(selected_card)

        # Nav button
        st.markdown("<div style='text-align:center;margin-top:6px;'>", unsafe_allow_html=True)
        if st.button("View Full Details →", key="nav_detail"):
            st.session_state["selected_property"] = selected_card.name
            st.switch_page("pages/3_Property_Detail.py")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning(f"No data found for **{sel_property}**.")

    # ── footer ──────────────────────────────────────────────────────────
    if last_updated:
        st.caption(f"Data last updated: {last_updated}")


# ── entry point ─────────────────────────────────────────────────────────
main()
