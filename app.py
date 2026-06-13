import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
from ge_api import fetch_latest, fetch_mapping, fetch_5m, compute_flips, WATCHLIST_NAMES

st.set_page_config(
    page_title="OSRS Flip Dashboard",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }

  section[data-testid="stSidebar"] { background: #0f172a; }
  section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
  section[data-testid="stSidebar"] label {
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #94a3b8 !important;
  }

  [data-testid="stMetric"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 1rem 1.25rem;
  }
  [data-testid="stMetricLabel"] { font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 0.06em; color: #94a3b8 !important; }
  [data-testid="stMetricValue"] { font-size: 1.45rem !important; font-weight: 700; color: #f1f5f9 !important; }
  [data-testid="stMetricDelta"]  { font-size: 0.78rem !important; }

  .section-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #475569;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 0.3rem;
    margin: 1.6rem 0 0.5rem 0;
  }
  .note { font-size: 0.75rem; color: #64748b; margin-bottom: 0.75rem; }

  .timing-green  { background:#052e16; border:1px solid #166534; border-radius:8px; padding:0.6rem 1rem; color:#bbf7d0; font-size:0.85rem; }
  .timing-yellow { background:#1c1700; border:1px solid #92400e; border-radius:8px; padding:0.6rem 1rem; color:#fde68a; font-size:0.85rem; }
  .timing-red    { background:#1f0606; border:1px solid #991b1b; border-radius:8px; padding:0.6rem 1rem; color:#fecaca; font-size:0.85rem; }

  div[data-testid="stSidebar"] .stButton button {
    background: #2563eb; color: white; border: none;
    border-radius: 8px; font-weight: 600;
    width: 100%; padding: 0.65rem; margin-top: 0.75rem;
  }
  div[data-testid="stSidebar"] .stButton button:hover { background: #1d4ed8; }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


def fmt_gp(n):
    if n is None: return "—"
    n = int(n)
    if n >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:     return f"{n/1_000_000:.2f}M"
    if n >= 1_000:         return f"{n/1_000:.1f}K"
    return f"{n:,}"


def get_timing():
    est = pytz.timezone("America/New_York")
    now = datetime.now(est)
    h   = now.hour
    ts  = now.strftime("%I:%M %p ET")
    if 14 <= h < 22:
        return "green",  f"🟢  Sell window — Peak US/EU overlap. Best time to exit positions. ({ts})"
    elif 6 <= h < 14:
        return "yellow", f"🟡  Transition window — Moderate activity. Selective orders fine. ({ts})"
    else:
        return "red",    f"🔴  Buy window — Off-peak. Place buy offers now, sell into the afternoon. ({ts})"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚔️ FlipOSRS")
    st.markdown("<div style='font-size:0.74rem;color:#475569;margin-bottom:1.5rem'>Live Grand Exchange Scanner</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-label'>Cash Stack</div>", unsafe_allow_html=True)
    cash_m = st.number_input(
        "Amount in millions of GP",
        min_value=1.0, max_value=100000.0, value=100.0, step=0.5,
        help="Enter in millions. 100 = 100,000,000 GP. Decimals OK (e.g. 150.7 = 150.7M)"
    )
    cash_stack_gp = int(cash_m * 1_000_000)
    st.caption(f"= {cash_stack_gp:,} GP")

    st.markdown("<div class='section-label'>Actions</div>", unsafe_allow_html=True)
    refresh = st.button("🔄  Update live data", use_container_width=True)

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.68rem;color:#334155;line-height:1.7'>"
        "Source: OSRS Wiki Real-Time Prices API<br>"
        "Tax: 2% on seller (5M GP hard cap)<br>"
        "Bulk = GE limit ≥1,000 + ≥500 trades/hr<br>"
        "Trades/hr = 5-min bucket × 12<br>"
        "Cycle GP capped by realistic fills, not raw limit"
        "</div>",
        unsafe_allow_html=True
    )


# ── Header ────────────────────────────────────────────────────────────────────
col_h, col_ts = st.columns([3, 1])
with col_h:
    st.markdown("## OSRS Grand Exchange — Live Flip Dashboard")
with col_ts:
    if "updated" in st.session_state:
        st.markdown(
            f"<div style='text-align:right;color:#475569;font-size:0.75rem;padding-top:0.7rem'>"
            f"Updated {st.session_state['updated']}</div>",
            unsafe_allow_html=True
        )

tw_color, tw_msg = get_timing()
st.markdown(f"<div class='timing-{tw_color}'>{tw_msg}</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)


# ── Data fetch ────────────────────────────────────────────────────────────────
if refresh or "data" not in st.session_state:
    with st.spinner("Fetching live GE data…"):
        try:
            latest  = fetch_latest()
            mapping = fetch_mapping()
            fivemin = fetch_5m()
            result  = compute_flips(latest, mapping, fivemin, cash_stack_gp)
            st.session_state["data"]    = result
            st.session_state["updated"] = datetime.now().strftime("%b %d %Y, %I:%M %p")
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

if "data" not in st.session_state:
    st.info("👆 Click **Update live data** in the sidebar to start.")
    st.stop()

bulk, singular, watch = st.session_state["data"]


# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Best Bulk — Cycle GP",   fmt_gp(bulk[0]["cycle_gp"]) if bulk else "—",      bulk[0]["name"] if bulk else "")
k2.metric("Best Bulk — ROI",        f"{bulk[0]['roi']:.2f}%" if bulk else "—",          f"{fmt_gp(bulk[0]['margin'])} spread" if bulk else "")
k3.metric("Best Singular — Spread", fmt_gp(singular[0]["margin"]) if singular else "—", singular[0]["name"] if singular else "")
k4.metric("Watchlist Items Found",  str(len(watch)),                                     f"of {len(WATCHLIST_NAMES)} tracked")
k5.metric("Cash Stack",             f"{cash_m:,.1f}M GP",                                f"{cash_stack_gp:,} GP")

st.markdown("<br>", unsafe_allow_html=True)


# ── Bulk flips ────────────────────────────────────────────────────────────────
st.markdown("<div class='section-label'>Recommended bulk flips — herbs, pots, runes, supplies</div>", unsafe_allow_html=True)
st.markdown("<div class='note'>GE limit ≥1,000 · ≥500 trades/hr · ranked by realistic cycle GP using your cash stack</div>", unsafe_allow_html=True)

if bulk:
    df_bulk = pd.DataFrame([{
        "Item":        r["name"],
        "Buy":         r["buy"],
        "Sell":        r["sell"],
        "Spread":      r["margin"],
        "ROI %":       round(r["roi"], 2),
        "GE Limit":    r["limit"],
        "Trades / hr": r["vol_per_hour"],
        "Cycle GP":    r["cycle_gp"],
    } for r in bulk])

    st.dataframe(
        df_bulk.style
            .format({"Buy": "{:,.0f}", "Sell": "{:,.0f}", "Spread": "{:,.0f}",
                     "ROI %": "{:.2f}", "GE Limit": "{:,.0f}",
                     "Trades / hr": "{:,.0f}", "Cycle GP": "{:,.0f}"})
            .background_gradient(subset=["Cycle GP"], cmap="Blues")
            .background_gradient(subset=["ROI %"], cmap="Greens"),
        use_container_width=True,
        hide_index=True,
    )

    fig = px.bar(
        df_bulk.head(12), x="Item", y="Cycle GP",
        color="ROI %", color_continuous_scale="teal",
        title="Top 12 bulk flips — estimated cycle GP",
        template="plotly_dark",
    )
    fig.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font_color="#cbd5e1", title_font_size=13,
        xaxis_tickangle=-35, margin=dict(t=45, b=70),
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No bulk items found. The 5-min data may be sparse — try refreshing again in a moment.")


# ── Singular flips ────────────────────────────────────────────────────────────
st.markdown("<div class='section-label'>Best singular flips — low limit, high spread</div>", unsafe_allow_html=True)
st.markdown("<div class='note'>GE limit ≤15 · price >500K GP · ranked by post-tax spread · slower fills, fatter margins</div>", unsafe_allow_html=True)

if singular:
    df_sing = pd.DataFrame([{
        "Item":        r["name"],
        "Buy":         r["buy"],
        "Sell":        r["sell"],
        "Spread":      r["margin"],
        "ROI %":       round(r["roi"], 2),
        "Limit":       r["limit"],
        "Trades / hr": r["vol_per_hour"],
        "Tax Cap":     "✓" if r["tax_cap"] else "",
    } for r in singular])

    st.dataframe(
        df_sing.style
            .format({"Buy": "{:,.0f}", "Sell": "{:,.0f}", "Spread": "{:,.0f}",
                     "ROI %": "{:.2f}", "Trades / hr": "{:,.0f}"})
            .background_gradient(subset=["Spread"], cmap="Purples"),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No singular items found in this data pull.")


# ── Watchlist ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-label'>Investment watchlist — live snapshot</div>", unsafe_allow_html=True)
st.markdown("<div class='note'>Tumeken's Shadow · Twisted Bow · Torva · Bandos · Armadyl · Scythe · Soulreaper Axe</div>", unsafe_allow_html=True)

if watch:
    df_watch = pd.DataFrame([{
        "Item":        r["name"],
        "Price":       r["sell"],
        "Buy offer":   r["buy"],
        "Spread":      r["margin"],
        "ROI %":       round(r["roi"], 2),
        "GE Limit":    r["limit"],
        "Trades / hr": r["vol_per_hour"],
        "Tax Cap":     "✓" if r["tax_cap"] else "",
    } for r in watch])

    st.dataframe(
        df_watch.style
            .format({"Price": "{:,.0f}", "Buy offer": "{:,.0f}", "Spread": "{:,.0f}",
                     "ROI %": "{:.2f}", "Trades / hr": "{:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )

    fig_w = px.bar(
        df_watch, x="Item", y="Spread",
        color="ROI %", color_continuous_scale="oranges",
        title="Watchlist — post-tax spread per item",
        template="plotly_dark",
    )
    fig_w.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font_color="#cbd5e1", title_font_size=13,
        xaxis_tickangle=-30, margin=dict(t=45, b=80),
    )
    fig_w.update_traces(marker_line_width=0)
    st.plotly_chart(fig_w, use_container_width=True)
else:
    st.info("No watchlist items returned in this pull.")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='font-size:0.7rem;color:#334155;text-align:center'>"
    "OSRS Wiki Real-Time Prices API · 2% GE tax (5M cap) · "
    "Trades/hr = 5-min bucket × 12 · Fills not guaranteed"
    "</div>",
    unsafe_allow_html=True
)