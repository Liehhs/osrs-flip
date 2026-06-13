import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pytz
from ge_api import fetch_latest, fetch_mapping, fetch_5m, compute_flips, WATCHLIST_NAMES

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OSRS Flip Dashboard",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Global font + base */
  html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }

  /* Sidebar */
  section[data-testid="stSidebar"] { background: #111827; }
  section[data-testid="stSidebar"] * { color: #e5e7eb !important; }
  section[data-testid="stSidebar"] .stNumberInput label,
  section[data-testid="stSidebar"] .stSelectbox label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: #9ca3af !important; }

  /* Metric cards */
  [data-testid="stMetric"] {
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 1rem 1.25rem;
  }
  [data-testid="stMetricLabel"] { font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.06em; color: #9ca3af !important; }
  [data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700; color: #f9fafb !important; }
  [data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

  /* Table styling */
  [data-testid="stDataFrame"] { border: 1px solid #374151; border-radius: 8px; overflow: hidden; }
  thead tr th { background: #1f2937 !important; color: #9ca3af !important; font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 0.06em; }
  tbody tr:nth-child(even) { background: #111827; }
  tbody tr:hover { background: #1e3a5f !important; }

  /* Section headers */
  .section-header {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #6b7280;
    margin: 1.5rem 0 0.5rem 0;
    border-bottom: 1px solid #1f2937;
    padding-bottom: 0.35rem;
  }

  /* Timing banner */
  .timing-green { background:#052e16; border:1px solid #166534; border-radius:8px; padding:0.6rem 1rem; color:#bbf7d0; font-size:0.85rem; }
  .timing-yellow { background:#1c1200; border:1px solid #854d0e; border-radius:8px; padding:0.6rem 1rem; color:#fef08a; font-size:0.85rem; }
  .timing-red { background:#1f0606; border:1px solid #991b1b; border-radius:8px; padding:0.6rem 1rem; color:#fecaca; font-size:0.85rem; }

  /* Refresh button */
  div[data-testid="stSidebar"] .stButton button {
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    width: 100%;
    padding: 0.65rem;
    margin-top: 0.5rem;
  }
  div[data-testid="stSidebar"] .stButton button:hover { background: #1d4ed8; }

  /* Hide default streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_gp(n):
    if n is None or (isinstance(n, float) and n != n):
        return "—"
    n = int(n)
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,}"

def get_timing():
    est = pytz.timezone("America/New_York")
    now = datetime.now(est)
    h = now.hour
    time_str = now.strftime("%I:%M %p ET")
    if 14 <= h < 22:
        return "green", f"🟢  Sell window — Peak US/EU overlap. Best time to exit positions. ({time_str})"
    elif 6 <= h < 14:
        return "yellow", f"🟡  Transition window — Moderate activity. Selective orders fine. ({time_str})"
    else:
        return "red", f"🔴  Buy window — Off-peak. Place buy offers now, sell into the afternoon. ({time_str})"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚔️ FlipOSRS")
    st.markdown("<div style='font-size:0.75rem;color:#6b7280;margin-bottom:1.5rem'>Live Grand Exchange Scanner</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Cash Stack</div>", unsafe_allow_html=True)
    cash_m = st.number_input(
        "Amount (millions of GP)",
        min_value=1.0, max_value=50000.0, value=100.0, step=0.5,
        help="Enter in millions. 100 = 100,000,000 GP. Supports decimals like 150.7."
    )
    cash_stack_gp = int(cash_m * 1_000_000)
    st.caption(f"= {cash_stack_gp:,} GP")

    st.markdown("<div class='section-header'>Bulk Flip Filters</div>", unsafe_allow_html=True)
    bulk_min_limit = st.number_input(
        "Min GE buy limit",
        min_value=100, max_value=50000, value=2000, step=100,
        help="Minimum 4-hour GE buy limit for an item to appear in the bulk table."
    )
    min_volume_5m = st.number_input(
        "Min trades in last 5 min",
        min_value=0, max_value=5000, value=5, step=1,
        help="Filters out illiquid items with near-zero real trading activity. Raise this to see only highly liquid items."
    )

    st.markdown("<div class='section-header'>Actions</div>", unsafe_allow_html=True)
    refresh = st.button("🔄  Update live data", use_container_width=True)

    st.markdown("---")
    st.markdown("<div style='font-size:0.7rem;color:#4b5563;line-height:1.6'>Data: OSRS Wiki Real-Time Prices API<br>Tax: 2% on seller (5M GP cap)<br>Volume: 5-min trade bucket × 12 = est. hourly<br>Cycle GP uses realistic fill cap, not raw limit</div>", unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────
col_title, col_ts = st.columns([3, 1])
with col_title:
    st.markdown("## OSRS Grand Exchange — Live Flip Dashboard")
with col_ts:
    if "updated" in st.session_state:
        st.markdown(f"<div style='text-align:right;color:#6b7280;font-size:0.78rem;padding-top:0.6rem'>Updated {st.session_state['updated']}</div>", unsafe_allow_html=True)

# Timing banner
tw_color, tw_msg = get_timing()
st.markdown(f"<div class='timing-{tw_color}'>{tw_msg}</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Data load ─────────────────────────────────────────────────────────────────
if refresh or "data" not in st.session_state:
    with st.spinner("Fetching live GE data…"):
        try:
            latest  = fetch_latest()
            mapping = fetch_mapping()
            fivemin = fetch_5m()
            bulk, singular, watch = compute_flips(
                latest, mapping, fivemin,
                cash_stack_gp, bulk_min_limit, min_volume_5m
            )
            st.session_state["data"]    = (bulk, singular, watch)
            st.session_state["updated"] = datetime.now().strftime("%b %d %Y, %I:%M %p")
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()
elif "data" in st.session_state:
    # Re-score with current sidebar values without hitting the API again
    try:
        if "raw" not in st.session_state:
            pass
        bulk, singular, watch = st.session_state["data"]
    except Exception:
        st.info("Click **Update live data** to load the market.")
        st.stop()

if "data" not in st.session_state:
    st.info("👆 Click **Update live data** in the sidebar to start.")
    st.stop()

bulk, singular, watch = st.session_state["data"]

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(
    "Best Bulk — Cycle GP",
    fmt_gp(bulk[0]["cycle_gp"]) if bulk else "—",
    bulk[0]["name"] if bulk else ""
)
k2.metric(
    "Best Bulk — ROI",
    f"{bulk[0]['roi']:.2f}%" if bulk else "—",
    f"{fmt_gp(bulk[0]['margin'])} spread" if bulk else ""
)
k3.metric(
    "Best Singular — Spread",
    fmt_gp(singular[0]["margin"]) if singular else "—",
    singular[0]["name"] if singular else ""
)
k4.metric(
    "Watchlist Found",
    str(len(watch)),
    f"of {len(WATCHLIST_NAMES)} tracked"
)
k5.metric(
    "Cash Stack",
    f"{cash_m:,.1f}M GP",
    f"{cash_stack_gp:,} GP"
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Bulk flips table ──────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Best bulk flips — ranked by realistic 4-hour cycle GP</div>", unsafe_allow_html=True)
st.caption("Cycle GP uses min(GE limit, affordable units, estimated hourly fills ÷ 2) so illiquid items can't rank above liquid ones.")

if bulk:
    df_bulk = pd.DataFrame([{
        "Item":         r["name"],
        "Buy (gp)":     r["buy"],
        "Sell (gp)":    r["sell"],
        "Spread (gp)":  r["margin"],
        "ROI %":        round(r["roi"], 2),
        "GE Limit":     r["limit"],
        "Trades/hr ≈":  r["vol_per_hour"],
        "Cycle GP ≈":   r["cycle_gp"],
        "Tax Cap":      "✓" if r["tax_cap"] else "",
    } for r in bulk])

    st.dataframe(
        df_bulk.style.format({
            "Buy (gp)":    "{:,.0f}",
            "Sell (gp)":   "{:,.0f}",
            "Spread (gp)": "{:,.0f}",
            "ROI %":       "{:.2f}",
            "GE Limit":    "{:,.0f}",
            "Trades/hr ≈": "{:,.0f}",
            "Cycle GP ≈":  "{:,.0f}",
        }).background_gradient(subset=["Cycle GP ≈"], cmap="Blues")
         .background_gradient(subset=["ROI %"], cmap="Greens"),
        use_container_width=True,
        hide_index=True,
    )

    fig_bulk = px.bar(
        df_bulk.head(10), x="Item", y="Cycle GP ≈",
        color="ROI %", color_continuous_scale="teal",
        title="Top 10 bulk items — estimated cycle GP",
        labels={"Cycle GP ≈": "Cycle GP (gp)"},
        template="plotly_dark",
    )
    fig_bulk.update_layout(
        plot_bgcolor="#111827", paper_bgcolor="#111827",
        font_color="#e5e7eb", title_font_size=13,
        coloraxis_colorbar=dict(title="ROI %", tickfont=dict(size=10)),
        xaxis_tickangle=-30, margin=dict(t=40, b=60),
    )
    fig_bulk.update_traces(marker_line_width=0)
    st.plotly_chart(fig_bulk, use_container_width=True)
else:
    st.info("No bulk items match the current filters. Try lowering Min trades in last 5 min.")

# ── Singular flips table ──────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Best singular flips — ranked by post-tax spread</div>", unsafe_allow_html=True)
st.caption("Low GE limit (≤15), price >500K GP. Slower tickets, fatter margins. Requires patience on fills.")

if singular:
    df_sing = pd.DataFrame([{
        "Item":         r["name"],
        "Buy (gp)":     r["buy"],
        "Sell (gp)":    r["sell"],
        "Spread (gp)":  r["margin"],
        "ROI %":        round(r["roi"], 2),
        "Limit":        r["limit"],
        "Trades/hr ≈":  r["vol_per_hour"],
        "Tax Cap":      "✓" if r["tax_cap"] else "",
    } for r in singular])

    st.dataframe(
        df_sing.style.format({
            "Buy (gp)":    "{:,.0f}",
            "Sell (gp)":   "{:,.0f}",
            "Spread (gp)": "{:,.0f}",
            "ROI %":       "{:.2f}",
            "Trades/hr ≈": "{:,.0f}",
        }).background_gradient(subset=["Spread (gp)"], cmap="Purples"),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No singular items found with current data.")

# ── Investment watchlist ───────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Investment watchlist — live snapshot</div>", unsafe_allow_html=True)
st.caption("Tracked items: Tumeken's Shadow, Twisted Bow, Torva, Bandos, Armadyl, Scythe, Soulreaper Axe.")

if watch:
    df_watch = pd.DataFrame([{
        "Item":         r["name"],
        "Price (gp)":   r["sell"],
        "Buy offer":    r["buy"],
        "Spread (gp)":  r["margin"],
        "ROI %":        round(r["roi"], 2),
        "GE Limit":     r["limit"],
        "Trades/hr ≈":  r["vol_per_hour"],
        "Tax Cap":      "✓" if r["tax_cap"] else "",
    } for r in watch])

    st.dataframe(
        df_watch.style.format({
            "Price (gp)":  "{:,.0f}",
            "Buy offer":   "{:,.0f}",
            "Spread (gp)": "{:,.0f}",
            "ROI %":       "{:.2f}",
            "Trades/hr ≈": "{:,.0f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Watchlist spread bar
    fig_watch = px.bar(
        df_watch, x="Item", y="Spread (gp)",
        color="ROI %", color_continuous_scale="oranges",
        title="Watchlist — post-tax spread",
        template="plotly_dark",
        labels={"Spread (gp)": "Spread (gp)"},
    )
    fig_watch.update_layout(
        plot_bgcolor="#111827", paper_bgcolor="#111827",
        font_color="#e5e7eb", title_font_size=13,
        xaxis_tickangle=-30, margin=dict(t=40, b=80),
    )
    fig_watch.update_traces(marker_line_width=0)
    st.plotly_chart(fig_watch, use_container_width=True)
else:
    st.info("No watchlist items were returned in this data pull.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='font-size:0.72rem;color:#4b5563;text-align:center'>"
    "Data sourced from the OSRS Wiki Real-Time Prices API · Tax: 2% (5M cap) · "
    "Trades/hr estimated from 5-min bucket × 12 · Fills not guaranteed"
    "</div>",
    unsafe_allow_html=True
)