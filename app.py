import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pytz
from ge_api import (
    fetch_latest, fetch_mapping, fetch_5m, fetch_timeseries,
    compute_flips, WATCHLIST_NAMES
)

st.set_page_config(
    page_title="OSRS GE Flip Dashboard",
    layout="wide",
    page_icon="⚔️",
    initial_sidebar_state="collapsed",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Top nav tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #0f172a;
    border-bottom: 1px solid #1e293b;
    padding: 0 1rem;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    font-size: 0.82rem;
    font-weight: 500;
    padding: 0.75rem 1.25rem;
    border-bottom: 2px solid transparent;
    border-radius: 0;
  }
  .stTabs [aria-selected="true"] {
    color: #f1f5f9 !important;
    border-bottom: 2px solid #3b82f6 !important;
    background: transparent !important;
  }
  .stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem; }

  /* Metrics */
  [data-testid="stMetric"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.85rem 1rem;
  }
  [data-testid="stMetricLabel"] { font-size: 0.65rem !important; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b !important; }
  [data-testid="stMetricValue"] { font-size: 1.35rem !important; font-weight: 700; color: #f1f5f9 !important; }
  [data-testid="stMetricDelta"]  { font-size: 0.72rem !important; }

  /* Table */
  [data-testid="stDataFrame"] { border: 1px solid #1e293b; border-radius: 8px; }
  [data-testid="stDataFrame"] th { background: #0f172a !important; color: #94a3b8 !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.05em; }
  [data-testid="stDataFrame"] td { font-size: 0.82rem !important; }

  /* Timing banners */
  .banner-green  { background:#052e16; border:1px solid #166534; border-radius:6px; padding:0.5rem 1rem; color:#bbf7d0; font-size:0.82rem; margin-bottom:1rem; }
  .banner-yellow { background:#1c1700; border:1px solid #92400e; border-radius:6px; padding:0.5rem 1rem; color:#fde68a; font-size:0.82rem; margin-bottom:1rem; }
  .banner-red    { background:#1f0606; border:1px solid #991b1b; border-radius:6px; padding:0.5rem 1rem; color:#fecaca; font-size:0.82rem; margin-bottom:1rem; }

  .section-label {
    font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em;
    color: #475569; border-bottom: 1px solid #1e293b;
    padding-bottom: 0.25rem; margin: 1.25rem 0 0.4rem 0;
  }
  .note { font-size: 0.73rem; color: #64748b; margin-bottom: 0.6rem; }
  .tag-ideal    { color: #4ade80; font-weight:600; }
  .tag-demand   { color: #fb923c; font-weight:600; }
  .tag-flood    { color: #f87171; font-weight:600; }
  .tag-nodata   { color: #94a3b8; }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 0.75rem; padding-bottom: 2rem; max-width: 100% !important; }

  button[kind="primary"] { background: #2563eb !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_gp(n):
    if n is None: return "—"
    n = int(n)
    if abs(n) >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:     return f"{n/1_000_000:.2f}M"
    if abs(n) >= 1_000:         return f"{n/1_000:.1f}K"
    return f"{n:,}"

def get_timing():
    est = pytz.timezone("America/New_York")
    now = datetime.now(est)
    h, ts = now.hour, now.strftime("%I:%M %p ET")
    if 14 <= h < 22:
        return "green",  f"🟢  Peak sell window — US/EU overlap active. Exit positions now. ({ts})"
    elif 6 <= h < 14:
        return "yellow", f"🟡  Transition window — Moderate activity. Good for placing buy orders. ({ts})"
    else:
        return "red",    f"🔴  Buy window — Off-peak, bot activity high. Place buys now, sell at peak. ({ts})"

def ratio_tag(r):
    if r is None:              return "— no data"
    if 0.8 <= r <= 1.5:       return f"✅ {r:.2f}"
    elif 1.5 < r <= 3.0:      return f"🔼 {r:.2f}"
    elif r > 3.0:              return f"🔴 {r:.2f}"
    elif 0.4 <= r < 0.8:      return f"🟡 {r:.2f}"
    else:                      return f"🔴 {r:.2f}"

def fq_tag(label):
    return {"Ideal":"✅ Ideal","High demand":"🔼 High demand","Hard to buy":"🔴 Hard to buy",
            "Slight flood":"🟡 Slight flood","Flooded":"🔴 Flooded","No data":"— No data"}.get(label, label)

NUM_FMT = {
    "Buy Price":         "{:,.0f}",
    "Sell Price":        "{:,.0f}",
    "Tax (gp)":          "{:,.0f}",
    "Profit / unit":     "{:,.0f}",
    "ROI %":             "{:.2f}",
    "Buy Qty / hr":      "{:,.0f}",
    "Sell Qty / hr":     "{:,.0f}",
    "Daily Volume":      "{:,.0f}",
    "GE Limit":          "{:,.0f}",
    "Potential Profit":  "{:,.0f}",
    "Adj. Potential":    "{:,.0f}",
    "Realistic 4hr":     "{:,.0f}",
}

def to_df(rows, cols):
    col_map = {
        "name":             "Item",
        "buy_price":        "Buy Price",
        "sell_price":       "Sell Price",
        "tax":              "Tax (gp)",
        "profit_unit":      "Profit / unit",
        "roi":              "ROI %",
        "buy_qty_hr":       "Buy Qty / hr",
        "sell_qty_hr":      "Sell Qty / hr",
        "daily_volume":     "Daily Volume",
        "ratio":            "B/S Ratio",
        "fq_label":         "Fill Quality",
        "ge_limit":         "GE Limit",
        "potential_profit": "Potential Profit",
        "adj_potential":    "Adj. Potential",
        "realistic_profit": "Realistic 4hr",
    }
    out = []
    for r in rows:
        row = {}
        for key in cols:
            label = col_map.get(key, key)
            val   = r.get(key)
            if key == "ratio":    val = ratio_tag(val)
            elif key == "fq_label": val = fq_tag(val)
            elif key == "roi":    val = round(val, 2) if val else 0
            row[label] = val
        out.append(row)
    df = pd.DataFrame(out)
    fmt = {col_map[k]: v for k, v in NUM_FMT.items() if col_map.get(k) in df.columns}
    return df, fmt

DARK = dict(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
            title_font_size=13, margin=dict(t=45, b=70))

# ── Data fetch (cached in session) ───────────────────────────────────────────
def needs_refresh():
    if "data" not in st.session_state:
        return True
    d = st.session_state["data"]
    # invalidate if old key schema
    try:
        if d[0] and "adj_potential" not in d[0][0]:
            return True
    except Exception:
        return True
    return False

def do_fetch():
    with st.spinner("Fetching live GE data from OSRS Wiki API…"):
        try:
            latest  = fetch_latest()
            mapping = fetch_mapping()
            fivemin = fetch_5m()
            result  = compute_flips(latest, mapping, fivemin)
            st.session_state["data"]    = result
            st.session_state["updated"] = datetime.now().strftime("%b %d %Y, %I:%M:%S %p")
            return True
        except Exception as e:
            st.error(f"API error: {e}")
            return False

# ── Top bar ───────────────────────────────────────────────────────────────────
hcol1, hcol2, hcol3 = st.columns([4, 2, 1])
with hcol1:
    st.markdown("## ⚔️ OSRS GE Flip Dashboard")
with hcol2:
    if "updated" in st.session_state:
        st.markdown(
            f"<div style='color:#475569;font-size:0.72rem;padding-top:0.9rem'>"
            f"Last updated: {st.session_state['updated']}</div>",
            unsafe_allow_html=True
        )
with hcol3:
    refresh_btn = st.button("🔄 Refresh", type="primary", use_container_width=True)

if refresh_btn or needs_refresh():
    if not do_fetch():
        st.stop()

if "data" not in st.session_state:
    st.stop()

bulk, singular, high_roi, watch, all_rows = st.session_state["data"]

tw_color, tw_msg = get_timing()
st.markdown(f"<div class='banner-{tw_color}'>{tw_msg}</div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_bulk, tab_singular, tab_roi, tab_watch, tab_guide = st.tabs([
    "📦  Bulk Flips",
    "💎  Singular / High Margin",
    "📈  High ROI",
    "🔭  Investment Watchlist",
    "📖  Guide",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BULK FLIPS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_bulk:
    st.markdown("<div class='section-label'>Key metrics — bulk flips</div>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Best Adj. Potential",    fmt_gp(bulk[0].get("adj_potential")) if bulk else "—",  bulk[0].get("name","") if bulk else "")
    k2.metric("Best Profit / unit",     fmt_gp(bulk[0].get("profit_unit"))   if bulk else "—",  f"{bulk[0].get('roi',0):.1f}% ROI" if bulk else "")
    k3.metric("Best Potential Profit",  fmt_gp(bulk[0].get("potential_profit")) if bulk else "—", "Full GE limit × profit/unit")
    k4.metric("Items in bulk list",     str(len(bulk)),                                           "GE limit ≥1,000 · ≥200 trades/hr")

    st.markdown("<br>", unsafe_allow_html=True)

    # Sort control
    sc1, sc2 = st.columns([2, 1])
    with sc1:
        sort_by = st.selectbox(
            "Sort by",
            ["Adj. Potential", "Potential Profit", "Profit / unit", "ROI %", "Daily Volume"],
            index=0, key="bulk_sort"
        )
    with sc2:
        show_n = st.selectbox("Show top", [10, 20, 30, 40], index=1, key="bulk_n")

    sort_key_map = {
        "Adj. Potential":   "adj_potential",
        "Potential Profit": "potential_profit",
        "Profit / unit":    "profit_unit",
        "ROI %":            "roi",
        "Daily Volume":     "daily_volume",
    }
    sk = sort_key_map[sort_by]
    sorted_bulk = sorted(bulk, key=lambda x: -x.get(sk, 0))[:show_n]

    st.markdown(
        "<div class='note'>"
        "GE limit ≥1,000 · ≥200 trades/hr · "
        "<b>Potential Profit</b> = profit/unit × full GE limit (no cash cap) · "
        "<b>Adj. Potential</b> = Potential Profit × fill quality multiplier · "
        "<b>Realistic 4hr</b> = profit × min(GE limit, sell-side fills in 4hrs)"
        "</div>", unsafe_allow_html=True
    )

    BULK_COLS = ["name","buy_price","sell_price","tax","profit_unit","roi",
                 "buy_qty_hr","sell_qty_hr","ratio","fq_label","ge_limit",
                 "potential_profit","adj_potential","realistic_profit"]
    df_b, fmt_b = to_df(sorted_bulk, BULK_COLS)
    st.dataframe(df_b.style.format(fmt_b), use_container_width=True, hide_index=True, height=520)

    st.markdown("<div class='section-label'>Top bulk flips — chart</div>", unsafe_allow_html=True)
    chart_top = sorted_bulk[:15]
    fig = px.bar(
        pd.DataFrame([{"Item": r["name"], sort_by: r.get(sk, 0), "ROI %": round(r.get("roi",0),2)} for r in chart_top]),
        x="Item", y=sort_by, color="ROI %", color_continuous_scale="teal",
        title=f"Top 15 bulk flips sorted by {sort_by}",
        template="plotly_dark",
    )
    fig.update_layout(**DARK, xaxis_tickangle=-35, yaxis_title=sort_by)
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

    # Scatter: volume vs profit
    st.markdown("<div class='section-label'>Volume vs profit / unit — market landscape</div>", unsafe_allow_html=True)
    st.markdown("<div class='note'>High-volume + high-profit items are in the top-right. Ideal flips cluster there.</div>", unsafe_allow_html=True)
    sc_data = [{"Item": r["name"], "Sell Qty / hr": r["sell_qty_hr"],
                "Profit / unit": r["profit_unit"], "GE Limit": r["ge_limit"],
                "ROI %": round(r["roi"],2)} for r in bulk[:40]]
    fig_sc = px.scatter(
        pd.DataFrame(sc_data),
        x="Sell Qty / hr", y="Profit / unit",
        size="GE Limit", color="ROI %",
        hover_name="Item", color_continuous_scale="viridis",
        title="Bulk items — sell volume vs profit/unit (bubble = GE limit)",
        template="plotly_dark",
    )
    fig_sc.update_layout(**DARK, margin=dict(t=45, b=40))
    st.plotly_chart(fig_sc, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SINGULAR / HIGH MARGIN
# ═══════════════════════════════════════════════════════════════════════════════
with tab_singular:
    st.markdown("<div class='section-label'>Key metrics — singular flips</div>", unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Best Profit / unit",  fmt_gp(singular[0].get("profit_unit")) if singular else "—",  singular[0].get("name","") if singular else "")
    s2.metric("Best ROI %",          f"{singular[0].get('roi',0):.2f}%" if singular else "—",       f"{fmt_gp(singular[0].get('sell_price'))} sell price" if singular else "")
    s3.metric("Best Fill Quality",   singular[0].get("fq_label","—") if singular else "—",          "")
    s4.metric("Items in list",       str(len(singular)),                                             "GE limit ≤15 · price >500K")

    st.markdown("<br>", unsafe_allow_html=True)

    sc1b, sc2b = st.columns([2,1])
    with sc1b:
        s_sort = st.selectbox("Sort by", ["Profit / unit (adj)", "Profit / unit", "ROI %", "Sell Price"], index=0, key="sing_sort")
    with sc2b:
        s_n = st.selectbox("Show top", [10, 20, 30], index=1, key="sing_n")

    s_key_map = {
        "Profit / unit (adj)": lambda x: -(x.get("profit_unit",0) * x.get("fq_mult",1)),
        "Profit / unit":       lambda x: -x.get("profit_unit",0),
        "ROI %":               lambda x: -x.get("roi",0),
        "Sell Price":          lambda x: -x.get("sell_price",0),
    }
    sorted_sing = sorted(singular, key=s_key_map[s_sort])[:s_n]

    st.markdown(
        "<div class='note'>"
        "GE limit ≤15 · price >500K GP · ranked by demand-adjusted profit/unit · "
        "slow fills — check B/S ratio and daily volume before committing"
        "</div>", unsafe_allow_html=True
    )

    SING_COLS = ["name","buy_price","sell_price","tax","profit_unit","roi",
                 "buy_qty_hr","sell_qty_hr","ratio","fq_label","ge_limit","potential_profit"]
    df_s, fmt_s = to_df(sorted_sing, SING_COLS)
    st.dataframe(df_s.style.format(fmt_s), use_container_width=True, hide_index=True, height=480)

    st.markdown("<div class='section-label'>Singular flips — profit/unit chart</div>", unsafe_allow_html=True)
    fig_s = px.bar(
        pd.DataFrame([{"Item": r["name"], "Profit / unit": r["profit_unit"],
                       "ROI %": round(r.get("roi",0),2)} for r in sorted_sing[:15]]),
        x="Item", y="Profit / unit", color="ROI %",
        color_continuous_scale="purples",
        title="Top 15 singular flips — post-tax profit per unit",
        template="plotly_dark",
    )
    fig_s.update_layout(**DARK, xaxis_tickangle=-35, yaxis_title="Profit / unit (gp)")
    fig_s.update_traces(marker_line_width=0)
    st.plotly_chart(fig_s, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HIGH ROI
# ═══════════════════════════════════════════════════════════════════════════════
with tab_roi:
    st.markdown("<div class='section-label'>Key metrics — high ROI</div>", unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Best ROI %",          f"{high_roi[0].get('roi',0):.2f}%" if high_roi else "—",  high_roi[0].get("name","") if high_roi else "")
    r2.metric("Best Profit / unit",  fmt_gp(high_roi[0].get("profit_unit")) if high_roi else "—", f"limit: {high_roi[0].get('ge_limit',0):,}" if high_roi else "")
    r3.metric("Min ROI threshold",   "5%",   "≥50 trades/hr required")
    r4.metric("Items in list",       str(len(high_roi)), "")

    st.markdown("<br>", unsafe_allow_html=True)

    roi_n = st.selectbox("Show top", [10, 20, 30], index=1, key="roi_n")

    st.markdown(
        "<div class='note'>"
        "Any item with ROI ≥5% and ≥50 trades/hr · "
        "high ROI on a low-volume item can be a trap — check daily volume and fill quality"
        "</div>", unsafe_allow_html=True
    )

    ROI_COLS = ["name","buy_price","sell_price","tax","profit_unit","roi",
                "daily_volume","ratio","fq_label","ge_limit","potential_profit"]
    df_r, fmt_r = to_df(high_roi[:roi_n], ROI_COLS)
    st.dataframe(df_r.style.format(fmt_r), use_container_width=True, hide_index=True, height=480)

    # ROI vs volume scatter
    st.markdown("<div class='section-label'>ROI % vs daily volume</div>", unsafe_allow_html=True)
    st.markdown("<div class='note'>Top-right = high ROI + high volume = the best of both worlds.</div>", unsafe_allow_html=True)
    rsc = [{"Item": r["name"], "ROI %": round(r["roi"],2),
            "Daily Volume": r["daily_volume"], "Profit / unit": r["profit_unit"]} for r in high_roi[:40]]
    fig_r = px.scatter(
        pd.DataFrame(rsc), x="Daily Volume", y="ROI %",
        hover_name="Item", size="Profit / unit",
        color="ROI %", color_continuous_scale="greens",
        title="High ROI items — ROI % vs daily volume (bubble = profit/unit)",
        template="plotly_dark",
    )
    fig_r.update_layout(**DARK, margin=dict(t=45, b=40))
    st.plotly_chart(fig_r, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — INVESTMENT WATCHLIST
# ═══════════════════════════════════════════════════════════════════════════════
with tab_watch:
    st.markdown("<div class='section-label'>Live snapshot — investment-grade items</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='note'>"
        "These items are tracked for long-term price appreciation driven by game updates and meta shifts. "
        "Spread and ROI are secondary — the thesis is hold-to-profit, not active flipping."
        "</div>", unsafe_allow_html=True
    )

    if watch:
        w1, w2, w3 = st.columns(3)
        w1.metric("Items tracked", str(len(watch)), f"of {len(WATCHLIST_NAMES)} targets")
        best_w = max(watch, key=lambda x: x.get("profit_unit", 0))
        w2.metric("Highest spread today", fmt_gp(best_w.get("profit_unit")), best_w.get("name",""))
        best_roi_w = max(watch, key=lambda x: x.get("roi",0))
        w3.metric("Highest ROI today",    f"{best_roi_w.get('roi',0):.2f}%", best_roi_w.get("name",""))

        st.markdown("<br>", unsafe_allow_html=True)

        WATCH_COLS = ["name","buy_price","sell_price","tax","profit_unit","roi",
                      "buy_qty_hr","sell_qty_hr","ratio","fq_label","ge_limit"]
        df_w, fmt_w = to_df(watch, WATCH_COLS)
        st.dataframe(df_w.style.format(fmt_w), use_container_width=True, hide_index=True)

        fig_w = px.bar(
            df_w, x="Item", y="Profit / unit",
            color="ROI %", color_continuous_scale="oranges",
            title="Investment watchlist — current post-tax spread",
            template="plotly_dark",
        )
        fig_w.update_layout(**DARK, xaxis_tickangle=-25, yaxis_title="Profit / unit (gp)")
        fig_w.update_traces(marker_line_width=0)
        st.plotly_chart(fig_w, use_container_width=True)

        # Watchlist timeseries — fetch 90-day history for each item
        st.markdown("<div class='section-label'>90-day price history — select an item</div>", unsafe_allow_html=True)
        watch_names = [r["name"] for r in watch]
        selected = st.selectbox("Item", watch_names, key="watch_item")
        sel_row = next((r for r in watch if r["name"] == selected), None)
        if sel_row:
            ts_data = fetch_timeseries(sel_row["id"], "24h")
            if ts_data:
                ts_df = pd.DataFrame(ts_data)
                ts_df["date"] = pd.to_datetime(ts_df["timestamp"], unit="s")
                fig_ts = go.Figure()
                fig_ts.add_trace(go.Scatter(x=ts_df["date"], y=ts_df["avgHighPrice"],
                                            name="Sell (high)", line=dict(color="#38bdf8")))
                fig_ts.add_trace(go.Scatter(x=ts_df["date"], y=ts_df["avgLowPrice"],
                                            name="Buy (low)", line=dict(color="#818cf8")))
                fig_ts.update_layout(
                    title=f"{selected} — 90-day price history",
                    template="plotly_dark", **DARK,
                    margin=dict(t=45, b=40),
                    yaxis_title="Price (gp)", xaxis_title=""
                )
                st.plotly_chart(fig_ts, use_container_width=True)
            else:
                st.info("No timeseries data available for this item right now.")
    else:
        st.info("No watchlist items found in this data pull.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — GUIDE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_guide:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### Column Reference")
        st.markdown("""
| Column | Formula | What to look for |
|---|---|---|
| **Buy Price** | Instasell price | What you offer to buy at |
| **Sell Price** | Instabuy price | What you list to sell at |
| **Tax (gp)** | min(sell × 2%, 5M) | Your cost — shown separately |
| **Profit / unit** | Sell − Buy − Tax | Post-tax margin per flip |
| **ROI %** | (Profit / Buy) × 100 | Efficiency of capital |
| **Potential Profit** | Profit × GE Limit | Max GP if limit fully filled |
| **Adj. Potential** | Potential × Fill Quality | Realistic ranking score |
| **Realistic 4hr** | Profit × min(limit, sell-side fills) | Based on actual liquidity |
| **Buy Qty / hr** | 5-min high vol × 12 | How many people are buying |
| **Sell Qty / hr** | 5-min low vol × 12 | How many people are selling |
| **Daily Volume** | total_hr × 24 | Estimated full-day trades |
| **B/S Ratio** | Buy qty ÷ Sell qty | Market demand balance |
| **Fill Quality** | Derived from B/S ratio | How reliably both sides fill |
        """)

        st.markdown("### B/S Ratio Key")
        st.markdown("""
| Ratio | Label | Meaning |
|---|---|---|
| ✅ 0.8 – 1.5 | **Ideal** | Balanced — both sides fill predictably |
| 🔼 1.5 – 3.0 | **High demand** | Sells fast, buy offers sit longer |
| 🔴 > 3.0 | **Hard to buy** | Extreme demand — your buy offer may sit for hours |
| 🟡 0.4 – 0.8 | **Slight flood** | More sellers than buyers — sells slower |
| 🔴 < 0.4 | **Flooded** | Market dumped — very hard to sell out |
        """)

    with col_b:
        st.markdown("### GE Tax Rules (2025)")
        st.markdown("""
- Tax is **2%** charged to the **seller only** (not the buyer)
- Hard cap of **5,000,000 GP** per item sold
- Items under **50 GP** are tax-exempt
- Every profit figure in this dashboard is **post-tax**
        """)

        st.markdown("### GE Buying Limits")
        st.markdown("""
- Every item has a maximum you can buy per **4-hour window**
- The 4-hour timer starts when your **first item fills**, not when you place the order
- After 4 hours, your limit resets and you can buy again
- You have **8 GE slots** — run multiple items simultaneously
- **Potential Profit** assumes you fill your full limit (best case)
- **Realistic 4hr** is capped by actual sell-side volume (more honest)
        """)

        st.markdown("### Timing Strategy")
        st.markdown("""
- 🔴 **10 PM – 6 AM ET** — Buy window. Off-peak, bots supply items cheaply. Place buy orders.
- 🟡 **6 AM – 2 PM ET** — Transition. Moderate activity. Place and monitor orders.
- 🟢 **2 PM – 10 PM ET** — Sell window. Peak US/EU overlap. Best time to list sell orders.
        """)

        st.markdown("### Which tab to use")
        st.markdown("""
- **📦 Bulk Flips** — Herbs, pots, runes, bars. Fast fills. Lower profit/unit but high volume.
- **💎 Singular** — BIS gear, rare drops. Slow fills. High profit per unit, low limit (≤15).
- **📈 High ROI** — Any item where your % return is exceptional. Check volume carefully.
- **🔭 Watchlist** — Investment-grade items. Hold thesis, not active flip.
        """)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='font-size:0.68rem;color:#334155;text-align:center'>"
    "Data: OSRS Wiki Real-Time Prices API (RuneLite) · 2% GE tax · 5M GP cap · "
    "5-min buckets × 12 = trades/hr · Fills not guaranteed · Not financial advice"
    "</div>", unsafe_allow_html=True
)