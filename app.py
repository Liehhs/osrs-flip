import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import pytz

from ge_api import (
    fetch_latest, fetch_mapping, fetch_volumes, fetch_timeseries,
    compute_flips, WATCHLIST_NAMES, WATCHLIST_CATALYSTS, SIGNALS_UNIVERSE,
)

st.set_page_config(
    page_title="Owen's GE Tracker",
    layout="wide",
    page_icon="\U0001f4c8",
    initial_sidebar_state="collapsed",
)

PRICE_INTERVAL  = 60
VOLUME_INTERVAL = 300
MAPPING_KEY     = "mapping_loaded"

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color:#0f172a; }
[data-testid="stHeader"]           { background-color:#0f172a; }
body,.stMarkdown,.stDataFrame,.stMetric { color:#e5e7eb!important; }
.block-container { padding-top:1rem; }
.stTabs [data-baseweb="tab-list"] { gap:6px; }
.stTabs [data-baseweb="tab"] {
    background-color:#1e293b; color:#94a3b8;
    border-radius:6px 6px 0 0; padding:6px 18px; font-size:.85rem;
}
.stTabs [aria-selected="true"] {
    background-color:#334155!important; color:#38bdf8!important; font-weight:600;
}
div[data-testid="metric-container"] {
    background:#1e293b; border:1px solid #334155;
    border-radius:8px; padding:10px 16px;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt_gp(n):
    if n is None: return "\u2014"
    try: n = int(n)
    except: return "\u2014"
    if abs(n) >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:     return f"{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:         return f"{n/1_000:.1f}K"
    return f"{n:,}"

def now_ts():   return time.time()
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
        return "green",  f"Sell window \u2014 US/EU peak overlap. Best time to exit positions. ({ts})"
    if 6  <= h < 14:
        return "yellow", f"Transition window \u2014 Moderate activity. Good for placing buy orders. ({ts})"
    return     "red",   f"Buy window \u2014 Off-peak. Place buy orders now, sell into afternoon. ({ts})"

def ratio_fmt(r): return "\u2014" if r is None else f"{r:.2f}"

def ratio_css(r):
    if r is None:           return "color:#64748b"
    if 0.8 <= r <= 1.5:    return "color:#4ade80"
    if 1.5 < r  <= 3.0:    return "color:#fb923c"
    if r > 3.0:             return "color:#f87171"
    if 0.4 <= r <  0.8:    return "color:#facc15"
    return "color:#f87171"

def fq_fmt(label):
    return {"Ideal":"Ideal","High demand":"High demand","Hard to buy":"Hard to buy",
            "Slight flood":"Slight flood","Flooded":"Flooded","No data":"\u2014"}.get(label, label)

def fq_css(label):
    return {"Ideal":"color:#4ade80","High demand":"color:#fb923c",
            "Hard to buy":"color:#f87171","Slight flood":"color:#facc15",
            "Flooded":"color:#f87171","No data":"color:#64748b"}.get(label, "")

def pct_css(v):
    if v is None:   return "color:#64748b"
    if v >= 10:     return "color:#22c55e; font-weight:600"
    if v >  0:      return "color:#86efac"
    if v <= -10:    return "color:#ef4444; font-weight:600"
    if v <  0:      return "color:#fca5a5"
    return "color:#cbd5e1"

def trend_css(t):
    return {"Pullback":"color:#facc15; font-weight:600",
            "Building":"color:#4ade80; font-weight:600",
            "Extended":"color:#fb923c; font-weight:600",
            "Weakening":"color:#ef4444; font-weight:600",
            "Flat":"color:#94a3b8"}.get(t, "")

def flag_css(flags):
    if flags == "Quiet":                          return "color:#64748b"
    if "Price shock" in flags or "Big move" in flags:
        return "color:#fbbf24; font-weight:600"
    if "Fat margin"  in flags or "High GP"  in flags:
        return "color:#4ade80; font-weight:600"
    return "color:#cbd5e1"


# ── COL_DEFS ───────────────────────────────────────────────────────────────────
COL_DEFS = {
    "name":             ("Item",           lambda r: r.get("name", "\u2014")),
    "buy_price":        ("Buy",            lambda r: fmt_gp(r.get("buy_price"))),
    "sell_price":       ("Sell",           lambda r: fmt_gp(r.get("sell_price"))),
    "tax":              ("Tax",            lambda r: fmt_gp(r.get("tax"))),
    "profit_unit":      ("Profit/item",    lambda r: fmt_gp(r.get("profit_unit"))),
    "roi":              ("ROI %",          lambda r: f"{r.get('roi',0):.1f}%"),
    "buy_qty_hr":       ("Buy/hr",         lambda r: f"{int(r.get('buy_qty_hr',0)):,}"),
    "sell_qty_hr":      ("Sell/hr",        lambda r: f"{int(r.get('sell_qty_hr',0)):,}"),
    "daily_volume":     ("Daily Vol",      lambda r: fmt_gp(r.get("daily_volume"))),
    "ratio":            ("B/S",            lambda r: ratio_fmt(r.get("ratio"))),
    "fq_label":         ("Fill",           lambda r: fq_fmt(r.get("fq_label","No data"))),
    "ge_limit":         ("GE Lmt",         lambda r: f"{int(r.get('ge_limit',0)):,}"),
    "potential_profit": ("Pot. Profit",    lambda r: fmt_gp(r.get("potential_profit"))),
    "adj_potential":    ("Adj. Potential", lambda r: fmt_gp(r.get("adj_potential"))),
    "realistic_profit": ("Realistic 4hr",  lambda r: fmt_gp(r.get("realistic_profit"))),
    "chg_1d":           ("1D %",           lambda r: "\u2014" if r.get("chg_1d")  is None else f"{r['chg_1d']:+.1f}%"),
    "chg_7d":           ("7D %",           lambda r: "\u2014" if r.get("chg_7d")  is None else f"{r['chg_7d']:+.1f}%"),
    "chg_30d":          ("30D %",          lambda r: "\u2014" if r.get("chg_30d") is None else f"{r['chg_30d']:+.1f}%"),
    "trend":            ("Trend",          lambda r: r.get("trend","Flat")),
    "flags":            ("Signals",        lambda r: r.get("flags","Quiet")),
    "signal_context":   ("Why to Watch",   lambda r: r.get("signal_context", r.get("candidate_reason",""))),
    "catalyst":         ("Catalyst",       lambda r: WATCHLIST_CATALYSTS.get(r.get("name",""), "")),
}

def to_df(rows, col_keys):
    return pd.DataFrame([
        {COL_DEFS[k][0]: COL_DEFS[k][1](r) for k in col_keys}
        for r in rows
    ])


# ── Styler ─────────────────────────────────────────────────────────────────────
def make_styler(df, rows, col_keys):
    labels = {k: COL_DEFS[k][0] for k in col_keys if k in COL_DEFS}
    profit_label  = labels.get("profit_unit")
    roi_label     = labels.get("roi")
    ratio_label   = labels.get("ratio")
    fq_col        = labels.get("fq_label")
    ch1_label     = labels.get("chg_1d")
    ch7_label     = labels.get("chg_7d")
    ch30_label    = labels.get("chg_30d")
    trend_label   = labels.get("trend")
    flags_label   = labels.get("flags")

    profit_vals = [r.get("profit_unit", 0) for r in rows]
    roi_vals    = [r.get("roi",         0) for r in rows]
    p_max       = max(profit_vals) if profit_vals else 1
    cols        = list(df.columns)

    def style_row(row):
        idx = row.name
        if idx >= len(rows):
            return [""] * len(cols)
        r       = rows[idx]
        pct     = profit_vals[idx] / p_max if p_max else 0
        roi_val = roi_vals[idx]
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
            elif col == ratio_label: result.append(ratio_css(r.get("ratio")))
            elif col == fq_col:      result.append(fq_css(r.get("fq_label","No data")))
            elif col == ch1_label:   result.append(pct_css(r.get("chg_1d")))
            elif col == ch7_label:   result.append(pct_css(r.get("chg_7d")))
            elif col == ch30_label:  result.append(pct_css(r.get("chg_30d")))
            elif col == trend_label: result.append(trend_css(r.get("trend","Flat")))
            elif col == flags_label: result.append(flag_css(r.get("flags","Quiet")))
            else: result.append("")
        return result

    return df.style.apply(style_row, axis=1)


DARK_LAYOUT = dict(
    plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
    font_color="#cbd5e1", title_font_size=13,
    margin=dict(t=50, b=80, l=60, r=60),
)


# ── Session / fetch ────────────────────────────────────────────────────────────
def stale(key, interval):
    last = st.session_state.get(key)
    return last is None or (now_ts() - last) >= interval

def load_mapping():
    if MAPPING_KEY not in st.session_state:
        st.session_state["mapping"] = fetch_mapping()
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
        st.session_state.get("latest",    {}),
        st.session_state.get("mapping",   []),
        st.session_state.get("hour_vols", {}),
        st.session_state.get("fmin_vols", {}),
    )


# ── Header ─────────────────────────────────────────────────────────────────────
h1, h2, h3 = st.columns([4, 3, 1])
with h1:
    st.markdown("## Owen's GE Tracker")
with h3:
    manual = st.button("Refresh", type="primary", use_container_width=True)

with st.spinner("Loading\u2026"):
    load_mapping()
    if manual or stale("price_ts", PRICE_INTERVAL):   do_prices()
    if manual or stale("volume_ts", VOLUME_INTERVAL): do_volumes()
    recompute()

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=PRICE_INTERVAL * 1000, key="ar")
except ImportError:
    pass

p_ago = secs_ago(st.session_state.get("price_ts"))
v_ago = secs_ago(st.session_state.get("volume_ts"))

_tw_color, _tw_msg = get_timing()
_cmap = {"green": "#22c55e", "yellow": "#facc15", "red": "#ef4444"}
with h2:
    st.markdown(
        f"<div style='background:#1e293b;border-left:4px solid {_cmap[_tw_color]};"
        f"padding:10px 14px;border-radius:6px;font-size:.85rem;color:#e5e7eb'>"
        f"{_tw_msg}</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Data guard ─────────────────────────────────────────────────────────────────
data = st.session_state.get("data")
if not data:
    st.warning("Waiting for data\u2026"); st.stop()

bulk, singular, high_roi, watch, signals, all_rows = data

# ── KPI bar ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Bulk Flips",      len(bulk))
k2.metric("Singular Flips",  len(singular))
k3.metric("High ROI",        len(high_roi))
k4.metric("Watchlist Items", len(watch))
k5.metric("Prices",          fmt_ago(p_ago))
k6.metric("Volumes",         fmt_ago(v_ago))

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_bulk, tab_sing, tab_roi, tab_watch, tab_sig = st.tabs([
    "Bulk", "Singular", "High ROI", "Investment Watchlist", "Signals",
])

# ---- Bulk ----
with tab_bulk:
    st.caption(f"High-volume bulk flips. Updated {fmt_ago(p_ago)}.")
    if bulk:
        cols = ["name","buy_price","sell_price","profit_unit","roi",
                "ge_limit","total_hr","fq_label","ratio","realistic_profit"]
        # total_hr not in COL_DEFS by key; map manually
        df = to_df(bulk, [c for c in cols if c in COL_DEFS])
        st.dataframe(make_styler(df, bulk, [c for c in cols if c in COL_DEFS]),
                     use_container_width=True, hide_index=True, height=520)
    else:
        st.info("No bulk flips found.")

# ---- Singular ----
with tab_sing:
    st.caption("Low GE-limit, high-value singular flips.")
    if singular:
        cols = ["name","buy_price","sell_price","profit_unit","roi",
                "ge_limit","fq_label","ratio","adj_potential"]
        df = to_df(singular, [c for c in cols if c in COL_DEFS])
        st.dataframe(make_styler(df, singular, [c for c in cols if c in COL_DEFS]),
                     use_container_width=True, hide_index=True, height=520)
    else:
        st.info("No singular flips found.")

# ---- High ROI ----
with tab_roi:
    st.caption("Best ROI % regardless of volume. Good for smaller bankrolls.")
    if high_roi:
        cols = ["name","buy_price","sell_price","profit_unit","roi",
                "fq_label","ratio","ge_limit"]
        df = to_df(high_roi, [c for c in cols if c in COL_DEFS])
        st.dataframe(make_styler(df, high_roi, [c for c in cols if c in COL_DEFS]),
                     use_container_width=True, hide_index=True, height=520)
    else:
        st.info("No high-ROI items found.")

# ---- Investment Watchlist ----
# Column order: Item | 1D% | 7D% | 30D% | Trend | Signals | ROI% | Buy | Sell | Sell/hr | Buy/hr | B/S
with tab_watch:
    st.caption(
        "Curated investment-grade items. Always shown. "
        "Sorted by trend activity \u2014 most active moves first."
    )
    if watch:
        watch_cols = [
            "name", "chg_1d", "chg_7d", "chg_30d",
            "trend", "flags", "roi",
            "buy_price", "sell_price", "sell_qty_hr", "buy_qty_hr", "ratio",
        ]
        # Augment rows with catalyst for display (shown via separate expander below table)
        df = to_df(watch, [c for c in watch_cols if c in COL_DEFS])
        st.dataframe(
            make_styler(df, watch, [c for c in watch_cols if c in COL_DEFS]),
            use_container_width=True, hide_index=True, height=600,
        )
        with st.expander("Catalyst notes"):
            for row in watch:
                cat = WATCHLIST_CATALYSTS.get(row["name"], "")
                st.markdown(f"**{row['name']}** \u2014 {cat}")
    else:
        st.info("No watchlist items found.")

# ---- Signals ----
# Column order: Item | 1D% | 7D% | 30D% | Trend | Signals | ROI% | Buy | Sell | Sell/hr | Buy/hr | B/S | Why to Watch
with tab_sig:
    st.caption(
        "Meta-sensitive items driven by game updates, dev blogs, hype and community discussion. "
        "Always shown. Update the 'Why to Watch' column in ge_api.py SIGNALS_UNIVERSE as events change."
    )
    if signals:
        sig_cols = [
            "name", "chg_1d", "chg_7d", "chg_30d",
            "trend", "flags", "roi",
            "buy_price", "sell_price", "sell_qty_hr", "buy_qty_hr", "ratio",
            "signal_context",
        ]
        df = to_df(signals, [c for c in sig_cols if c in COL_DEFS])
        st.dataframe(
            make_styler(df, signals, [c for c in sig_cols if c in COL_DEFS]),
            use_container_width=True, hide_index=True, height=600,
        )
    else:
        st.info("No signals items found.")