import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import pytz
from ge_api import (
    fetch_latest, fetch_mapping, fetch_volumes, fetch_timeseries,
    compute_flips, WATCHLIST_NAMES
)

st.set_page_config(
    page_title="OSRS GE Flip Dashboard",
    layout="wide",
    page_icon="⚔️",
    initial_sidebar_state="collapsed",
)

PRICE_INTERVAL  = 60
VOLUME_INTERVAL = 300
MAPPING_KEY     = "mapping_loaded"

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .stTabs [data-baseweb="tab-list"] {
    gap:0; background:#0f172a; border-bottom:1px solid #1e293b; padding:0 1rem;
  }
  .stTabs [data-baseweb="tab"] {
    background:transparent !important; color:#64748b !important;
    font-size:0.82rem; font-weight:500;
    padding:0.75rem 1.25rem; border-bottom:2px solid transparent; border-radius:0;
  }
  .stTabs [aria-selected="true"] {
    color:#f1f5f9 !important; border-bottom:2px solid #3b82f6 !important;
    background:transparent !important;
  }
  .stTabs [data-baseweb="tab-panel"] { padding-top:1.25rem; }

  [data-testid="stMetric"] {
    background:#1e293b; border:1px solid #334155; border-radius:8px; padding:0.85rem 1rem;
  }
  [data-testid="stMetricLabel"] { font-size:0.65rem !important; text-transform:uppercase; letter-spacing:0.08em; color:#64748b !important; }
  [data-testid="stMetricValue"] { font-size:1.35rem !important; font-weight:700; color:#f1f5f9 !important; }
  [data-testid="stMetricDelta"]  { font-size:0.72rem !important; }

  [data-testid="stDataFrame"] { border:1px solid #1e293b; border-radius:8px; }
  [data-testid="stDataFrame"] th {
    background:#0f172a !important; color:#94a3b8 !important;
    font-size:0.72rem !important; text-transform:uppercase; letter-spacing:0.05em;
  }
  [data-testid="stDataFrame"] td { font-size:0.82rem !important; }

  .banner-green  { background:#052e16; border:1px solid #166534; border-radius:6px; padding:0.5rem 1rem; color:#bbf7d0; font-size:0.82rem; margin-bottom:1rem; }
  .banner-yellow { background:#1c1700; border:1px solid #92400e; border-radius:6px; padding:0.5rem 1rem; color:#fde68a; font-size:0.82rem; margin-bottom:1rem; }
  .banner-red    { background:#1f0606; border:1px solid #991b1b; border-radius:6px; padding:0.5rem 1rem; color:#fecaca; font-size:0.82rem; margin-bottom:1rem; }

  .section-label {
    font-size:0.65rem; text-transform:uppercase; letter-spacing:0.12em;
    color:#475569; border-bottom:1px solid #1e293b;
    padding-bottom:0.25rem; margin:1.25rem 0 0.4rem 0;
  }
  .note { font-size:0.73rem; color:#64748b; margin-bottom:0.6rem; }
  .refresh-bar {
    display:flex; gap:1.25rem; align-items:center;
    font-size:0.72rem; color:#475569; padding:0.4rem 0 0.6rem 0;
  }
  .refresh-bar b { color:#38bdf8; }

  #MainMenu, footer, header { visibility:hidden; }
  .block-container { padding-top:0.75rem; padding-bottom:2rem; max-width:100% !important; }
  button[kind="primary"] { background:#2563eb !important; border:none !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_gp(n):
    if n is None: return "—"
    n = int(n)
    if abs(n) >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:     return f"{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:         return f"{n/1_000:.1f}K"
    return f"{n:,}"

def fmt_gp_col(n):
    """Column-safe version: returns clean string like 2.3M"""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "—"
    if abs(n) >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:     return f"{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:         return f"{n/1_000:.1f}K"
    return f"{n:,}"

def now_ts():
    return time.time()

def secs_ago(ts):
    return int(now_ts() - ts) if ts else None

def fmt_ago(s):
    if s is None: return "never"
    if s < 60:    return f"{s}s ago"
    return f"{s//60}m {s%60}s ago"

def get_timing():
    est = pytz.timezone("America/New_York")
    now = datetime.now(est)
    h, ts = now.hour, now.strftime("%I:%M %p ET")
    if 14 <= h < 22:
        return "green",  f"🟢  Peak sell window — US/EU overlap active. Best time to exit positions. ({ts})"
    elif 6 <= h < 14:
        return "yellow", f"🟡  Transition window — Moderate activity. Good for placing buy orders. ({ts})"
    else:
        return "red",    f"🔴  Buy window — Off-peak. Place buys now, sell into afternoon peak. ({ts})"

def ratio_tag(r):
    if r is None:             return "— no data"
    if 0.8 <= r <= 1.5:      return f"✅ {r:.2f}"
    elif 1.5 < r <= 3.0:     return f"🔼 {r:.2f}"
    elif r > 3.0:             return f"🔴 {r:.2f}"
    elif 0.4 <= r < 0.8:     return f"🟡 {r:.2f}"
    else:                     return f"🔴 {r:.2f}"

def fq_tag(label):
    return {
        "Ideal":        "✅ Ideal",
        "High demand":  "🔼 High demand",
        "Hard to buy":  "🔴 Hard to buy",
        "Slight flood": "🟡 Slight flood",
        "Flooded":      "🔴 Flooded",
        "No data":      "— No data",
    }.get(label, label)

# ── Row → DataFrame builder ───────────────────────────────────────────────────
# All GP columns are pre-formatted as strings (e.g. "2.3M") so no pandas
# number formatter is needed and decimals never appear.
COL_DEFS = {
    # key            : (display label,  transform)
    "name"           : ("Item",            lambda v: v),
    "buy_price"      : ("Buy",             fmt_gp_col),
    "sell_price"     : ("Sell",            fmt_gp_col),
    "tax"            : ("Tax",             fmt_gp_col),
    "profit_unit"    : ("Profit/unit",     fmt_gp_col),
    "roi"            : ("ROI %",           lambda v: f"{v:.1f}%"),
    "buy_qty_hr"     : ("Buy/hr",          lambda v: f"{int(v):,}"),
    "sell_qty_hr"    : ("Sell/hr",         lambda v: f"{int(v):,}"),
    "daily_volume"   : ("Daily Vol",       lambda v: fmt_gp_col(v)),
    "ratio"          : ("B/S",             ratio_tag),
    "fq_label"       : ("Fill",            fq_tag),
    "ge_limit"       : ("GE Lmt",          lambda v: f"{int(v):,}"),
    "potential_profit": ("Pot. Profit",    fmt_gp_col),
    "adj_potential"  : ("Adj. Potential",  fmt_gp_col),
    "realistic_profit": ("Realistic 4hr", fmt_gp_col),
}

def to_df(rows, col_keys):
    records = []
    for r in rows:
        row = {}
        for k in col_keys:
            label, fn = COL_DEFS[k]
            row[label] = fn(r.get(k))
        records.append(row)
    return pd.DataFrame(records)

# ── Colour-highlighting helpers ───────────────────────────────────────────────
# Applied to ROI % column (string) and Profit/unit column (string)
# We re-derive the numeric values from the raw rows for the styler.


# ── Colour-highlighting — axis=1 compatible with all pandas versions ──────────
def _profit_color(val_str, pct):
    """Return CSS string for a profit/unit cell based on its relative rank."""
    if pct >= 0.7: return "background:#052e16; color:#4ade80; font-weight:600"
    if pct >= 0.4: return "background:#0f2d1a; color:#86efac"
    return ""

def _roi_color(roi):
    if roi >= 20:  return "background:#1c1000; color:#fbbf24; font-weight:600"
    if roi >= 10:  return "background:#1a1200; color:#fde68a"
    if roi >= 5:   return "background:#171400; color:#fef9c3"
    return ""

def highlight_rows(df, rows, col_keys):
    """Row-by-row styler — works with pandas ≥2.0 and Python 3.14."""
    profit_label = COL_DEFS["profit_unit"][0]
    roi_label    = COL_DEFS["roi"][0]

    profit_vals = [r.get("profit_unit", 0) for r in rows]
    roi_vals    = [r.get("roi", 0)         for r in rows]
    p_max = max(profit_vals) if profit_vals else 1

    # Build a lookup: row-index → (profit_pct, roi)
    row_meta = {
        i: (profit_vals[i] / p_max if p_max else 0, roi_vals[i])
        for i in range(len(rows))
    }

    cols = list(df.columns)

    def style_row(row):
        idx = row.name  # integer index
        if idx not in row_meta:
            return [""] * len(cols)
        pct, roi = row_meta[idx]
        result = []
        for col in cols:
            if col == profit_label:
                result.append(_profit_color(row[col], pct))
            elif col == roi_label:
                result.append(_roi_color(roi))
            else:
                result.append("")
        return result

    return df.style.apply(style_row, axis=1)

DARK = dict(
    plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
    title_font_size=13,
)

# ── Fetch / cache ─────────────────────────────────────────────────────────────
def stale(key, interval):
    last = st.session_state.get(key)
    return last is None or (now_ts() - last) >= interval

def load_mapping():
    if MAPPING_KEY not in st.session_state:
        st.session_state["mapping"]   = fetch_mapping()
        st.session_state[MAPPING_KEY] = True

def do_prices():
    st.session_state["latest"]   = fetch_latest()
    st.session_state["price_ts"] = now_ts()

def do_volumes():
    h, f = fetch_volumes()
    st.session_state["hour_vols"]  = h
    st.session_state["fmin_vols"]  = f
    st.session_state["volume_ts"]  = now_ts()

def recompute():
    result = compute_flips(
        st.session_state.get("latest", {}),
        st.session_state.get("mapping", []),
        st.session_state.get("hour_vols", {}),
        st.session_state.get("fmin_vols", {}),
    )
    st.session_state["data"] = result

# ── Header ────────────────────────────────────────────────────────────────────
h1, h2, h3 = st.columns([4, 3, 1])
with h1:
    st.markdown("## ⚔️ OSRS GE Flip Dashboard")
with h3:
    manual = st.button("🔄 Refresh", type="primary", use_container_width=True)

with st.spinner("Loading…"):
    load_mapping()
    if manual or stale("price_ts", PRICE_INTERVAL):
        do_prices()
    if manual or stale("volume_ts", VOLUME_INTERVAL):
        do_volumes()
    recompute()

# Auto-rerun every 60s
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=PRICE_INTERVAL * 1000, key="ar")
except ImportError:
    pass

p_ago = secs_ago(st.session_state.get("price_ts"))
v_ago = secs_ago(st.session_state.get("volume_ts"))
with h2:
    st.markdown(
        f"<div class='refresh-bar'>"
        f"💰 Prices: <b>{fmt_ago(p_ago)}</b> &nbsp;·&nbsp; "
        f"📊 Volumes: <b>{fmt_ago(v_ago)}</b> &nbsp;·&nbsp; "
        f"<span style='color:#475569'>auto every 60s</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

if "data" not in st.session_state:
    st.info("Loading data…")
    st.stop()

bulk, singular, high_roi, watch, all_rows = st.session_state["data"]

tw_color, tw_msg = get_timing()
st.markdown(f"<div class='banner-{tw_color}'>{tw_msg}</div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
t_bulk, t_sing, t_roi, t_watch, t_guide = st.tabs([
    "📦  Bulk Flips",
    "💎  Singular / High Margin",
    "📈  High ROI",
    "🔭  Investment Watchlist",
    "📖  Guide",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BULK FLIPS
# ═══════════════════════════════════════════════════════════════════════════════
with t_bulk:
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Best Adj. Potential",   fmt_gp(bulk[0].get("adj_potential"))    if bulk else "—", bulk[0].get("name","") if bulk else "")
    k2.metric("Best Profit / unit",    fmt_gp(bulk[0].get("profit_unit"))      if bulk else "—", f"{bulk[0].get('roi',0):.1f}% ROI" if bulk else "")
    k3.metric("Best Potential Profit", fmt_gp(bulk[0].get("potential_profit")) if bulk else "—", "Full GE limit × profit/unit")
    k4.metric("Items in list",         str(len(bulk)), "GE limit ≥1,000 · ≥200 trades/hr")
    st.markdown("<br>", unsafe_allow_html=True)

    show_n = st.selectbox("Show top", [10,20,30,40,60], index=1, key="bulk_n")
    # Default sort: adj_potential (best for decision-making)
    display_bulk = sorted(bulk, key=lambda x: -x.get("adj_potential",0))[:show_n]

    st.markdown("<div class='note'>"
        "Ranked by <b>Adj. Potential</b> (= Potential Profit × fill quality). "
        "Green = high profit/unit · Gold = high ROI%"
        "</div>", unsafe_allow_html=True)

    BULK_COLS = ["name","buy_price","sell_price","tax","profit_unit","roi",
                 "buy_qty_hr","sell_qty_hr","ratio","fq_label","ge_limit",
                 "potential_profit","adj_potential","realistic_profit"]
    df_b = to_df(display_bulk, BULK_COLS)
    st.dataframe(
        highlight_rows(df_b, display_bulk, BULK_COLS),
        use_container_width=True, hide_index=True, height=560,
    )

    st.markdown("<div class='section-label'>Top 15 — adj. potential</div>", unsafe_allow_html=True)
    chart_rows = display_bulk[:15]
    fig = go.Figure(go.Bar(
        x=[r["name"] for r in chart_rows],
        y=[r["adj_potential"] for r in chart_rows],
        marker=dict(
            color=[r["roi"] for r in chart_rows],
            colorscale="teal",
            showscale=True,
            colorbar=dict(title="ROI %"),
        ),
        text=[fmt_gp_col(r["adj_potential"]) for r in chart_rows],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Adj. Potential: %{text}<br>ROI: %{marker.color:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
        title="Top 15 bulk flips — demand-adjusted potential profit",
        title_font_size=13,
        xaxis_tickangle=-35,
        yaxis_title="Adj. Potential (gp)",
        margin=dict(t=50, b=80, l=60, r=60),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-label'>Volume vs profit/unit — market landscape</div>", unsafe_allow_html=True)
    sc_data = pd.DataFrame([{
        "Item": r["name"],
        "Sell/hr": r["sell_qty_hr"],
        "Profit/unit": r["profit_unit"],
        "GE Limit": r["ge_limit"],
        "ROI %": r["roi"],
    } for r in bulk[:40]])
    fig_sc = px.scatter(
        sc_data, x="Sell/hr", y="Profit/unit",
        size="GE Limit", color="ROI %",
        hover_name="Item", color_continuous_scale="viridis",
        title="Bulk items — sell volume vs profit/unit (bubble = GE limit)",
        template="plotly_dark",
    )
    fig_sc.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
        title_font_size=13, margin=dict(t=50, b=50, l=60, r=60),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SINGULAR / HIGH MARGIN
# ═══════════════════════════════════════════════════════════════════════════════
with t_sing:
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("Best Profit / unit",fmt_gp(singular[0].get("profit_unit")) if singular else "—", singular[0].get("name","") if singular else "")
    s2.metric("Best ROI %",        f"{singular[0].get('roi',0):.1f}%"    if singular else "—", f"{fmt_gp(singular[0].get('sell_price'))} sell" if singular else "")
    s3.metric("Best Fill Quality", singular[0].get("fq_label","—")       if singular else "—", "")
    s4.metric("Items in list",     str(len(singular)), "GE limit ≤15 · price >500K")
    st.markdown("<br>", unsafe_allow_html=True)

    s_n = st.selectbox("Show top", [10,20,30,40], index=1, key="sing_n")
    display_sing = sorted(singular, key=lambda x: -(x.get("profit_unit",0)*x.get("fq_mult",1)))[:s_n]

    st.markdown("<div class='note'>"
        "Ranked by demand-adjusted profit/unit. Slow fills — always verify B/S ratio and daily volume before committing capital."
        "</div>", unsafe_allow_html=True)

    SING_COLS = ["name","buy_price","sell_price","tax","profit_unit","roi",
                 "buy_qty_hr","sell_qty_hr","ratio","fq_label","ge_limit","potential_profit"]
    df_s = to_df(display_sing, SING_COLS)
    st.dataframe(
        highlight_rows(df_s, display_sing, SING_COLS),
        use_container_width=True, hide_index=True, height=500,
    )

    st.markdown("<div class='section-label'>Top 15 — profit per unit</div>", unsafe_allow_html=True)
    chart_s = display_sing[:15]
    fig_s = go.Figure(go.Bar(
        x=[r["name"] for r in chart_s],
        y=[r["profit_unit"] for r in chart_s],
        marker=dict(
            color=[r["roi"] for r in chart_s],
            colorscale="purples",
            showscale=True,
            colorbar=dict(title="ROI %"),
        ),
        text=[fmt_gp_col(r["profit_unit"]) for r in chart_s],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Profit/unit: %{text}<br>ROI: %{marker.color:.1f}%<extra></extra>",
    ))
    fig_s.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
        title="Top 15 singular flips — post-tax profit per unit",
        title_font_size=13,
        xaxis_tickangle=-35,
        yaxis_title="Profit / unit (gp)",
        margin=dict(t=50, b=80, l=60, r=60),
    )
    st.plotly_chart(fig_s, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HIGH ROI
# ═══════════════════════════════════════════════════════════════════════════════
with t_roi:
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Best ROI %",        f"{high_roi[0].get('roi',0):.1f}%" if high_roi else "—", high_roi[0].get("name","") if high_roi else "")
    r2.metric("Best Profit / unit",fmt_gp(high_roi[0].get("profit_unit")) if high_roi else "—", f"limit: {high_roi[0].get('ge_limit',0):,}" if high_roi else "")
    r3.metric("Min ROI threshold", "5%", "≥50 trades/hr required")
    r4.metric("Items in list",     str(len(high_roi)), "")
    st.markdown("<br>", unsafe_allow_html=True)

    roi_n = st.selectbox("Show top", [10,20,30,40], index=1, key="roi_n")
    display_roi = sorted(high_roi, key=lambda x: -x.get("roi",0))[:roi_n]

    st.markdown("<div class='note'>"
        "Any item with ROI ≥5% and ≥50 trades/hr. "
        "High ROI on low-volume items is a trap — always check Daily Volume and Fill Quality."
        "</div>", unsafe_allow_html=True)

    ROI_COLS = ["name","buy_price","sell_price","tax","profit_unit","roi",
                "daily_volume","ratio","fq_label","ge_limit","potential_profit"]
    df_r = to_df(display_roi, ROI_COLS)
    st.dataframe(
        highlight_rows(df_r, display_roi, ROI_COLS),
        use_container_width=True, hide_index=True, height=500,
    )

    st.markdown("<div class='section-label'>ROI % vs daily volume</div>", unsafe_allow_html=True)
    rsc = pd.DataFrame([{
        "Item": r["name"],
        "ROI %": r["roi"],
        "Daily Volume": r["daily_volume"],
        "Profit/unit": r["profit_unit"],
    } for r in high_roi[:40]])
    fig_r = px.scatter(
        rsc, x="Daily Volume", y="ROI %",
        hover_name="Item", size="Profit/unit",
        color="ROI %", color_continuous_scale="greens",
        title="High ROI items — ROI % vs daily volume (top-right = best of both worlds)",
        template="plotly_dark",
    )
    fig_r.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
        title_font_size=13, margin=dict(t=50, b=50, l=60, r=60),
    )
    st.plotly_chart(fig_r, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — INVESTMENT WATCHLIST
# ═══════════════════════════════════════════════════════════════════════════════
with t_watch:
    st.markdown("<div class='note'>"
        "Hold-thesis items. Spread and ROI are secondary — "
        "long-term price appreciation from game updates is the primary signal."
        "</div>", unsafe_allow_html=True)

    if watch:
        w1,w2,w3 = st.columns(3)
        w1.metric("Items tracked", str(len(watch)), f"of {len(WATCHLIST_NAMES)} targets")
        best_w     = max(watch, key=lambda x: x.get("profit_unit",0))
        best_roi_w = max(watch, key=lambda x: x.get("roi",0))
        w2.metric("Highest spread",fmt_gp(best_w.get("profit_unit")), best_w.get("name",""))
        w3.metric("Highest ROI",   f"{best_roi_w.get('roi',0):.1f}%", best_roi_w.get("name",""))
        st.markdown("<br>", unsafe_allow_html=True)

        WATCH_COLS = ["name","buy_price","sell_price","tax","profit_unit","roi",
                      "buy_qty_hr","sell_qty_hr","ratio","fq_label","ge_limit"]
        df_w = to_df(watch, WATCH_COLS)
        st.dataframe(
            highlight_rows(df_w, watch, WATCH_COLS),
            use_container_width=True, hide_index=True,
        )

        chart_w = watch
        fig_w = go.Figure(go.Bar(
            x=[r["name"] for r in chart_w],
            y=[r["profit_unit"] for r in chart_w],
            marker=dict(
                color=[r["roi"] for r in chart_w],
                colorscale="oranges",
                showscale=True,
                colorbar=dict(title="ROI %"),
            ),
            text=[fmt_gp_col(r["profit_unit"]) for r in chart_w],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Profit/unit: %{text}<br>ROI: %{marker.color:.1f}%<extra></extra>",
        ))
        fig_w.update_layout(
            template="plotly_dark",
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
            title="Investment watchlist — current post-tax spread",
            title_font_size=13,
            xaxis_tickangle=-25,
            yaxis_title="Profit / unit (gp)",
            margin=dict(t=50, b=80, l=60, r=60),
        )
        st.plotly_chart(fig_w, use_container_width=True)

        st.markdown("<div class='section-label'>90-day price history</div>", unsafe_allow_html=True)
        selected = st.selectbox("Select item", [r["name"] for r in watch], key="watch_item")
        sel_row  = next((r for r in watch if r["name"] == selected), None)
        if sel_row:
            ts_data = fetch_timeseries(sel_row["id"], "24h")
            if ts_data:
                ts_df = pd.DataFrame(ts_data)
                ts_df["date"] = pd.to_datetime(ts_df["timestamp"], unit="s")
                avg_high = ts_df["avgHighPrice"].mean()
                avg_low  = ts_df["avgLowPrice"].mean()
                fig_ts = go.Figure()
                fig_ts.add_trace(go.Scatter(
                    x=ts_df["date"], y=ts_df["avgHighPrice"],
                    name="Sell (high)", line=dict(color="#38bdf8"),
                    fill="tonexty" if False else None,
                ))
                fig_ts.add_trace(go.Scatter(
                    x=ts_df["date"], y=ts_df["avgLowPrice"],
                    name="Buy (low)", line=dict(color="#818cf8"),
                ))
                # 90-day average reference lines
                fig_ts.add_hline(y=avg_high, line_dash="dot", line_color="#38bdf8",
                                 annotation_text=f"90d avg sell: {fmt_gp_col(avg_high)}",
                                 annotation_position="bottom right")
                fig_ts.add_hline(y=avg_low, line_dash="dot", line_color="#818cf8",
                                 annotation_text=f"90d avg buy: {fmt_gp_col(avg_low)}",
                                 annotation_position="top right")
                fig_ts.update_layout(
                    template="plotly_dark",
                    plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
                    title=f"{selected} — 90-day price history",
                    title_font_size=13,
                    margin=dict(t=50, b=50, l=60, r=60),
                    yaxis_title="Price (gp)",
                    xaxis_title="",
                )
                st.plotly_chart(fig_ts, use_container_width=True)

                # Buy signal: is current buy price below 90d avg?
                cur_buy  = sel_row.get("buy_price", 0)
                cur_sell = sel_row.get("sell_price", 0)
                if cur_buy < avg_low * 0.97:
                    st.success(f"🟢 Buy signal: current buy price ({fmt_gp_col(cur_buy)}) is >3% below 90-day avg ({fmt_gp_col(avg_low)}). Possible dip entry.")
                elif cur_sell > avg_high * 1.05:
                    st.warning(f"🔴 Elevated: current sell price ({fmt_gp_col(cur_sell)}) is >5% above 90-day avg ({fmt_gp_col(avg_high)}). May be a spike — wait for pullback.")
                else:
                    st.info(f"⚪ Neutral: prices within normal range of 90-day average.")
            else:
                st.info("No timeseries data available right now.")
    else:
        st.info("No watchlist items found in this pull.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — GUIDE
# ═══════════════════════════════════════════════════════════════════════════════
with t_guide:
    ga, gb = st.columns(2)
    with ga:
        st.markdown("### Column Reference")
        st.markdown("""
| Column | What it means |
|---|---|
| **Buy** | Instasell — your offer price |
| **Sell** | Instabuy — your sell list price |
| **Tax** | min(sell × 2%, 5M GP) — charged to seller |
| **Profit/unit** | Sell − Buy − Tax (post-tax) |
| **ROI %** | (Profit ÷ Buy) × 100 |
| **Pot. Profit** | Profit/unit × full GE limit |
| **Adj. Potential** | Pot. Profit × fill quality multiplier |
| **Realistic 4hr** | Profit × min(GE limit, sell-side fills × 4) |
| **Buy/hr** | /1h highPriceVol (fallback: /5m × 12) |
| **Sell/hr** | /1h lowPriceVol (fallback: /5m × 12) |
| **Daily Vol** | total_hr × 24 (estimated) |
| **B/S** | Buy/hr ÷ Sell/hr — demand balance |
| **Fill** | Fill quality derived from B/S ratio |
        """)

        st.markdown("### B/S Ratio Key")
        st.markdown("""
| B/S | Label | Meaning |
|---|---|---|
| ✅ 0.8 – 1.5 | Ideal | Both sides fill predictably |
| 🔼 1.5 – 3.0 | High demand | Sells fast, buys sit longer |
| 🔴 > 3.0 | Hard to buy | Buy offer may sit hours |
| 🟡 0.4 – 0.8 | Slight flood | More sellers, sells slower |
| 🔴 < 0.4 | Flooded | Very hard to sell |
        """)

    with gb:
        st.markdown("### Colour Coding")
        st.markdown("""
| Colour | Signal |
|---|---|
| 🟩 Dark green | High profit/unit (top 70% of list) |
| 🟩 Medium green | Mid-tier profit/unit (top 40–70%) |
| 🟨 Gold | ROI ≥ 20% |
| 🟨 Pale yellow | ROI 10–20% |
        """)

        st.markdown("### Refresh Schedule")
        st.markdown("""
| Data | Endpoint | Interval |
|---|---|---|
| Buy/sell prices | `/latest` | Every **60s** (auto) |
| Trade volumes | `/1h` + `/5m` fallback | Every **5 min** (auto) |
| Item metadata | `/mapping` | Once at startup |
| Price history | `/timeseries` | On-demand (Watchlist tab) |

Volumes use `/1h` first — prevents sparse items (e.g. impling jars) showing 0 on quiet 5-min windows.
        """)

        st.markdown("### GE Tax (2025)")
        st.markdown("""
- **2%** of sell price, charged to seller
- **5M GP hard cap** per item
- Items under **50 GP** exempt
- All figures in this dashboard are **post-tax**
        """)

        st.markdown("### Timing")
        st.markdown("""
| Window | Time (ET) | Action |
|---|---|---|
| 🔴 Buy | 10 PM – 6 AM | Place buy orders at off-peak |
| 🟡 Transition | 6 AM – 2 PM | Monitor and adjust |
| 🟢 Sell | 2 PM – 10 PM | List sell orders at peak activity |
        """)

st.markdown("---")
st.markdown(
    "<div style='font-size:0.68rem;color:#334155;text-align:center'>"
    "Data: OSRS Wiki Real-Time Prices API (RuneLite) · 2% GE tax · 5M GP cap · "
    "Prices every 60s · Volumes every 5m · Fills not guaranteed · Not financial advice"
    "</div>",
    unsafe_allow_html=True,
)