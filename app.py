import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import pytz

from ge_api import (
    fetch_latest, fetch_mapping, fetch_volumes, fetch_timeseries,
    compute_flips, build_shifts_data,
    WATCHLIST_NAMES, WATCHLIST_CATALYSTS, SIGNALS_UNIVERSE,
)

st.set_page_config(
    page_title="Owen's GE Tracker",
    layout="wide",
    page_icon="\U0001f4c8",
    initial_sidebar_state="collapsed",
)

PRICE_INTERVAL   = 60
VOLUME_INTERVAL  = 300
SHIFTS_INTERVAL  = 300   # 5 min — matches 5m bucket cadence for intraday
DAILY_INTERVAL   = 3600  # 1 hr is fine; daily timeseries updates once/day
MAPPING_KEY      = "mapping_loaded"

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
.section-header {
    font-size:1rem; font-weight:600; color:#94a3b8;
    letter-spacing:.06em; text-transform:uppercase;
    border-bottom:1px solid #334155; padding-bottom:6px;
    margin-top:1.4rem; margin-bottom:.5rem;
}
.sub-label {
    font-size:.78rem; color:#64748b; margin-bottom:4px;
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

def now_ts():     return time.time()
def secs_ago(ts): return int(now_ts() - ts) if ts else None
def fmt_ago(s):
    if s is None: return "never"
    if s < 60:    return f"{s}s ago"
    if s < 3600:  return f"{s//60}m {s%60}s ago"
    return f"{s//3600}h {(s%3600)//60}m ago"

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
    if r is None:        return "color:#64748b"
    if 0.8 <= r <= 1.5:  return "color:#4ade80"
    if 1.5 < r  <= 3.0:  return "color:#fb923c"
    if r > 3.0:          return "color:#f87171"
    if 0.4 <= r <  0.8:  return "color:#facc15"
    return "color:#f87171"

def fq_fmt(label):
    return {"Ideal":"Ideal","High demand":"High demand","Hard to buy":"Hard to buy",
            "Slight flood":"Slight flood","Flooded":"Flooded","No data":"\u2014"}.get(label, label)

def fq_css(label):
    return {"Ideal":"color:#4ade80","High demand":"color:#fb923c",
            "Hard to buy":"color:#f87171","Slight flood":"color:#facc15",
            "Flooded":"color:#f87171","No data":"color:#64748b"}.get(label, "")

def pct_css(v):
    if v is None:  return "color:#64748b"
    if v >= 10:    return "color:#22c55e; font-weight:600"
    if v >  0:     return "color:#86efac"
    if v <= -10:   return "color:#ef4444; font-weight:600"
    if v <  0:     return "color:#fca5a5"
    return "color:#cbd5e1"

def trend_css(t):
    return {"Pullback":"color:#facc15; font-weight:600",
            "Building":"color:#4ade80; font-weight:600",
            "Extended":"color:#fb923c; font-weight:600",
            "Weakening":"color:#ef4444; font-weight:600",
            "Flat":"color:#94a3b8"}.get(t, "")

def flag_css(flags):
    if flags == "Quiet":                                      return "color:#64748b"
    if "Price shock" in flags or "Big move" in flags:
        return "color:#fbbf24; font-weight:600"
    if "Fat margin"  in flags or "High GP"  in flags:
        return "color:#4ade80; font-weight:600"
    return "color:#cbd5e1"

def fmt_pct(v):
    if v is None: return "\u2014"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.2f}%"


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
    "fq_label":         ("Fill",          lambda r: fq_fmt(r.get("fq_label","No data"))),
    "ge_limit":         ("GE Lmt",         lambda r: f"{int(r.get('ge_limit',0)):,}"),
    "potential_profit": ("Pot. Profit",    lambda r: fmt_gp(r.get("potential_profit"))),
    "adj_potential":    ("Adj. Potential", lambda r: fmt_gp(r.get("adj_potential"))),
    "realistic_profit": ("Realistic 4hr",  lambda r: fmt_gp(r.get("realistic_profit"))),
    "chg_1d":           ("1D %",           lambda r: fmt_pct(r.get("chg_1d"))),
    "chg_7d":           ("7D %",           lambda r: fmt_pct(r.get("chg_7d"))),
    "chg_14d":          ("14D %",          lambda r: fmt_pct(r.get("chg_14d"))),
    "chg_30d":          ("30D %",          lambda r: fmt_pct(r.get("chg_30d"))),
    "chg_20m":          ("20m %",          lambda r: fmt_pct(r.get("chg_20m"))),
    "chg_40m":          ("40m %",          lambda r: fmt_pct(r.get("chg_40m"))),
    "chg_1h":           ("1h %",           lambda r: fmt_pct(r.get("chg_1h"))),
    "chg_6h":           ("6h %",           lambda r: fmt_pct(r.get("chg_6h"))),
    "chg_12h":          ("12h %",          lambda r: fmt_pct(r.get("chg_12h"))),
    "trend":            ("Trend",          lambda r: r.get("trend","Flat")),
    "flags":            ("Signals",        lambda r: r.get("flags","Quiet")),
    "signal_context":   ("Why to Watch",   lambda r: r.get("signal_context", r.get("candidate_reason",""))),
    "catalyst":         ("Catalyst",       lambda r: WATCHLIST_CATALYSTS.get(r.get("name",""), "")),
}

def to_df(rows, col_keys):
    valid = [k for k in col_keys if k in COL_DEFS]
    return pd.DataFrame([
        {COL_DEFS[k][0]: COL_DEFS[k][1](r) for k in valid}
        for r in rows
    ])


# ── Styler ─────────────────────────────────────────────────────────────────────
# All pct-change columns that should receive green/red coloring
_PCT_KEYS = {"chg_1d","chg_7d","chg_14d","chg_30d","chg_20m","chg_40m","chg_1h","chg_6h","chg_12h"}

def make_styler(df, rows, col_keys):
    valid  = [k for k in col_keys if k in COL_DEFS]
    labels = {k: COL_DEFS[k][0] for k in valid}
    profit_label = labels.get("profit_unit")
    roi_label    = labels.get("roi")
    ratio_label  = labels.get("ratio")
    fq_col       = labels.get("fq_label")
    trend_label  = labels.get("trend")
    flags_label  = labels.get("flags")
    pct_labels   = {labels[k]: k for k in valid if k in _PCT_KEYS}

    profit_vals = [r.get("profit_unit", 0) for r in rows]
    roi_vals    = [r.get("roi", 0)         for r in rows]
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
            elif col == trend_label: result.append(trend_css(r.get("trend","Flat")))
            elif col == flags_label: result.append(flag_css(r.get("flags","Quiet")))
            elif col in pct_labels:
                raw_key = pct_labels[col]
                # Strip the data key and fetch raw value for color decision
                v = r.get(raw_key)
                result.append(pct_css(v))
            else:
                result.append("")
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
    st.session_state["hour_vols"] = h
    st.session_state["fmin_vols"] = f
    st.session_state["volume_ts"] = now_ts()

def recompute():
    st.session_state["data"] = compute_flips(
        st.session_state.get("latest",    {}),
        st.session_state.get("mapping",   []),
        st.session_state.get("hour_vols", {}),
        st.session_state.get("fmin_vols", {}),
    )

def do_shifts(all_rows, mapping):
    ht, bulk = build_shifts_data(all_rows, mapping)
    st.session_state["shifts_ht"]   = ht
    st.session_state["shifts_bulk"] = bulk
    st.session_state["shifts_ts"]   = now_ts()


# ── Shared section-header renderer ────────────────────────────────────────────
def section_header(title):
    st.markdown(f"<div class='section-header'>{title}</div>", unsafe_allow_html=True)

def sub_label(text):
    st.markdown(f"<div class='sub-label'>{text}</div>", unsafe_allow_html=True)

def show_table(rows, col_keys, height=420):
    if not rows:
        st.info("No data available.")
        return
    valid = [k for k in col_keys if k in COL_DEFS]
    df = to_df(rows, valid)
    st.dataframe(make_styler(df, rows, valid),
                 use_container_width=True, hide_index=True, height=height)


# ── Shifts section renderer ────────────────────────────────────────────────────
def render_shifts_section(section_title, ht_rows, bulk_rows, sort_key, asc=False,
                           col_keys_ht=None, col_keys_bulk=None, updated_label=""):
    section_header(section_title)
    if updated_label:
        st.caption(updated_label)

    sub_label("High-Ticket Items  (sell price \u2265 3M)")
    if ht_rows:
        sorted_ht = sorted(ht_rows,
                           key=lambda r: (r.get(sort_key) is None,
                                          (r.get(sort_key) or 0) if asc else -(r.get(sort_key) or 0)))
        show_table(sorted_ht, col_keys_ht or [], height=380)
    else:
        st.info("No high-ticket data.")

    sub_label("Bulk Commodities  (prayers, herbs, logs, planks, bones, runes, etc.)")
    if bulk_rows:
        sorted_bulk = sorted(bulk_rows,
                             key=lambda r: (r.get(sort_key) is None,
                                            (r.get(sort_key) or 0) if asc else -(r.get(sort_key) or 0)))
        show_table(sorted_bulk, col_keys_bulk or [], height=380)
    else:
        st.info("No bulk commodity data.")


# ── Header ─────────────────────────────────────────────────────────────────────
_tw_color, _tw_msg = get_timing()
_cmap = {"green": "#22c55e", "yellow": "#facc15", "red": "#ef4444"}

col_title, col_banner, col_btn = st.columns([3, 5, 1])
with col_title:
    st.markdown("## Owen's GE Tracker")
with col_banner:
    st.markdown(
        f"<div style='background:#1e293b;border-left:4px solid {_cmap[_tw_color]};"
        f"padding:10px 14px;border-radius:6px;font-size:.85rem;color:#e5e7eb;margin-top:4px'>"
        f"{_tw_msg}</div>",
        unsafe_allow_html=True,
    )
with col_btn:
    manual = st.button("Refresh", type="primary", use_container_width=True)

# ── Data loading ───────────────────────────────────────────────────────────────
with st.spinner("Loading\u2026"):
    load_mapping()
    if manual or stale("price_ts",  PRICE_INTERVAL):  do_prices()
    if manual or stale("volume_ts", VOLUME_INTERVAL): do_volumes()
    recompute()

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=PRICE_INTERVAL * 1000, key="ar")
except ImportError:
    pass

p_ago = secs_ago(st.session_state.get("price_ts"))
v_ago = secs_ago(st.session_state.get("volume_ts"))

st.divider()

data = st.session_state.get("data")
if not data:
    st.warning("Waiting for data\u2026"); st.stop()

bulk_rows, singular, high_roi, watch, signals, all_rows = data

# ── KPI bar ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Bulk Flips",      len(bulk_rows))
k2.metric("Singular Flips",  len(singular))
k3.metric("High ROI",        len(high_roi))
k4.metric("Watchlist Items", len(watch))
k5.metric("Prices",          fmt_ago(p_ago))
k6.metric("Volumes",         fmt_ago(v_ago))

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_bulk, tab_sing, tab_roi, tab_shifts, tab_watch, tab_sig = st.tabs([
    "Bulk", "Singular", "High ROI", "Shifts", "Watchlist", "Signals",
])

# ───────────────────────── Bulk ──────────────────────────────────────────────
with tab_bulk:
    st.caption(f"High-volume bulk flips. Updated {fmt_ago(p_ago)}.")
    cols = ["name","buy_price","sell_price","profit_unit","roi",
            "ge_limit","fq_label","ratio","realistic_profit"]
    show_table(bulk_rows, cols, height=520)

# ───────────────────────── Singular ──────────────────────────────────────────
with tab_sing:
    st.caption("Low GE-limit, high-value singular flips.")
    cols = ["name","buy_price","sell_price","profit_unit","roi",
            "ge_limit","fq_label","ratio","adj_potential"]
    show_table(singular, cols, height=520)

# ───────────────────────── High ROI ──────────────────────────────────────────
with tab_roi:
    st.caption("Best ROI % regardless of volume.")
    cols = ["name","buy_price","sell_price","profit_unit","roi","fq_label","ratio","ge_limit"]
    show_table(high_roi, cols, height=520)

# ───────────────────────── Shifts ────────────────────────────────────────────
with tab_shifts:
    st.caption(
        "Price shift tracking across multiple time horizons. "
        "Intraday tables refresh every 5 min. Daily tables refresh every hour."
    )

    # Lazy-load shifts data (expensive — fetches timeseries per item)
    mapping = st.session_state.get("mapping", [])
    if stale("shifts_ts", SHIFTS_INTERVAL) or manual:
        with st.spinner("Fetching shift data (timeseries per item, takes ~15-30s)\u2026"):
            do_shifts(all_rows, mapping)

    shifts_ht   = st.session_state.get("shifts_ht",   [])
    shifts_bulk = st.session_state.get("shifts_bulk", [])
    shifts_ago  = fmt_ago(secs_ago(st.session_state.get("shifts_ts")))

    # Common column sets
    INTRADAY_COLS_HT   = ["name","chg_20m","chg_40m","chg_1h","chg_6h","chg_12h",
                           "roi","buy_price","sell_price","sell_qty_hr","buy_qty_hr","ratio","fq_label"]
    INTRADAY_COLS_BULK = ["name","chg_20m","chg_40m","chg_1h","chg_6h","chg_12h",
                          "roi","buy_price","sell_price","sell_qty_hr","buy_qty_hr","ratio","ge_limit"]
    DAILY_COLS_HT      = ["name","trend","flags","roi",
                           "buy_price","sell_price","sell_qty_hr","buy_qty_hr","ratio","fq_label"]
    DAILY_COLS_BULK    = ["name","trend","flags","roi",
                          "buy_price","sell_price","sell_qty_hr","buy_qty_hr","ratio","ge_limit"]

    # ── Section 1: Intraday ──────────────────────────────────────────────────
    render_shifts_section(
        "Section 1 \u2014 Intraday Price Shifts",
        shifts_ht, shifts_bulk,
        sort_key="chg_1h", asc=False,
        col_keys_ht   = INTRADAY_COLS_HT,
        col_keys_bulk = INTRADAY_COLS_BULK,
        updated_label = f"Updates every 5 min via 5m price buckets. Last updated: {shifts_ago}.",
    )

    # ── Section 2: 1D ───────────────────────────────────────────────────────
    _d1_cols_ht   = ["name","chg_1d"] + DAILY_COLS_HT[1:]
    _d1_cols_bulk = ["name","chg_1d"] + DAILY_COLS_BULK[1:]
    render_shifts_section(
        "Section 2 \u2014 1-Day Price Shifts",
        shifts_ht, shifts_bulk,
        sort_key="chg_1d", asc=False,
        col_keys_ht   = _d1_cols_ht,
        col_keys_bulk = _d1_cols_bulk,
        updated_label = f"Ranked by largest absolute 1D % move. Last updated: {shifts_ago}.",
    )

    # ── Section 3: 7D ───────────────────────────────────────────────────────
    _d7_cols_ht   = ["name","chg_7d"] + DAILY_COLS_HT[1:]
    _d7_cols_bulk = ["name","chg_7d"] + DAILY_COLS_BULK[1:]
    render_shifts_section(
        "Section 3 \u2014 7-Day Price Shifts",
        shifts_ht, shifts_bulk,
        sort_key="chg_7d", asc=False,
        col_keys_ht   = _d7_cols_ht,
        col_keys_bulk = _d7_cols_bulk,
        updated_label = f"Ranked by largest absolute 7D % move (rolling). Last updated: {shifts_ago}.",
    )

    # ── Section 4: 14D ──────────────────────────────────────────────────────
    _d14_cols_ht   = ["name","chg_14d"] + DAILY_COLS_HT[1:]
    _d14_cols_bulk = ["name","chg_14d"] + DAILY_COLS_BULK[1:]
    render_shifts_section(
        "Section 4 \u2014 14-Day Price Shifts",
        shifts_ht, shifts_bulk,
        sort_key="chg_14d", asc=False,
        col_keys_ht   = _d14_cols_ht,
        col_keys_bulk = _d14_cols_bulk,
        updated_label = f"Ranked by largest absolute 14D % move (rolling). Last updated: {shifts_ago}.",
    )

    # ── Section 5: 30D ──────────────────────────────────────────────────────
    _d30_cols_ht   = ["name","chg_30d"] + DAILY_COLS_HT[1:]
    _d30_cols_bulk = ["name","chg_30d"] + DAILY_COLS_BULK[1:]
    render_shifts_section(
        "Section 5 \u2014 30-Day Price Shifts",
        shifts_ht, shifts_bulk,
        sort_key="chg_30d", asc=False,
        col_keys_ht   = _d30_cols_ht,
        col_keys_bulk = _d30_cols_bulk,
        updated_label = f"Ranked by largest absolute 30D % move (rolling). Last updated: {shifts_ago}.",
    )

# ───────────────────────── Watchlist ─────────────────────────────────────────
with tab_watch:
    st.caption(
        "Curated investment-grade items. Always shown. "
        "Sorted by trend activity \u2014 most active moves first."
    )
    watch_cols = ["name","chg_1d","chg_7d","chg_30d","trend","flags",
                  "roi","buy_price","sell_price","sell_qty_hr","buy_qty_hr","ratio"]
    show_table(watch, watch_cols, height=600)
    with st.expander("Catalyst notes"):
        for row in watch:
            cat = WATCHLIST_CATALYSTS.get(row["name"], "")
            st.markdown(f"**{row['name']}** \u2014 {cat}")

# ───────────────────────── Signals ───────────────────────────────────────────
with tab_sig:
    st.caption(
        "Meta-sensitive items driven by game updates, dev blogs, hype and community discussion. "
        "Always shown. Update SIGNALS_UNIVERSE in ge_api.py as events change."
    )
    sig_cols = ["name","chg_1d","chg_7d","chg_30d","trend","flags",
                "roi","buy_price","sell_price","sell_qty_hr","buy_qty_hr","ratio","signal_context"]
    show_table(signals, sig_cols, height=600)