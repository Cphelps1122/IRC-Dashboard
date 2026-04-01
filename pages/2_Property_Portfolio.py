import streamlit as st
import math

# ================================================================
# PAGE CONFIG — Must be the first Streamlit call
# ================================================================
st.set_page_config(
    page_title="Property Portfolio",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================================================================
# SAMPLE DATA — Replace this list with your Google Sheets pull.
# Each dict = one property card.  Field names are referenced in
# the card-builder below, so keep keys consistent if you rename.
# ================================================================
PORTFOLIO = [
    {
        "id": "prop-001",
        "name": "Lakewood Commons",
        "address": "1420 Lakewood Blvd, Melissa, TX 75454",
        "status": "Active",
        "revenue": 18400,
        "expenses": 6200,
        "occupancy": 96,
        "noi": 12200,
        "cap_rate": 7.2,
        "yoy_change": 4.8,
        "revenue_history": [14200,14800,15400,15200,16000,16500,17000,16800,17200,17800,18000,18400],
        "last_updated": "2026-03-31",
    },
    {
        "id": "prop-002",
        "name": "Ridgepoint Offices",
        "address": "820 Commerce Dr, McKinney, TX 75071",
        "status": "Active",
        "revenue": 32750,
        "expenses": 11400,
        "occupancy": 91,
        "noi": 21350,
        "cap_rate": 6.8,
        "yoy_change": 2.1,
        "revenue_history": [28000,29200,29800,30100,30500,31000,31200,31800,32000,32100,32500,32750],
        "last_updated": "2026-03-30",
    },
    {
        "id": "prop-003",
        "name": "Elm Street Retail Center",
        "address": "305 Elm St, Anna, TX 75409",
        "status": "Pending",
        "revenue": 9800,
        "expenses": 4100,
        "occupancy": 78,
        "noi": 5700,
        "cap_rate": 5.4,
        "yoy_change": -1.3,
        "revenue_history": [10500,10200,9800,10000,9600,9900,9700,9500,9800,9600,9700,9800],
        "last_updated": "2026-03-29",
    },
    {
        "id": "prop-004",
        "name": "Sunset Apartments",
        "address": "7700 Sunset Ridge Pkwy, Frisco, TX 75035",
        "status": "Active",
        "revenue": 54200,
        "expenses": 19800,
        "occupancy": 94,
        "noi": 34400,
        "cap_rate": 6.1,
        "yoy_change": 5.6,
        "revenue_history": [44000,45500,46200,47800,48500,49200,50000,51200,52000,52800,53400,54200],
        "last_updated": "2026-03-31",
    },
    {
        "id": "prop-005",
        "name": "Northgate Industrial",
        "address": "1100 Industrial Blvd, Princeton, TX 75407",
        "status": "Vacant",
        "revenue": 0,
        "expenses": 3200,
        "occupancy": 0,
        "noi": -3200,
        "cap_rate": 0,
        "yoy_change": -100,
        "revenue_history": [8200,7500,6800,5400,4000,2800,1500,800,0,0,0,0],
        "last_updated": "2026-03-28",
    },
    {
        "id": "prop-006",
        "name": "Heritage Plaza",
        "address": "490 Heritage Pkwy, Celina, TX 75009",
        "status": "Active",
        "revenue": 22100,
        "expenses": 7600,
        "occupancy": 88,
        "noi": 14500,
        "cap_rate": 7.9,
        "yoy_change": 3.4,
        "revenue_history": [18500,19000,19200,19800,20100,20400,20800,21000,21300,21500,21800,22100],
        "last_updated": "2026-03-31",
    },
]


# ================================================================
# GLOBAL CSS — Injected once.  Controls summary bar, cards,
# sparklines, badges, hover effects, and responsive grid.
# ================================================================
GLOBAL_CSS = """
<style>
/* --- Tighter top padding --- */
.block-container { padding-top: 1.5rem !important; }

/* --- Summary Bar --- */
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

/* --- Property Card --- */
.prop-card {
    background: #1e2130;
    border: 1px solid #2a2d3a;
    border-radius: 12px;
    padding: 22px 24px 18px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    position: relative;
    overflow: hidden;
    transition: all .25s ease;
}
.prop-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: #3d8bfd;
    transform: scaleX(0);
    transition: transform .3s ease;
}
.prop-card:hover {
    border-color: #3d8bfd;
    box-shadow: 0 4px 20px rgba(61,139,253,.15), 0 8px 32px rgba(0,0,0,.3);
    transform: translateY(-2px);
}
.prop-card:hover::before { transform: scaleX(1); }

.card-hdr {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}
.card-title {
    font-size: 1.02rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.3;
}
.card-addr {
    font-size: .77rem;
    color: #6b7280;
    margin-top: 2px;
}

/* --- Badges --- */
.badge {
    font-size: .67rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    padding: 4px 10px;
    border-radius: 20px;
    white-space: nowrap;
    flex-shrink: 0;
}
.badge-active  { background: rgba(52,211,153,.12); color: #34d399; }
.badge-pending { background: rgba(251,191,36,.12);  color: #fbbf24; }
.badge-vacant  { background: rgba(248,113,113,.12); color: #f87171; }

/* --- KPI Strip --- */
.kpi-strip {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    padding: 12px 0;
    border-top: 1px solid #2a2d3a;
    border-bottom: 1px solid #2a2d3a;
}
.kpi-label {
    font-size: .67rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #6b7280;
}
.kpi-val {
    font-size: 1.06rem;
    font-weight: 700;
    color: #e8eaed;
}
.kpi-val.pos { color: #34d399; }
.kpi-val.neg { color: #f87171; }

/* --- Sparkline row --- */
.spark-row {
    display: flex;
    align-items: center;
    gap: 12px;
}
.spark-lbl {
    font-size: .72rem;
    color: #6b7280;
    white-space: nowrap;
    flex-shrink: 0;
}
.spark-chart {
    flex: 1;
    height: 36px;
    min-width: 0;
}
.spark-chart svg { width: 100%; height: 100%; }

/* --- Card Footer --- */
.card-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 2px;
}
.card-updated {
    font-size: .72rem;
    color: #6b7280;
}

/* --- Streamlit nav buttons styled to match cards --- */
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: transparent;
    border: 1px solid #2a2d3a;
    color: #3d8bfd;
    font-size: .78rem;
    font-weight: 600;
    padding: 5px 16px;
    border-radius: 8px;
    transition: all .2s;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    border-color: #3d8bfd;
    background: rgba(61,139,253,.1);
}

@media (max-width: 540px) {
    .summary-bar { grid-template-columns: repeat(2, 1fr); }
}
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ================================================================
# SPARKLINE SVG GENERATOR
# Pass a list of numbers → get back an inline SVG string.
# Auto-colors green (uptrend) or red (downtrend).
# ================================================================
def make_sparkline(data: list, width: int = 200, height: int = 36) -> str:
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
    trend_clr = "#34d399" if data[-1] >= data[0] else "#f87171"
    last_x = width
    last_y = pad + uh - ((data[-1] - mn) / rng) * uh
    grad_id = f"sg{id(data) % 99999}"

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
        return f"${v/1000:.1f}K"
    return f"${v:,}"

def fmt_currency_full(v):
    return f"${v:,}"


# ================================================================
# COMPUTE AGGREGATE PORTFOLIO METRICS
# Revenue-weighted YoY.  Averages exclude vacant properties.
# ================================================================
def compute_metrics(data):
    total_rev = sum(p["revenue"] for p in data)
    total_exp = sum(p["expenses"] for p in data)
    total_noi = sum(p["noi"] for p in data)
    active    = sum(1 for p in data if p["status"] == "Active")
    occupied  = [p for p in data if p["occupancy"] > 0]
    avg_occ   = (sum(p["occupancy"] for p in occupied) / len(occupied)) if occupied else 0
    avg_cap   = (sum(p["cap_rate"] for p in occupied) / len(occupied)) if occupied else 0
    rev_props = [p for p in data if p["revenue"] > 0]
    weighted_yoy = (
        sum(p["yoy_change"] * p["revenue"] for p in rev_props)
        / sum(p["revenue"] for p in rev_props)
    ) if rev_props else 0

    return {
        "total_revenue": total_rev,
        "total_expenses": total_exp,
        "total_noi": total_noi,
        "count": len(data),
        "active": active,
        "avg_occ": f"{avg_occ:.1f}",
        "avg_cap": f"{avg_cap:.1f}",
        "yoy": f"{weighted_yoy:.1f}",
    }


# ================================================================
# RENDER: SUMMARY BAR
# ================================================================
m = compute_metrics(PORTFOLIO)
yoy_val = float(m["yoy"])
yoy_cls = "up" if yoy_val >= 0 else "down"
yoy_arrow = "▲" if yoy_val >= 0 else "▼"

summary_html = f"""
<div class="summary-bar">
    <div class="summary-metric">
        <span class="sum-label">Properties</span>
        <span class="sum-value">{m['count']}</span>
        <span class="sum-delta up">{m['active']} Active</span>
    </div>
    <div class="summary-metric">
        <span class="sum-label">Monthly Revenue</span>
        <span class="sum-value">{fmt_currency_full(m['total_revenue'])}</span>
        <span class="sum-delta {yoy_cls}">{yoy_arrow} {abs(yoy_val)}% YoY</span>
    </div>
    <div class="summary-metric">
        <span class="sum-label">Net Operating Income</span>
        <span class="sum-value">{fmt_currency_full(m['total_noi'])}</span>
    </div>
    <div class="summary-metric">
        <span class="sum-label">Avg Occupancy</span>
        <span class="sum-value">{m['avg_occ']}%</span>
    </div>
    <div class="summary-metric">
        <span class="sum-label">Avg Cap Rate</span>
        <span class="sum-value">{m['avg_cap']}%</span>
    </div>
    <div class="summary-metric">
        <span class="sum-label">Monthly Expenses</span>
        <span class="sum-value">{fmt_currency_full(m['total_expenses'])}</span>
    </div>
</div>
"""
st.markdown(summary_html, unsafe_allow_html=True)


# ================================================================
# RENDER: PROPERTY CARDS  (3 per row)
# Each card = custom HTML (sparkline + KPIs + badge) +
# a native st.button underneath for navigation.
# ================================================================
CARDS_PER_ROW = 3

for row_start in range(0, len(PORTFOLIO), CARDS_PER_ROW):
    row_props = PORTFOLIO[row_start : row_start + CARDS_PER_ROW]
    cols = st.columns(CARDS_PER_ROW)

    for col, prop in zip(cols, row_props):
        with col:
            status_lower = prop["status"].lower()
            badge_cls = (
                "badge-active" if status_lower == "active"
                else "badge-pending" if status_lower == "pending"
                else "badge-vacant"
            )
            noi_cls = "pos" if prop["noi"] >= 0 else "neg"
            yoy_sign = "+" if prop["yoy_change"] >= 0 else ""
            yoy_color = "#34d399" if prop["yoy_change"] >= 0 else "#f87171"
            spark_svg = make_sparkline(prop["revenue_history"])

            card_html = f"""
            <div class="prop-card">
                <div class="card-hdr">
                    <div>
                        <div class="card-title">{prop['name']}</div>
                        <div class="card-addr">{prop['address']}</div>
                    </div>
                    <span class="badge {badge_cls}">{prop['status']}</span>
                </div>
                <div class="kpi-strip">
                    <div>
                        <div class="kpi-label">Revenue</div>
                        <div class="kpi-val">{fmt_currency(prop['revenue'])}</div>
                    </div>
                    <div>
                        <div class="kpi-label">NOI</div>
                        <div class="kpi-val {noi_cls}">{fmt_currency(prop['noi'])}</div>
                    </div>
                    <div>
                        <div class="kpi-label">Occupancy</div>
                        <div class="kpi-val">{prop['occupancy']}%</div>
                    </div>
                </div>
                <div class="spark-row">
                    <span class="spark-lbl">12-mo trend</span>
                    <div class="spark-chart">{spark_svg}</div>
                    <span class="spark-lbl" style="color:{yoy_color}">{yoy_sign}{prop['yoy_change']}%</span>
                </div>
                <div class="card-foot">
                    <span class="card-updated">Updated {prop['last_updated']}</span>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            # --- Nav button: stores property ID and jumps to detail page ---
            if st.button(f"View Details →", key=f"nav_{prop['id']}"):
                st.session_state["selected_property_id"] = prop["id"]
                st.session_state["selected_property_name"] = prop["name"]
                st.switch_page("pages/3_Property_Detail.py")
