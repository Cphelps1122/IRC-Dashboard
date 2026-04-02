import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io, base64, calendar
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from utils.load_data import load_data

# ─── Page config (must be first Streamlit command) ────────
st.set_page_config(page_title="Property Portfolio", layout="wide")


# ═══════════════════════════════════════════════════════════
#  COLUMN DETECTION
# ═══════════════════════════════════════════════════════════

def detect_column(df: pd.DataFrame, candidates: list) -> Optional[str]:
    """Return the first column name from *candidates* that exists in df."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


# ═══════════════════════════════════════════════════════════
#  ENSURE YEAR / MONTH / MONTH_NUM
#  ─ Uses the sheet's own Month & Year columns first.
#  ─ Falls back to Billing Date ONLY if those are missing
#    or mostly empty.
# ═══════════════════════════════════════════════════════════

MONTH_MAP: dict = {}
for _i in range(1, 13):
    MONTH_MAP[calendar.month_name[_i].lower()]  = _i   # january → 1
    MONTH_MAP[calendar.month_abbr[_i].lower()]  = _i   # jan → 1
    MONTH_MAP[str(_i)]                          = _i   # "1"  → 1
    MONTH_MAP[str(_i).zfill(2)]                 = _i   # "01" → 1


def _parse_month_num(val):
    """Convert a single Month cell → int 1-12  or  NaN."""
    if pd.isna(val):
        return np.nan
    s = str(val).strip().lower()
    if s in MONTH_MAP:
        return MONTH_MAP[s]
    try:
        n = int(float(s))
        if 1 <= n <= 12:
            return n
    except (ValueError, TypeError):
        pass
    return np.nan


def ensure_year_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Guarantee *Year* (numeric), *Month* (str name), and *Month_Num*
    (int 1-12) columns exist in df.

    Priority order:
      1. Sheet's own Year / Month columns  (Christopher's preference)
      2. Billing Date  (fallback only if #1 missing or >50 % NaN)
    """
    df = df.copy()

    has_year  = "Year"  in df.columns
    has_month = "Month" in df.columns
    has_bd    = "Billing Date" in df.columns

    # ── Year ──────────────────────────────────────────────
    if has_year:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        if df["Year"].isna().mean() > 0.5 and has_bd:
            df["Year"] = pd.to_datetime(
                df["Billing Date"], errors="coerce"
            ).dt.year
    elif has_bd:
        df["Year"] = pd.to_datetime(
            df["Billing Date"], errors="coerce"
        ).dt.year
    else:
        df["Year"] = np.nan

    # ── Month_Num ─────────────────────────────────────────
    if has_month:
        df["Month_Num"] = df["Month"].apply(_parse_month_num)
        if df["Month_Num"].isna().mean() > 0.5 and has_bd:
            df["Month_Num"] = pd.to_datetime(
                df["Billing Date"], errors="coerce"
            ).dt.month
    elif has_bd:
        df["Month_Num"] = pd.to_datetime(
            df["Billing Date"], errors="coerce"
        ).dt.month
    else:
        df["Month_Num"] = np.nan

    # ── Month (name string) ──────────────────────────────
    if "Month" not in df.columns or df["Month"].isna().all():
        df["Month"] = df["Month_Num"].apply(
            lambda x: calendar.month_name[int(x)]
            if pd.notna(x) and 1 <= int(x) <= 12
            else np.nan
        )

    # ── Final coerce ──────────────────────────────────────
    df["Year"]      = pd.to_numeric(df["Year"],      errors="coerce")
    df["Month_Num"] = pd.to_numeric(df["Month_Num"], errors="coerce")

    return df


# ═══════════════════════════════════════════════════════════
#  DATA CLASS
# ═══════════════════════════════════════════════════════════

@dataclass
class PropertyCard:
    name:          str
    total_cost:    float            = 0.0
    avg_monthly:   float            = 0.0
    total_usage:   float            = 0.0
    yoy_change:    Optional[float]  = None
    status:        str              = "Inactive"
    value_history: list             = field(default_factory=list)
    last_billing:  str              = "N/A"


# ═══════════════════════════════════════════════════════════
#  BUILD PORTFOLIO
# ═══════════════════════════════════════════════════════════

def build_portfolio(df: pd.DataFrame) -> List[PropertyCard]:
    """
    Build one PropertyCard per unique property in *df*.
    Expects ensure_year_month() to have already run.
    """
    prop_col = detect_column(df, [
        "Property Name", "Property", "Account", "Location",
        "Site", "Address", "Building", "Facility", "Name",
    ])
    if prop_col is None or df.empty:
        return []

    amt_col   = "$ Amount" if "$ Amount" in df.columns else None
    usage_col = "Usage"    if "Usage"    in df.columns else None

    now           = datetime.now()
    current_year  = now.year
    current_month = now.month

    cards: List[PropertyCard] = []

    for name, grp in df.groupby(prop_col):
        if pd.isna(name) or str(name).strip() == "":
            continue

        card = PropertyCard(name=str(name).strip())

        # Keep only rows where Year & Month_Num are usable
        valid = grp.dropna(subset=["Year", "Month_Num"]).copy()

        # ── Total cost ────────────────────────────────────
        if amt_col and amt_col in valid.columns and not valid.empty:
            card.total_cost = valid[amt_col].sum()
            n_months = valid.drop_duplicates(
                subset=["Year", "Month_Num"]
            ).shape[0]
            card.avg_monthly = (
                card.total_cost / n_months if n_months > 0 else 0.0
            )

        # ── Total usage ───────────────────────────────────
        if usage_col and usage_col in valid.columns and not valid.empty:
            card.total_usage = valid[usage_col].sum()

        # ── YoY change (current-yr vs prior-yr) ──────────
        if amt_col and not valid.empty:
            years = sorted(valid["Year"].dropna().unique())
            if len(years) >= 2:
                max_yr  = int(years[-1])
                prev_yr = int(years[-2])
                curr_sum = valid.loc[valid["Year"] == max_yr, amt_col].sum()
                prev_sum = valid.loc[valid["Year"] == prev_yr, amt_col].sum()
                if prev_sum > 0:
                    card.yoy_change = (
                        (curr_sum - prev_sum) / prev_sum
                    ) * 100

        # ── Status ────────────────────────────────────────
        if not valid.empty:
            try:
                last_year  = int(valid["Year"].max())
                last_month = int(
                    valid.loc[valid["Year"] == last_year, "Month_Num"].max()
                )
                months_since = (
                    (current_year - last_year) * 12
                    + (current_month - last_month)
                )
                if months_since <= 3:
                    card.status = "Active"
                elif months_since <= 6:
                    card.status = "Pending"
                else:
                    card.status = "Inactive"

                card.last_billing = (
                    f"{calendar.month_abbr[last_month]} {last_year}"
                )
            except (ValueError, TypeError):
                card.status = "Inactive"
        else:
            # Last-resort: try Billing Date for status
            if "Billing Date" in grp.columns:
                bd = pd.to_datetime(
                    grp["Billing Date"], errors="coerce"
                ).dropna()
                if not bd.empty:
                    last_bd = bd.max()
                    ms = (
                        (current_year - last_bd.year) * 12
                        + (current_month - last_bd.month)
                    )
                    if ms <= 3:
                        card.status = "Active"
                    elif ms <= 6:
                        card.status = "Pending"
                    card.last_billing = last_bd.strftime("%b %Y")

        # ── Sparkline data (up to last 12 months) ────────
        if amt_col and not valid.empty:
            spark = (
                valid
                .groupby(["Year", "Month_Num"])[amt_col]
                .sum()
                .reset_index()
                .sort_values(["Year", "Month_Num"])
            )
            card.value_history = spark[amt_col].tolist()[-12:]
        elif amt_col and amt_col in grp.columns:
            card.value_history = (
                grp[amt_col].dropna().tolist()[-12:]
            )

        cards.append(card)

    # Sort: Active → Pending → Inactive, then alphabetical
    order = {"Active": 0, "Pending": 1, "Inactive": 2}
    cards.sort(key=lambda c: (order.get(c.status, 3), c.name))

    return cards


# ═══════════════════════════════════════════════════════════
#  SPARKLINE GENERATOR  (Agg backend + RGBA tuples)
# ═══════════════════════════════════════════════════════════

def generate_sparkline(data: list) -> str:
    """Return a base64-encoded PNG sparkline."""
    if not data or len(data) < 2:
        return ""

    fig, ax = plt.subplots(figsize=(2.2, 0.6))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor((0, 0, 0, 0))

    x = list(range(len(data)))
    line_c = (0.08, 0.42, 0.85, 1.0)     # solid blue
    fill_c = (0.08, 0.42, 0.85, 0.12)    # translucent blue

    ax.plot(x, data, color=line_c, linewidth=1.5)
    ax.fill_between(x, data, min(data), color=fill_c)

    ax.axis("off")
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(
        buf, format="png", dpi=120,
        transparent=True, bbox_inches="tight", pad_inches=0,
    )
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ═══════════════════════════════════════════════════════════
#  FORMAT HELPERS  (full numbers — NO "K" abbreviation)
# ═══════════════════════════════════════════════════════════

def fmt_dollar(val: float) -> str:
    return f"${val:,.2f}"

def fmt_number(val: float) -> str:
    if val == int(val):
        return f"{int(val):,}"
    return f"{val:,.2f}"

def fmt_pct(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"


# ═══════════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════════

CARD_CSS = """
<style>
/* ── Summary bar ── */
.summary-bar {
    display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;
}
.summary-item {
    flex: 1; min-width: 160px; background: #0E1117;
    border: 1px solid #1E2A3A; border-radius: 10px;
    padding: 1rem 1.2rem; text-align: center;
}
.summary-label {
    font-size: 0.75rem; color: #8899AA;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.summary-value {
    font-size: 1.35rem; font-weight: 700;
    color: #FFFFFF; margin-top: 4px;
}

/* ── Property card ── */
.prop-card {
    background: linear-gradient(135deg, #0E1117 0%, #131A24 100%);
    border: 1px solid #1E2A3A; border-radius: 14px;
    padding: 1.8rem 2rem; margin-top: 0.5rem;
}
.card-header {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 1.2rem;
}
.card-title {
    font-size: 1.3rem; font-weight: 700; color: #FFFFFF;
}

.badge {
    font-size: 0.7rem; font-weight: 600;
    padding: 4px 12px; border-radius: 20px;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.badge-active {
    background: rgba(0,210,120,0.15); color: #00D278;
    border: 1px solid rgba(0,210,120,0.30);
}
.badge-pending {
    background: rgba(255,180,0,0.15); color: #FFB400;
    border: 1px solid rgba(255,180,0,0.30);
}
.badge-inactive {
    background: rgba(255,60,60,0.12); color: #FF5252;
    border: 1px solid rgba(255,60,60,0.25);
}

.card-metrics {
    display: flex; gap: 1.5rem; flex-wrap: wrap;
    margin-bottom: 1rem;
}
.metric-block { flex: 1; min-width: 130px; }
.metric-label {
    font-size: 0.72rem; color: #8899AA;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.metric-value {
    font-size: 1.15rem; font-weight: 700;
    color: #FFFFFF; margin-top: 2px;
}

.yoy-up   { color: #FF5252; }
.yoy-down { color: #00D278; }
.yoy-na   { color: #8899AA; }

.spark-row   { margin-top: 0.5rem; }
.spark-label {
    font-size: 0.72rem; color: #8899AA;
    text-transform: uppercase; letter-spacing: 0.5px;
    margin-bottom: 4px;
}

.last-billing {
    font-size: 0.72rem; color: #556677;
    margin-top: 0.8rem; text-align: right;
}
</style>
"""


# ═══════════════════════════════════════════════════════════
#  RENDER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def render_summary_bar(cards: List[PropertyCard]):
    total_cost   = sum(c.total_cost  for c in cards)
    total_usage  = sum(c.total_usage for c in cards)
    active_count = sum(1 for c in cards if c.status == "Active")
    total_props  = len(cards)

    html = f"""
    <div class="summary-bar">
        <div class="summary-item">
            <div class="summary-label">Total Properties</div>
            <div class="summary-value">{total_props}</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">Active</div>
            <div class="summary-value">{active_count}</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">Portfolio Cost</div>
            <div class="summary-value">{fmt_dollar(total_cost)}</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">Total Usage</div>
            <div class="summary-value">{fmt_number(total_usage)}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_property_card(card: PropertyCard):
    badge_cls = {
        "Active":   "badge-active",
        "Pending":  "badge-pending",
        "Inactive": "badge-inactive",
    }.get(card.status, "badge-inactive")

    yoy_cls = "yoy-na"
    yoy_str = fmt_pct(card.yoy_change)
    if card.yoy_change is not None:
        yoy_cls = "yoy-up" if card.yoy_change > 0 else "yoy-down"

    sparkline_html = ""
    if card.value_history and len(card.value_history) >= 2:
        src = generate_sparkline(card.value_history)
        if src:
            n = len(card.value_history)
            sparkline_html = f"""
            <div class="spark-row">
                <div class="spark-label">Monthly Trend (last {n} mo)</div>
                <img src="data:image/png;base64,{src}"
                     style="width:100%;max-width:320px;height:auto;" />
            </div>
            """

    html = f"""
    <div class="prop-card">
        <div class="card-header">
            <div class="card-title">{card.name}</div>
            <span class="badge {badge_cls}">{card.status}</span>
        </div>
        <div class="card-metrics">
            <div class="metric-block">
                <div class="metric-label">Total Cost</div>
                <div class="metric-value">{fmt_dollar(card.total_cost)}</div>
            </div>
            <div class="metric-block">
                <div class="metric-label">Avg Monthly</div>
                <div class="metric-value">{fmt_dollar(card.avg_monthly)}</div>
            </div>
            <div class="metric-block">
                <div class="metric-label">Total Usage</div>
                <div class="metric-value">{fmt_number(card.total_usage)}</div>
            </div>
            <div class="metric-block">
                <div class="metric-label">YoY Change</div>
                <div class="metric-value {yoy_cls}">{yoy_str}</div>
            </div>
        </div>
        {sparkline_html}
        <div class="last-billing">Last billing: {card.last_billing}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════

st.markdown(CARD_CSS, unsafe_allow_html=True)
st.title("Property Portfolio")

# ── Load data ─────────────────────────────────────────────
df, last_updated = load_data()

if df.empty:
    st.warning("No data returned from Google Sheets.")
    st.stop()

st.caption(f"Last updated: {last_updated}")

# ── Ensure Year / Month / Month_Num exist ─────────────────
df = ensure_year_month(df)

# ── Detect key columns ────────────────────────────────────
PROP_COL = detect_column(df, [
    "Property Name", "Property", "Account", "Location",
    "Site", "Address", "Building", "Facility", "Name",
])
UTIL_COL = detect_column(df, [
    "Utility", "Utility Type", "Service", "Type", "Service Type",
])

if PROP_COL is None:
    st.error(
        "Cannot find a property-name column in the data. "
        "Expected one of: Property Name, Property, Account, Location, etc."
    )
    st.stop()

# ── Utility filter ────────────────────────────────────────
utility_options = ["Select All"]
if UTIL_COL:
    utility_options += sorted(
        df[UTIL_COL].dropna().astype(str).unique().tolist()
    )

col1, col2 = st.columns(2)
with col1:
    selected_utility = st.selectbox("Utility Type", utility_options)

# ── Apply utility filter ──────────────────────────────────
df_filtered = df.copy()
if UTIL_COL and selected_utility != "Select All":
    df_filtered = df_filtered[
        df_filtered[UTIL_COL].astype(str) == selected_utility
    ]

# ── Property filter (repopulates on utility change) ──────
prop_names = sorted(
    df_filtered[PROP_COL].dropna().astype(str).unique().tolist()
)

with col2:
    if prop_names:
        selected_property = st.selectbox("Property", prop_names)
    else:
        st.selectbox("Property", ["No properties found"])
        selected_property = None

# ── Build portfolio cards ─────────────────────────────────
PORTFOLIO = build_portfolio(df_filtered)

if not PORTFOLIO:
    st.warning(
        "No portfolio data could be built from the current filters. "
        "Check that your Google Sheet has valid Year/Month "
        "or Billing Date values."
    )
    st.stop()

# ── Summary bar (reflects current utility filter) ────────
render_summary_bar(PORTFOLIO)

# ── Render the selected property card ─────────────────────
selected_card = next(
    (c for c in PORTFOLIO if c.name == selected_property), None
)

if selected_card:
    render_property_card(selected_card)
    st.markdown("")
    if st.button("View Full Details →"):
        st.switch_page("pages/3_Property_Detail.py")
else:
    st.info("Select a property from the dropdown above to view its card.")
