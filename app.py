import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import pytz
from ge_api import (
    fetch_latest, fetch_mapping, fetch_volumes, fetch_timeseries,
    compute_flips, WATCHLIST_NAMES, WATCHLIST_CATALYSTS
)

st.set_page_config(
    page_title="Owen's GE Tracker",
    layout="wide",
    page_icon="",
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
  .stTabs [data-baseweb="tab-panel"] { padding-top:1rem; }

  [data-testid="stDataFrame"] { border:1px solid #1e293b; border-radius:8px; }
  [data-testid="stDataFrame"] th {
    background:#0f172a !important; color:#94a3b8 !important;
    font-size:0.72rem !important; text-transform:uppercase; letter-spacing:0.05em;
  }
  [data-testid="stDataFrame"] td { font-size:0.82rem !important; }
  [data-testid="stDataFrame"] [role="gridcell"] { white-space: normal !important; line-height: 1.25 !important; }
  [data-testid="stDataFrame"] [role="columnheader"] { white-space: normal !important; }

  .banner-green  { background:#052e16; border:1px solid #166534; border-radius:6px; padding:0.45rem 1rem; color:#bbf7d0; font-size:0.8rem; margin-bottom:0.75rem; }
  .banner-yellow { background:#1c1700; border:1px solid #92400e; border-radius:6px; padding:0.45rem 1rem; color:#fde68a; font-size:0.8rem; margin-bottom:0.75rem; }
  .banner-red    { background:#1f0606; border:1px solid #991b1b; border-radius:6px; padding:0.45rem 1rem; color:#fecaca; font-size:0.8rem; margin-bottom:0.75rem; }

  .section-label {
    font-size:0.62rem; text-transform:uppercase; letter-spacing:0.12em;
    color:#475569; border-bottom:1px solid #1e293b;
    padding-bottom:0.2rem; margin:1.1rem 0 0.35rem 0;
  }
  .refresh-bar {
    display:flex; gap:1.25rem; align-items:center;
    font-size:0.72rem; color:#475569; padding:0.3rem 0 0.5rem 0;
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
    try: n = int(n)
    except: return "—"
    if abs(n) >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:     return f"{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:         return f"{n/1_000:.1f}K"
    return f"{n:,}"

def now_ts():  return time.time()
def secs_ago(ts): return int(now_ts() - ts) if ts else None
def fmt_ago(s):
    if s is None: return "never"
    if s < 60:    return f"{s}s ago"
    return f"{s//60}m {s%60}s ago"

def get_timing():
    est = pytz.timezone("America/New_York")
    now = datetime.now(est)
    h, ts = now.hour, now.strftime("%I:%M %p ET")
    if 14 <= h < 22:
        return "green",  f"Sell window — US/EU peak overlap. Best time to exit positions. ({ts})"
    elif 6 <= h < 14:
        return "yellow", f"Transition window — Moderate activity. Good for placing buy orders. ({ts})"
    else:
        return "red",    f"Buy window — Off-peak. Place buy orders now, sell into afternoon. ({ts})"

def ratio_fmt(r):
    if r is None: return "—"
    return f"{r:.2f}"

def ratio_css(r):
    if r is None: return "color:#64748b"
    if 0.8 <= r <= 1.5:  return "color:#4ade80"
    if 1.5 < r <= 3.0:   return "color:#fb923c"
    if r > 3.0:           return "color:#f87171"
    if 0.4 <= r < 0.8:   return "color:#facc15"
    return "color:#f87171"

def fq_fmt(label):
    return {
        "Ideal":        "Ideal",
        "High demand":  "High demand",
        "Hard to buy":  "Hard to buy",
        "Slight flood": "Slight flood",
        "Flooded":      "Flooded",
        "No data":      "—",
    }.get(label, label)

def fq_css(label):
    return {
        "Ideal":        "color:#4ade80",
        "High demand":  "color:#fb923c",
        "Hard to buy":  "color:#f87171",
        "Slight flood": "color:#facc15",
        "Flooded":      "color:#f87171",
        "No data":      "color:#64748b",
    }.get(label, "")

def pct_css(v):
    if v is None: return "color:#64748b"
    if v >= 10: return "color:#22c55e; font-weight:600"
    if v > 0: return "color:#86efac"
    if v <= -10: return "color:#ef4444; font-weight:600"
    if v < 0: return "color:#fca5a5"
    return "color:#cbd5e1"

def trend_css(t):
    return {
        "Pullback": "color:#facc15; font-weight:600",
        "Building": "color:#4ade80; font-weight:600",
        "Extended": "color:#fb923c; font-weight:600",
        "Weakening": "color:#ef4444; font-weight:600",
        "Flat": "color:#94a3b8",
    }.get(t, "")

# ── DataFrame builder ──────────────────────────────────────────────────────────
COL_DEFS = {
    "name":            ("Item",          lambda r: r.get("name","—")),
    "buy_price":       ("Buy",           lambda r: fmt_gp(r.get("buy_price"))),
    "sell_price":      ("Sell",          lambda r: fmt_gp(r.get("sell_price"))),
    "tax":             ("Tax",           lambda r: fmt_gp(r.get("tax"))),
    "profit_unit":     ("Profit/item",   lambda r: fmt_gp(r.get("profit_unit"))),
    "roi":             ("ROI %",         lambda r: f"{r.get('roi',0):.1f}%"),
    "buy_qty_hr":      ("Buy/hr",        lambda r: f"{int(r.get('buy_qty_hr',0)):,}"),
    "sell_qty_hr":     ("Sell/hr",       lambda r: f"{int(r.get('sell_qty_hr',0)):,}"),
    "daily_volume":    ("Daily Vol",     lambda r: fmt_gp(r.get("daily_volume"))),
    "ratio":           ("B/S",           lambda r: ratio_fmt(r.get("ratio"))),
    "fq_label":        ("Fill",          lambda r: fq_fmt(r.get("fq_label","No data"))),
    "ge_limit":        ("GE Lmt",        lambda r: f"{int(r.get('ge_limit',0)):,}"),
    "potential_profit":("Pot. Profit",   lambda r: fmt_gp(r.get("potential_profit"))),
    "adj_potential":   ("Adj. Potential",lambda r: fmt_gp(r.get("adj_potential"))),
    "realistic_profit":("Realistic 4hr", lambda r: fmt_gp(r.get("realistic_profit"))),
    "chg_1d":         ("1D %",          lambda r: "—" if r.get("chg_1d") is None else f"{r.get('chg_1d',0):+.1f}%"),
    "chg_7d":         ("7D %",          lambda r: "—" if r.get("chg_7d") is None else f"{r.get('chg_7d',0):+.1f}%"),
    "chg_30d":        ("30D %",         lambda r: "—" if r.get("chg_30d") is None else f"{r.get('chg_30d',0):+.1f}%"),
    "trend":          ("Trend",         lambda r: r.get("trend","Flat")),
}

def to_df(rows, col_keys):
    records = [
        {COL_DEFS[k][0]: COL_DEFS[k][1](r) for k in col_keys}
        for r in rows
    ]
    return pd.DataFrame(records)

# ── Row styler (axis=1) ────────────────────────────────────────────────────────
def make_styler(df, rows, col_keys):
    profit_label = COL_DEFS["profit_unit"][0]
    roi_label    = COL_DEFS["roi"][0]
    ratio_label  = COL_DEFS["ratio"][0]
    fq_label_col = COL_DEFS["fq_label"][0]
    ch1_label     = COL_DEFS["chg_1d"][0]
    ch7_label     = COL_DEFS["chg_7d"][0]
    ch30_label    = COL_DEFS["chg_30d"][0]
    trend_label   = COL_DEFS["trend"][0]

    profit_vals = [r.get("profit_unit", 0) for r in rows]
    roi_vals    = [r.get("roi", 0)         for r in rows]
    p_max = max(profit_vals) if profit_vals else 1

    cols = list(df.columns)

    def style_row(row):
        idx = row.name
        if idx >= len(rows):
            return [""] * len(cols)
        r       = rows[idx]
        pct     = profit_vals[idx] / p_max if p_max else 0
        roi_val = roi_vals[idx]
        ratio_v = r.get("ratio")
        fq_v    = r.get("fq_label", "No data")
        ch1_v   = r.get("chg_1d")
        ch7_v   = r.get("chg_7d")
        ch30_v  = r.get("chg_30d")
        tr_v    = r.get("trend", "Flat")
        result  = []
        for col in cols:
            if col == profit_label:
                if pct >= 0.7:   result.append("background:#052e16; color:#4ade80; font-weight:600")
                elif pct >= 0.4: result.append("background:#0f2d1a; color:#86efac")
                else:            result.append("")
            elif col == roi_label:
                if roi_val >= 20:   result.append("background:#1c1000; color:#fbbf24; font-weight:600")
                elif roi_val >= 10: result.append("background:#1a1200; color:#fde68a")
                elif roi_val >= 5:  result.append("background:#171400; color:#fef9c3")
                else:               result.append("")
            elif col == ratio_label:
                result.append(ratio_css(ratio_v))
            elif col == fq_label_col:
                result.append(fq_css(fq_v))
            elif col == ch1_label:
                result.append(pct_css(ch1_v))
            elif col == ch7_label:
                result.append(pct_css(ch7_v))
            elif col == ch30_label:
                result.append(pct_css(ch30_v))
            elif col == trend_label:
                result.append(trend_css(tr_v))
            else:
                result.append("")
        return result

    return df.style.apply(style_row, axis=1)

DARK_LAYOUT = dict(
    plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
    title_font_size=13, margin=dict(t=50, b=80, l=60, r=60),
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
    st.session_state["data"] = compute_flips(
        st.session_state.get("latest", {}),
        st.session_state.get("mapping", []),
        st.session_state.get("hour_vols", {}),
        st.session_state.get("fmin_vols", {}),
    )



# ── Header ────────────────────────────────────────────────────────────────────
h1, h2, h3 = st.columns([4, 3, 1])
with h1:
    st.markdown("## Owen's GE Tracker")
with h3:
    manual = st.button("Refresh", type="primary", use_container_width=True)

with st.spinner("Loading…"):
    load_mapping()
    if manual or stale("price_ts", PRICE_INTERVAL):
        do_prices()
    if manual or stale("volume_ts", VOLUME_INTERVAL):
        do_volumes()
    recompute()

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
        f"Prices: <b>{fmt_ago(p_ago)}</b> &nbsp;·&nbsp; "
        f"Volumes: <b>{fmt_ago(v_ago)}</b> &nbsp;·&nbsp; "
        f"<span style='color:#334155'>auto every 60s</span>"
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
t_sing, t_bulk, t_roi, t_watch, t_guide = st.tabs([
    "Singular / High Margin",
    "Bulk Flips",
    "High ROI",
    "Investment Watchlist",
    "Guide",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SINGULAR / HIGH MARGIN
# ═══════════════════════════════════════════════════════════════════════════════
with t_sing:
    s_n = st.selectbox("Show top", [10, 20, 30, 40], index=1, key="sing_n")
    display_sing = sorted(singular, key=lambda x: (-x.get("profit_unit",0), -x.get("fq_mult",0), -x.get("roi",0)))[:s_n]

    SING_COLS = ["name","buy_price","sell_price","tax","profit_unit","roi",
                 "buy_qty_hr","sell_qty_hr","ratio","fq_label","ge_limit","potential_profit"]
    df_s = to_df(display_sing, SING_COLS)
    st.dataframe(make_styler(df_s, display_sing, SING_COLS),
                 use_container_width=True, hide_index=True, height=520)

    st.markdown("<div class='section-label'>Profit per unit</div>", unsafe_allow_html=True)
    if display_sing:
        chart_s = display_sing[:15]
        fig_s = go.Figure(go.Bar(
            x=[r["name"] for r in chart_s],
            y=[r["profit_unit"] for r in chart_s],
            marker=dict(color=[r["roi"] for r in chart_s], colorscale="purples",
                        showscale=True, colorbar=dict(title="ROI %")),
            text=[fmt_gp(r["profit_unit"]) for r in chart_s],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Profit/item: %{text}<br>ROI: %{marker.color:.1f}%<extra></extra>",
        ))
        fig_s.update_layout(
            template="plotly_dark", **DARK_LAYOUT,
            xaxis_tickangle=-35, yaxis_title="Profit / item (gp)",
            title="Top 15 singular flips — post-tax profit per item",
        )
        st.plotly_chart(fig_s, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BULK FLIPS
# ═══════════════════════════════════════════════════════════════════════════════
with t_bulk:
    b_n = st.selectbox("Show top", [10, 20, 30, 40, 60], index=1, key="bulk_n")
    display_bulk = sorted(bulk, key=lambda x: (-x.get("profit_unit",0), -x.get("fq_mult",0), -x.get("ge_limit",0), -x.get("roi",0)))[:b_n]

    BULK_COLS = ["name","buy_price","sell_price","tax","profit_unit","ratio","fq_label","ge_limit",
                 "buy_qty_hr","sell_qty_hr","roi","realistic_profit"]
    df_b = to_df(display_bulk, BULK_COLS)
    st.dataframe(make_styler(df_b, display_bulk, BULK_COLS),
                 use_container_width=True, hide_index=True, height=560)

    st.caption("Bulk tab only includes items with real two-sided liquidity, sane B/S, enough sell-side activity to move size in 4 hours, and a minimum practical profit floor so trivial flips do not clutter the list.")

    st.markdown("<div class='section-label'>Best bulk candidates — ranked by profit/item first, then fill quality</div>", unsafe_allow_html=True)
    if display_bulk:
        chart_b = display_bulk[:15]
        fig_b = go.Figure(go.Bar(
            x=[r["name"] for r in chart_b],
            y=[r["realistic_profit"] for r in chart_b],
            marker=dict(color=[r["ratio"] if r.get("ratio") is not None else 0 for r in chart_b], colorscale="Viridis",
                        showscale=True, colorbar=dict(title="B/S")),
            text=[fmt_gp(r["realistic_profit"]) for r in chart_b],
            textposition="outside",
            customdata=[[fmt_gp(r["profit_unit"]), r["fq_label"], f'{r["ge_limit"]:,}'] for r in chart_b],
            hovertemplate="<b>%{x}</b><br>Realistic 4hr: %{text}<br>Profit/item: %{customdata[0]}<br>Fill: %{customdata[1]}<br>GE Limit: %{customdata[2]}<br>B/S: %{marker.color:.2f}<extra></extra>",
        ))
        fig_b.update_layout(
            template="plotly_dark", **DARK_LAYOUT,
            xaxis_tickangle=-35, yaxis_title="Realistic 4hr profit (gp)",
            title="Top 15 bulk flips — practical 4-hour profit",
        )
        st.plotly_chart(fig_b, use_container_width=True)

    st.markdown("<div class='section-label'>Bulk market landscape — volume vs profit/item</div>", unsafe_allow_html=True)
    if bulk:
        sc_data = pd.DataFrame([{
            "Item": r["name"], "Sell/hr": r["sell_qty_hr"],
            "Profit/item": r["profit_unit"], "GE Limit": r["ge_limit"], "ROI %": r["roi"],
        } for r in bulk[:40]])
        fig_sc = px.scatter(
            sc_data, x="Sell/hr", y="Profit/item",
            size="GE Limit", color="ROI %",
            hover_name="Item", color_continuous_scale="viridis",
            title="Bulk items — sell/hr vs profit/item (bubble = GE limit)",
            template="plotly_dark",
        )
        fig_sc.update_layout(
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
            title_font_size=13, margin=dict(t=50, b=50, l=60, r=60),
        )
        st.plotly_chart(fig_sc, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HIGH ROI
# ═══════════════════════════════════════════════════════════════════════════════
with t_roi:
    roi_n = st.selectbox("Show top", [10, 20, 30, 40], index=1, key="roi_n")
    display_roi = sorted(high_roi, key=lambda x: -x.get("roi", 0))[:roi_n]

    ROI_COLS = ["name","buy_price","sell_price","tax","profit_unit","roi",
                "daily_volume","ratio","fq_label","ge_limit","potential_profit"]
    df_r = to_df(display_roi, ROI_COLS)
    st.dataframe(make_styler(df_r, display_roi, ROI_COLS),
                 use_container_width=True, hide_index=True, height=500)

    st.markdown("<div class='section-label'>ROI % vs daily volume</div>", unsafe_allow_html=True)
    if high_roi:
        rsc = pd.DataFrame([{
            "Item": r["name"], "ROI %": r["roi"],
            "Daily Volume": r["daily_volume"], "Profit/item": r["profit_unit"],
        } for r in high_roi[:40]])
        fig_r = px.scatter(
            rsc, x="Daily Volume", y="ROI %",
            hover_name="Item", size="Profit/item",
            color="ROI %", color_continuous_scale="greens",
            title="High ROI — ROI % vs daily volume  (top-right = ideal)",
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
    if watch:
        trend_order = {"Pullback": 0, "Building": 1, "Extended": 2, "Flat": 3, "Weakening": 4}
        f1, f2 = st.columns([1, 4])
        with f1:
            trend_filter = st.selectbox("Trend filter", ["All", "Pullback", "Building", "Extended", "Flat", "Weakening"], index=0, key="watch_trend")
        display_watch = [r for r in watch if trend_filter == "All" or r.get("trend") == trend_filter]
        display_watch = sorted(display_watch, key=lambda r: (trend_order.get(r.get("trend", "Flat"), 9), -r.get("profit_unit", 0), -(r.get("chg_30d") or 0)
    ),
)
        WATCH_COLS = ["name", "trend", "chg_1d", "chg_7d", "chg_30d", "buy_price", "sell_price", "tax", "profit_unit", "roi",
                      "buy_qty_hr", "sell_qty_hr", "ratio", "fq_label", "ge_limit"]
        records = []
        for r in display_watch:
            row = {COL_DEFS[k][0]: COL_DEFS[k][1](r) for k in WATCH_COLS}
            row["Catalyst"] = WATCHLIST_CATALYSTS.get(r["name"], "")
            records.append(row)
        df_w_full = pd.DataFrame(records)
        cols_order = ["Item", "Trend", "1D %", "7D %", "30D %", "Catalyst"] + [c for c in df_w_full.columns if c not in ("Item", "Trend", "1D %", "7D %", "30D %", "Catalyst")]
        df_w_full = df_w_full[cols_order]

        profit_label = COL_DEFS["profit_unit"][0]
        roi_label    = COL_DEFS["roi"][0]
        ratio_label  = COL_DEFS["ratio"][0]
        fq_label_col = COL_DEFS["fq_label"][0]
        ch1_label    = COL_DEFS["chg_1d"][0]
        ch7_label    = COL_DEFS["chg_7d"][0]
        ch30_label   = COL_DEFS["chg_30d"][0]
        trend_label  = COL_DEFS["trend"][0]
        profit_vals  = [r.get("profit_unit", 0) for r in display_watch]
        roi_vals     = [r.get("roi", 0) for r in display_watch]
        p_max = max(profit_vals) if profit_vals else 1
        all_cols = list(df_w_full.columns)

        def style_watch(row):
            idx = row.name
            if idx >= len(display_watch):
                return [""] * len(all_cols)
            r       = display_watch[idx]
            pct     = profit_vals[idx] / p_max if p_max else 0
            roi_val = roi_vals[idx]
            ratio_v = r.get("ratio")
            fq_v    = r.get("fq_label", "No data")
            ch1_v   = r.get("chg_1d")
            ch7_v   = r.get("chg_7d")
            ch30_v  = r.get("chg_30d")
            tr_v    = r.get("trend", "Flat")
            result  = []
            for col in all_cols:
                if col == profit_label:
                    if pct >= 0.7:
                        result.append("background:#052e16; color:#4ade80; font-weight:600")
                    elif pct >= 0.4:
                        result.append("background:#0f2d1a; color:#86efac")
                    else:
                        result.append("")
                elif col == roi_label:
                    if roi_val >= 20:
                        result.append("background:#1c1000; color:#fbbf24; font-weight:600")
                    elif roi_val >= 10:
                        result.append("background:#1a1200; color:#fde68a")
                    elif roi_val >= 5:
                        result.append("background:#171400; color:#fef9c3")
                    else:
                        result.append("")
                elif col == ratio_label:
                    result.append(ratio_css(ratio_v))
                elif col == fq_label_col:
                    result.append(fq_css(fq_v))
                elif col == ch1_label:
                    result.append(pct_css(ch1_v))
                elif col == ch7_label:
                    result.append(pct_css(ch7_v))
                elif col == ch30_label:
                    result.append(pct_css(ch30_v))
                elif col == trend_label:
                    result.append(trend_css(tr_v))
                else:
                    result.append("")
            return result

        st.dataframe(
            df_w_full.style.apply(style_watch, axis=1),
            use_container_width=True, hide_index=True, height=620,
            column_config={
                "Catalyst": st.column_config.TextColumn("Catalyst", width="large"),
                "Item": st.column_config.TextColumn("Item", width="medium"),
                "Trend": st.column_config.TextColumn("Trend", width="small"),
                "1D %": st.column_config.TextColumn("1D %", width="small"),
                "7D %": st.column_config.TextColumn("7D %", width="small"),
                "30D %": st.column_config.TextColumn("30D %", width="small"),
            },
        )

        st.markdown("<div class='section-label'>Current profit/item by item</div>", unsafe_allow_html=True)
        fig_w = go.Figure(go.Bar(
            x=[r["name"] for r in display_watch],
            y=[r["profit_unit"] for r in display_watch],
            marker=dict(color=[r["roi"] for r in display_watch], colorscale="oranges",
                        showscale=True, colorbar=dict(title="ROI %")),
            text=[fmt_gp(r["profit_unit"]) for r in display_watch],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Profit/item: %{text}<br>ROI: %{marker.color:.1f}%<extra></extra>",
        ))
        fig_w.update_layout(
            template="plotly_dark", **DARK_LAYOUT,
            xaxis_tickangle=-25, yaxis_title="Profit / item (gp)",
            title="Investment watchlist — current post-tax spread",
        )
        st.plotly_chart(fig_w, use_container_width=True)

        st.markdown("<div class='section-label'>90-day price history</div>", unsafe_allow_html=True)
        select_source = display_watch if display_watch else watch
        selected = st.selectbox("Select item", [r["name"] for r in select_source], key="watch_item")
        sel_row  = next((r for r in select_source if r["name"] == selected), None)
        if sel_row:
            ts_data = fetch_timeseries(sel_row["id"], "24h")
            if ts_data:
                ts_df = pd.DataFrame(ts_data)
                ts_df["date"] = pd.to_datetime(ts_df["timestamp"], unit="s")
                avg_high = ts_df["avgHighPrice"].mean()
                avg_low  = ts_df["avgLowPrice"].mean()
                cur_buy  = sel_row.get("buy_price", 0)
                cur_sell = sel_row.get("sell_price", 0)

                fig_ts = go.Figure()
                fig_ts.add_trace(go.Scatter(x=ts_df["date"], y=ts_df["avgHighPrice"],
                                            name="Sell (high)", line=dict(color="#38bdf8")))
                fig_ts.add_trace(go.Scatter(x=ts_df["date"], y=ts_df["avgLowPrice"],
                                            name="Buy (low)",  line=dict(color="#818cf8")))
                fig_ts.add_hline(y=avg_high, line_dash="dot", line_color="#38bdf8",
                                 annotation_text=f"90d avg sell: {fmt_gp(avg_high)}",
                                 annotation_position="bottom right")
                fig_ts.add_hline(y=avg_low, line_dash="dot", line_color="#818cf8",
                                 annotation_text=f"90d avg buy: {fmt_gp(avg_low)}",
                                 annotation_position="top right")
                fig_ts.update_layout(
                    template="plotly_dark",
                    plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
                    title=f"{selected} — 90-day price history",
                    title_font_size=13, margin=dict(t=50, b=50, l=60, r=60),
                    yaxis_title="Price (gp)", xaxis_title="",
                )
                st.plotly_chart(fig_ts, use_container_width=True)

                if cur_buy < avg_low * 0.97:
                    st.success(f"Buy signal: current buy price ({fmt_gp(cur_buy)}) is >3% below 90-day avg ({fmt_gp(avg_low)}). Potential dip entry.")
                elif cur_sell > avg_high * 1.05:
                    st.warning(f"Elevated: current sell ({fmt_gp(cur_sell)}) is >5% above 90-day avg ({fmt_gp(avg_high)}). Possible spike — consider waiting for pullback.")
                else:
                    st.info(f"Neutral: prices within normal range of 90-day avg (buy avg: {fmt_gp(avg_low)}, sell avg: {fmt_gp(avg_high)}).")

                st.caption(WATCHLIST_CATALYSTS.get(selected, ""))
            else:
                st.info("No timeseries data available for this item right now.")
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
| Column | Meaning |
|---|---|
| Buy | Instasell — your offer price |
| Sell | Instabuy — your list price |
| Tax | min(sell × 2%, 5M GP) — seller pays |
| Profit/item | Sell − Buy − Tax |
| ROI % | (Profit ÷ Buy) × 100 |
| Buy/hr | Rolling 1hr high-price volume (/1h endpoint) |
| Sell/hr | Rolling 1hr low-price volume (/1h endpoint) |
| Daily Vol | (Buy/hr + Sell/hr) × 24 |
| B/S | Buy/hr ÷ Sell/hr |
| Fill | Fill quality derived from B/S |
| GE Lmt | Buy limit per 4-hour window |
| Pot. Profit | Profit/unit × full GE limit |
| Adj. Potential | Pot. Profit × fill quality multiplier |
| Realistic 4hr | Profit × min(GE limit, sell-side fills × 4); bulk tab also excludes thin, one-sided, and too-small-to-matter markets |
        """)

        st.markdown("### B/S Ratio")
        st.markdown("""
| B/S | Fill | Colour |
|---|---|---|
| 0.8–1.5 | Ideal | Green |
| 1.5–3.0 | High demand | Orange |
| >3.0 | Hard to buy | Red |
| 0.4–0.8 | Slight flood | Yellow |
| <0.4 | Flooded | Red |
        """)

    with gb:
        st.markdown("### Colour Coding in Tables")
        st.markdown("""
| Column | Colour | Threshold |
|---|---|---|
| Profit/item | Dark green | Top 70% of list |
| Profit/item | Mid green | Top 40–70% of list |
| ROI % | Gold bold | ≥ 20% |
| ROI % | Pale gold | 10–20% |
| ROI % | Pale yellow | 5–10% |
| B/S | Green | 0.8–1.5 (ideal) |
| B/S | Orange | 1.5–3.0 (high demand) |
| B/S | Yellow | 0.4–0.8 (slight flood) |
| B/S | Red | >3.0 or <0.4 |
        """)

        st.markdown("### Sorting note")
        st.markdown("""
- Tables are pre-ranked by dashboard logic for each tab
- Use the default ranking rather than clicking column headers for decision-making
- This preserves readable GP/K/M formatting and avoids Streamlit type-parsing issues
        """)

        st.markdown("### Refresh Schedule")
        st.markdown("""
| Data | Endpoint | Interval |
|---|---|---|
| Prices | /latest | Every 60s (auto) |
| Volumes | /1h + /5m fallback | Every 5 min (auto) |
| Item metadata | /mapping | Once at startup |
| Price history | /timeseries | On-demand (Watchlist) |
        """)

        st.markdown("### GE Tax (May 2025)")
        st.markdown("""
- 2% of sell price, charged to seller only
- Hard cap of 5,000,000 GP per transaction
- Items under 50 GP are exempt
- All figures in this dashboard are post-tax
        """)

        st.markdown("### Timing")
        st.markdown("""
| Window | ET | Action |
|---|---|---|
| Buy | 10 PM – 6 AM | Place buy orders at off-peak |
| Transition | 6 AM – 2 PM | Monitor and adjust |
| Sell | 2 PM – 10 PM | List sell orders at peak |
        """)

st.markdown("---")
st.markdown(
    "<div style='font-size:0.68rem;color:#334155;text-align:center'>"
    "OSRS Wiki Real-Time Prices API · 2% GE tax · 5M GP cap · "
    "Prices every 60s · Volumes every 5m · Fills not guaranteed"
    "</div>",
    unsafe_allow_html=True,
)