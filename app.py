import streamlit as st
import pandas as pd
from datetime import datetime
import time
import pytz

from ge_api import (
    fetch_latest, fetch_mapping, fetch_volumes, fetch_timeseries,
    compute_flips, build_shifts_data,
    WATCHLIST_NAMES, WATCHLIST_CATALYSTS, WATCHLIST_CATEGORY, SIGNALS_UNIVERSE,
)

st.set_page_config(
    page_title="Owen's GE Tracker",
    layout="wide",
    page_icon="\U0001f4c8",
    initial_sidebar_state="collapsed",
)

PRICE_INTERVAL  = 60
VOLUME_INTERVAL = 300
SHIFTS_INTERVAL = 300
MAPPING_KEY     = "mapping_loaded"

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color:#0f172a; }
[data-testid="stHeader"]           { background-color:#0f172a; }
body,.stMarkdown,.stDataFrame,.stMetric { color:#e5e7eb!important; }
.block-container { padding-top:1.5rem !important; padding-bottom:2rem; }
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
    font-size:.88rem; font-weight:700; color:#94a3b8;
    letter-spacing:.08em; text-transform:uppercase;
    border-bottom:1px solid #334155; padding-bottom:6px;
    margin-top:1.8rem; margin-bottom:.5rem;
}
.sub-label {
    font-size:.74rem; color:#64748b; margin-bottom:3px; margin-top:.5rem;
}
.pair-label {
    font-size:.74rem; font-weight:600; letter-spacing:.07em; text-transform:uppercase;
    padding:3px 8px; border-radius:4px; margin-bottom:4px; display:inline-block;
}
.pair-label-gain { background:#052e16; color:#4ade80; }
.pair-label-loss { background:#2d0a0a; color:#f87171; }
.mover-strip {
    background:#1e293b; border:1px solid #334155; border-radius:8px;
    padding:12px 16px; margin-bottom:1rem;
}
.mover-strip-title {
    font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
    color:#38bdf8; margin-bottom:8px;
}
.mover-row { display:flex; gap:8px; flex-wrap:wrap; }
.mover-chip {
    background:#0f172a; border:1px solid #334155; border-radius:6px;
    padding:5px 10px; display:inline-flex; flex-direction:column;
    min-width:110px; max-width:160px;
}
.mc-name  { font-size:.75rem; color:#cbd5e1; font-weight:600;
            white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.mc-pos   { font-size:.88rem; font-weight:700; color:#4ade80; }
.mc-neg   { font-size:.88rem; font-weight:700; color:#f87171; }
.mc-neu   { font-size:.88rem; font-weight:700; color:#94a3b8; }
.mc-price { font-size:.68rem; color:#64748b; margin-top:1px; }
/* Trend legend */
.legend-box {
    background:#1e293b; border:1px solid #334155; border-radius:8px;
    padding:10px 16px; margin-bottom:1rem; display:flex; gap:20px; flex-wrap:wrap;
}
.legend-item { display:flex; align-items:center; gap:8px; }
.legend-badge {
    font-size:.72rem; font-weight:700; padding:2px 7px; border-radius:4px;
    white-space:nowrap;
}
.lb-extended  { background:#1c1000; color:#fb923c; }
.lb-building  { background:#052e16; color:#4ade80; }
.lb-pullback  { background:#1c1a00; color:#facc15; }
.lb-weakening { background:#2d0a0a; color:#f87171; }
.lb-flat      { background:#1e293b; color:#94a3b8; border:1px solid #334155; }
.legend-desc  { font-size:.75rem; color:#94a3b8; }
/* Watchlist category badge */
.cat-badge {
    font-size:.68rem; font-weight:600; padding:1px 6px; border-radius:3px;
    background:#0f172a; border:1px solid #334155; color:#64748b;
    white-space:nowrap;
}
/* Signal type badges */
.sig-game-update   { background:#1c1000; color:#fb923c; }
.sig-meta-shift    { background:#0c1a2e; color:#38bdf8; }
.sig-boss-demand   { background:#1a1200; color:#fde68a; }
.sig-supply-shock  { background:#2d0a0a; color:#f87171; }
.sig-community     { background:#1a0c2e; color:#c084fc; }
.sig-pvp-meta      { background:#2d1a0a; color:#fdba74; }
.sig-new-content   { background:#052e16; color:#4ade80; }
.status-active   { font-size:.68rem; font-weight:700; color:#f87171; }
.status-watch    { font-size:.68rem; font-weight:700; color:#facc15; }
.status-cooling  { font-size:.68rem; font-weight:700; color:#94a3b8; }
</style>
""", unsafe_allow_html=True)


# -- Helpers ------------------------------------------------------------------
def fmt_gp(n):
    if n is None: return "--"
    try: n = int(n)
    except: return "--"
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
        return "green",  f"Sell window -- US/EU peak overlap. Best time to exit positions. ({ts})"
    if 6  <= h < 14:
        return "yellow", f"Transition window -- Moderate activity. Good for placing buy orders. ({ts})"
    return     "red",   f"Buy window -- Off-peak. Place buy orders now, sell into afternoon. ({ts})"

def ratio_fmt(r): return "--" if r is None else f"{r:.2f}"

def ratio_css(r):
    if r is None:       return "color:#64748b"
    if 0.8 <= r <= 1.5: return "color:#4ade80"
    if 1.5 < r  <= 3.0: return "color:#fb923c"
    if r > 3.0:         return "color:#f87171"
    if 0.4 <= r <  0.8: return "color:#facc15"
    return "color:#f87171"

def fq_fmt(label):
    return {"Ideal":"Ideal","High demand":"High demand","Hard to buy":"Hard to buy",
            "Slight flood":"Slight flood","Flooded":"Flooded","No data":"--"}.get(label, label)

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
    if flags == "Quiet":                               return "color:#64748b"
    if "Price shock" in flags or "Big move" in flags:  return "color:#fbbf24; font-weight:600"
    if "Fat margin"  in flags or "High GP"  in flags:  return "color:#4ade80; font-weight:600"
    return "color:#cbd5e1"

def fmt_pct(v):
    if v is None: return "--"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.2f}%"


# -- COL_DEFS (non-shifts tabs) -----------------------------------------------
COL_DEFS = {
    "name":             ("Item",           lambda r: r.get("name", "--")),
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
    "signal_context":   ("Signal",         lambda r: r.get("signal_context","")),
    "category":         ("Source",         lambda r: r.get("category","")),
}

_PCT_KEYS = {"chg_1d","chg_7d","chg_14d","chg_30d","chg_20m","chg_40m","chg_1h","chg_6h","chg_12h"}

def to_df_generic(rows, col_keys):
    valid = [k for k in col_keys if k in COL_DEFS]
    return pd.DataFrame([
        {COL_DEFS[k][0]: COL_DEFS[k][1](r) for k in valid}
        for r in rows
    ])

def make_styler_generic(df, rows, col_keys):
    valid        = [k for k in col_keys if k in COL_DEFS]
    labels       = {k: COL_DEFS[k][0] for k in valid}
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
        if idx >= len(rows): return [""] * len(cols)
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
                result.append(pct_css(r.get(pct_labels[col])))
            else:
                result.append("")
        return result

    return df.style.apply(style_row, axis=1)

def show_table(rows, col_keys, height=420):
    if not rows:
        st.info("No data available.")
        return
    valid = [k for k in col_keys if k in COL_DEFS]
    df = to_df_generic(rows, valid)
    st.dataframe(make_styler_generic(df, rows, valid),
                 use_container_width=True, hide_index=True, height=height)


# -- Trend legend -------------------------------------------------------------
def render_trend_legend():
    st.markdown("""
<div class='legend-box'>
  <div class='legend-item'>
    <span class='legend-badge lb-extended'>Extended</span>
    <span class='legend-desc'>Strong multi-week uptrend still accelerating -- price up 30D, 7D, and 1D</span>
  </div>
  <div class='legend-item'>
    <span class='legend-badge lb-building'>Building</span>
    <span class='legend-desc'>Steady uptrend forming -- positive 30D base, holding gains short-term</span>
  </div>
  <div class='legend-item'>
    <span class='legend-badge lb-pullback'>Pullback</span>
    <span class='legend-desc'>Was rising long-term but now pulling back short-term -- potential re-entry</span>
  </div>
  <div class='legend-item'>
    <span class='legend-badge lb-weakening'>Weakening</span>
    <span class='legend-desc'>Falling on both 30D and 7D horizons -- avoid or wait for reversal signal</span>
  </div>
  <div class='legend-item'>
    <span class='legend-badge lb-flat'>Flat</span>
    <span class='legend-desc'>No meaningful directional trend -- sideways price action</span>
  </div>
</div>
""", unsafe_allow_html=True)


# -- Shifts table builder -----------------------------------------------------
# Columns: Item | % Shift (with prev price) | Trend | Current Price | B/S

def build_shift_df(rows, pct_key, prev_key, pct_label):
    records = []
    for r in rows:
        v    = r.get(pct_key)
        prev = r.get(prev_key)
        cur  = r.get("sell_price")
        # % Shift -- plain percentage
        if v is not None:
            sign = "+" if v > 0 else ""
            pct_str = f"{sign}{v:.2f}%"
        else:
            pct_str = "--"
        # Price -- current + GP delta in parentheses
        cur_fmt = fmt_gp(cur)
        if cur and prev and cur != prev:
            delta     = cur - prev
            sign      = "+" if delta >= 0 else ""
            delta_fmt = f"{sign}{fmt_gp(delta)}"
            price_str = f"{cur_fmt} ({delta_fmt})"
        else:
            price_str = cur_fmt
        records.append({
            "Item":    r.get("name", "--"),
            pct_label: pct_str,
            "Trend":   r.get("trend", "Flat"),
            "Price":   price_str,
            "B/S":     ratio_fmt(r.get("ratio")),
        })
    return pd.DataFrame(records)

def style_shift_df(df, rows, pct_key, pct_label):
    cols = list(df.columns)
    def style_row(row):
        idx = row.name
        if idx >= len(rows): return [""] * len(cols)
        r = rows[idx]
        result = []
        for col in cols:
            if col == pct_label:
                result.append(pct_css(r.get(pct_key)))
            elif col == "Trend":
                result.append(trend_css(r.get("trend", "Flat")))
            elif col == "B/S":
                result.append(ratio_css(r.get("ratio")))
            else:
                result.append("")
        return result
    return df.style.apply(style_row, axis=1)

def show_split_tables(rows, pct_key, prev_key, pct_label, pool_label, height=340):
    gainers   = sorted([r for r in rows if (r.get(pct_key) or 0) > 0],
                       key=lambda r: r.get(pct_key) or 0, reverse=True)
    decliners = sorted([r for r in rows if (r.get(pct_key) or 0) < 0],
                       key=lambda r: r.get(pct_key) or 0)

    col_l, col_r = st.columns(2, gap="medium")
    with col_l:
        st.markdown(f"<span class='pair-label pair-label-gain'>{pool_label} -- Gainers</span>",
                    unsafe_allow_html=True)
        if gainers:
            df = build_shift_df(gainers, pct_key, prev_key, pct_label)
            st.dataframe(style_shift_df(df, gainers, pct_key, pct_label),
                         use_container_width=True, hide_index=True, height=height)
        else:
            st.caption("No gainers in this window.")

    with col_r:
        st.markdown(f"<span class='pair-label pair-label-loss'>{pool_label} -- Decliners</span>",
                    unsafe_allow_html=True)
        if decliners:
            df = build_shift_df(decliners, pct_key, prev_key, pct_label)
            st.dataframe(style_shift_df(df, decliners, pct_key, pct_label),
                         use_container_width=True, hide_index=True, height=height)
        else:
            st.caption("No decliners in this window.")


# -- Top Movers strip ---------------------------------------------------------
def _chip(name, v, sell):
    if v is None: return ""
    sign  = "+" if v > 0 else ""
    cls   = "mc-pos" if v > 0 else ("mc-neg" if v < 0 else "mc-neu")
    short = name if len(name) <= 22 else name[:20] + ".."
    return (
        f"<div class='mover-chip'>"
        f"<span class='mc-name' title='{name}'>{short}</span>"
        f"<span class='{cls}'>{sign}{v:.2f}%</span>"
        f"<span class='mc-price'>{sell}</span>"
        f"</div>"
    )

def render_top_movers(ht_rows, bulk_rows):
    all_items = list({r["id"]: r for r in ht_rows + bulk_rows}.values())
    periods = [
        ("20m",  "chg_20m"),
        ("40m",  "chg_40m"),
        ("1h",   "chg_1h"),
        ("6h",   "chg_6h"),
        ("12h",  "chg_12h"),
        ("1D",   "chg_1d"),
        ("7D",   "chg_7d"),
        ("14D",  "chg_14d"),
        ("30D",  "chg_30d"),
    ]
    st.markdown("<div class='section-header'>Top Movers -- Biggest Shifts at a Glance</div>",
                unsafe_allow_html=True)
    st.caption("Top 3 absolute % movers (combined high-ticket + bulk) per time window.")

    def _render_row(period_list):
        cols = st.columns(len(period_list))
        for col, (label, key) in zip(cols, period_list):
            with col:
                valid = [r for r in all_items if r.get(key) is not None]
                top3  = sorted(valid, key=lambda r: abs(r.get(key) or 0), reverse=True)[:3]
                chips = "".join([_chip(r["name"], r.get(key), fmt_gp(r.get("sell_price")))
                                 for r in top3])
                st.markdown(
                    f"<div class='mover-strip'>"
                    f"<div class='mover-strip-title'>{label}</div>"
                    f"<div class='mover-row'>"
                    f"{chips if chips else '<span style=\"color:#64748b;font-size:.75rem\">No data</span>'}"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

    st.markdown("<div class='sub-label'>Intraday</div>", unsafe_allow_html=True)
    _render_row(periods[:5])
    st.markdown("<div class='sub-label'>Daily</div>", unsafe_allow_html=True)
    _render_row(periods[5:])


# -- Shifts section -----------------------------------------------------------
def render_shifts_section(section_title, ht_rows, bulk_rows,
                          pct_key, prev_key, pct_label, updated_label=""):
    st.markdown(f"<div class='section-header'>{section_title}</div>", unsafe_allow_html=True)
    if updated_label:
        st.caption(updated_label)

    st.markdown("<div class='sub-label'>High-Ticket Items  (sell price >= 3M)</div>",
                unsafe_allow_html=True)
    show_split_tables(ht_rows, pct_key, prev_key, pct_label, "High-Ticket", height=340)

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-label'>Bulk Commodities</div>", unsafe_allow_html=True)
    show_split_tables(bulk_rows, pct_key, prev_key, pct_label, "Bulk", height=340)


# -- Watchlist renderer -------------------------------------------------------
RAID_CATS  = {"CoX", "ToB", "ToA", "Nightmare", "Raids/FA"}
BOSS_CATS  = {"Nex", "DT2", "GWD", "Zulrah", "Cerberus", "Dagannoth",
              "Varlamore", "Specialist", "Accessories"}
CLUE_CATS  = {"Clue"}
MIN_PRICE      = 1_000_000  # 1M floor for boss/raid
CLUE_MIN_PRICE = 500_000    # 500K floor for clue items

def _tracker_card(label, rows, floor=None):
    """Render a rolling 7D aggregate tracker card for a group of items."""
    if floor is None:
        floor = MIN_PRICE
    valid = [r for r in rows if (r.get("sell_price") or 0) >= floor]
    total_now  = sum(r.get("sell_price") or 0 for r in valid)
    total_prev = sum(
        (r.get("sell_price") or 0) / (1 + (r.get("chg_7d") or 0) / 100)
        for r in valid if r.get("chg_7d") is not None
    )
    if total_prev > 0:
        pct    = (total_now - total_prev) / total_prev * 100
        delta  = total_now - total_prev
        sign   = "+" if pct >= 0 else ""
        d_sign = "+" if delta >= 0 else ""
        pct_str   = f"{sign}{pct:.2f}%"
        delta_str = f"({d_sign}{fmt_gp(int(delta))})"
        color     = "#4ade80" if pct >= 0 else "#f87171"
        shift_html = (
            f"<span style='font-size:1.05rem; font-weight:700; color:{color};'>"
            f"{pct_str}</span>&nbsp;"
            f"<span style='font-size:.82rem; color:#94a3b8;'>{delta_str}</span>"
        )
    else:
        shift_html = "<span style='color:#64748b'>No data</span>"

    total_val_str = fmt_gp(int(total_now))

    st.markdown(
        f"<div style='background:#1e293b; border:1px solid #334155; border-radius:8px;"
        f"padding:12px 16px;'>"
        f"<div style='font-size:.72rem; font-weight:700; letter-spacing:.09em;"
        f"text-transform:uppercase; color:#64748b; margin-bottom:6px;'>{label}</div>"
        f"<div>{shift_html}</div>"
        f"<div style='font-size:.75rem; color:#94a3b8; margin-top:5px;'>"
        f"Total value: <span style='color:#e2e8f0; font-weight:600;'>{total_val_str}</span>"
        f"</div>"
        f"<div style='font-size:.68rem; color:#475569; margin-top:2px;'>"
        f"{len(valid)} tracked items</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

def _show_watchlist_table(rows, floor=None):
    if floor is None:
        floor = MIN_PRICE
    filtered = [r for r in rows if (r.get("sell_price") or 0) >= floor]
    if not filtered:
        st.caption("No items at or above 1M currently.")
        return
    df = pd.DataFrame([{
        "Item":   r.get("name", "--"),
        "Source": r.get("category", "--"),
        "1D %":   fmt_pct(r.get("chg_1d")),
        "7D %":   fmt_pct(r.get("chg_7d")),
        "14D %":  fmt_pct(r.get("chg_14d")),
        "30D %":  fmt_pct(r.get("chg_30d")),
        "Trend":  r.get("trend", "Flat"),
        "Price":  fmt_gp(r.get("sell_price")),
        "B/S":    ratio_fmt(r.get("ratio")),
    } for r in filtered])
    cols = list(df.columns)
    def style_wl(row):
        idx = row.name
        if idx >= len(filtered): return [""] * len(cols)
        r = filtered[idx]
        result = []
        for col in cols:
            if col in ("1D %", "7D %", "14D %", "30D %"):
                key = {"1D %": "chg_1d", "7D %": "chg_7d",
                       "14D %": "chg_14d", "30D %": "chg_30d"}[col]
                result.append(pct_css(r.get(key)))
            elif col == "Trend":
                result.append(trend_css(r.get("trend", "Flat")))
            elif col == "B/S":
                result.append(ratio_css(r.get("ratio")))
            elif col == "Source":
                result.append("color:#64748b; font-size:.78rem")
            else:
                result.append("")
        return result
    height = min(60 + len(filtered) * 36, 640)
    st.dataframe(df.style.apply(style_wl, axis=1),
                 use_container_width=True, hide_index=True, height=height)

def render_watchlist(watch):
    if not watch:
        st.info("No watchlist data.")
        return

    raid_items = [r for r in watch if r.get("category", "") in RAID_CATS]
    boss_items = [r for r in watch if r.get("category", "") in BOSS_CATS]
    clue_items = [r for r in watch if r.get("category", "") in CLUE_CATS]

    # -- 3 aggregate tracker cards --
    render_trend_legend()
    st.markdown("<div class='section-header'>7-Day Aggregate Trackers</div>",
                unsafe_allow_html=True)
    st.caption(
        "Rolling 7D change across all 1M+ items in each category. "
        "Rising = players are farming that content more. Falling = less activity or oversupply."
    )
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1: _tracker_card("Raid Uniques", raid_items)
    with c2: _tracker_card("Boss Uniques", boss_items)
    with c3: _tracker_card("Clue Uniques", clue_items, floor=CLUE_MIN_PRICE)
    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Raid Uniques</div>", unsafe_allow_html=True)
    st.caption("CoX / ToB / ToA / Nightmare / Raids/FA -- multi-mechanic raid drops.")
    _show_watchlist_table(raid_items)

    st.markdown("<div class='section-header'>Boss Uniques</div>", unsafe_allow_html=True)
    st.caption("Nex, DT2, GWD, Zulrah, Cerberus, Dagannoth, Varlamore, and other single-boss drops.")
    _show_watchlist_table(boss_items)

    st.markdown("<div class='section-header'>Clue Uniques</div>", unsafe_allow_html=True)
    st.caption("High-demand clue scroll rewards (500K+). Fixed supply -- price driven entirely by demand.")
    _show_watchlist_table(clue_items, floor=CLUE_MIN_PRICE)


# -- Signals renderer ---------------------------------------------------------
SIG_TYPE_CSS = {
    "game update":    "sig-game-update",
    "meta shift":     "sig-meta-shift",
    "boss demand":    "sig-boss-demand",
    "supply shock":   "sig-supply-shock",
    "community hype": "sig-community",
    "pvp meta":       "sig-pvp-meta",
    "new content":    "sig-new-content",
    "raids prep":     "sig-new-content",
    "price risk":     "sig-supply-shock",
}

# Type label display mapping -- human-readable
SIG_TYPE_DISPLAY = {
    "game update":    "Game Update",
    "meta shift":     "Meta Shift",
    "boss demand":    "Boss Demand",
    "supply shock":   "Supply/Risk",
    "community hype": "Community",
    "pvp meta":       "PvP Meta",
    "new content":    "New Content",
    "raids prep":     "Raids Prep",
    "price risk":     "Price Risk",
}

def render_signals_legend():
    st.markdown("""
<div class='legend-box'>
  <div class='legend-item'>
    <span class='legend-badge' style='background:#1c1000;color:#fb923c;'>Game Update</span>
    <span class='legend-desc'>Item directly affected by a patch, buff, or nerf</span>
  </div>
  <div class='legend-item'>
    <span class='legend-badge' style='background:#0c1a2e;color:#38bdf8;'>Meta Shift</span>
    <span class='legend-desc'>Item reacting to a change in how players are building or fighting</span>
  </div>
  <div class='legend-item'>
    <span class='legend-badge' style='background:#1a1200;color:#fde68a;'>Boss Demand</span>
    <span class='legend-desc'>Item tied to boss popularity or activity shifts</span>
  </div>
  <div class='legend-item'>
    <span class='legend-badge' style='background:#2d0a0a;color:#f87171;'>Supply/Risk</span>
    <span class='legend-desc'>Fixed or tightening supply, or a downside risk to current price</span>
  </div>
  <div class='legend-item'>
    <span class='legend-badge' style='background:#052e16;color:#4ade80;'>Raids Prep</span>
    <span class='legend-desc'>Demand rising as players gear up for an upcoming raid</span>
  </div>
  <div class='legend-item'>
    <span class='legend-badge' style='background:#2d1a0a;color:#fdba74;'>PvP Meta</span>
    <span class='legend-desc'>Item reacting to PvP tournament, tournament, or wilderness meta</span>
  </div>
  <div class='legend-item'>
    <span class='legend-badge' style='background:#1a0c2e;color:#c084fc;'>Community</span>
    <span class='legend-desc'>Streamer, Reddit, or community hype driving demand</span>
  </div>
  <div style='margin-top:6px; width:100%; border-top:1px solid #334155; padding-top:8px;'>
    <span style='font-size:.72rem; font-weight:700; color:#64748b; margin-right:10px;'>STATUS:</span>
    <span class='legend-badge' style='background:#2d0a0a;color:#f87171;'>ACTIVE</span>
    <span class='legend-desc' style='margin-right:12px;'>Live catalyst now</span>
    <span class='legend-badge' style='background:#1c1a00;color:#facc15;'>WATCH</span>
    <span class='legend-desc' style='margin-right:12px;'>Upcoming or uncertain</span>
    <span class='legend-badge' style='background:#1e293b;color:#94a3b8;border:1px solid #334155;'>COOLING</span>
    <span class='legend-desc'>Catalyst fading -- monitor only</span>
  </div>
</div>
""", unsafe_allow_html=True)

def render_signals(signals):
    if not signals:
        st.info("No signals data.")
        return

    render_signals_legend()

    records = []
    for r in signals:
        raw = r.get("signal_context", "")
        parts = [p.strip() for p in raw.split("|")]
        raw_type   = parts[0].strip().lower() if len(parts) > 0 else ""
        sig_status = parts[1].strip()         if len(parts) > 1 else ""
        sig_reason = parts[2].strip()         if len(parts) > 2 else ""
        display_type = SIG_TYPE_DISPLAY.get(raw_type, parts[0].strip() if parts else "")
        records.append({
            "_row":       r,
            "name":       r.get("name", ""),
            "raw_type":   raw_type,
            "type":       display_type,
            "status":     sig_status,
            "reason":     sig_reason,
            "trend":      r.get("trend", "Flat"),
            "chg_1d":     r.get("chg_1d"),
            "chg_7d":     r.get("chg_7d"),
            "chg_30d":    r.get("chg_30d"),
            "sell_price": r.get("sell_price"),
            "ratio":      r.get("ratio"),
        })

    df = pd.DataFrame([{
        "Item":    rec["name"],
        "Type":    rec["type"],
        "Status":  rec["status"],
        "Reason":  rec["reason"],
        "Trend":   rec["trend"],
        "1D %":    fmt_pct(rec["chg_1d"]),
        "7D %":    fmt_pct(rec["chg_7d"]),
        "30D %":   fmt_pct(rec["chg_30d"]),
        "Price":   fmt_gp(rec["sell_price"]),
        "B/S":     ratio_fmt(rec["ratio"]),
    } for rec in records])

    cols = list(df.columns)

    TYPE_BG = {
        "game update":    ("background:#1c1000", "color:#fb923c"),
        "meta shift":     ("background:#0c1a2e", "color:#38bdf8"),
        "boss demand":    ("background:#1a1200", "color:#fde68a"),
        "supply shock":   ("background:#2d0a0a", "color:#f87171"),
        "price risk":     ("background:#2d0a0a", "color:#f87171"),
        "community hype": ("background:#1a0c2e", "color:#c084fc"),
        "pvp meta":       ("background:#2d1a0a", "color:#fdba74"),
        "new content":    ("background:#052e16", "color:#4ade80"),
        "raids prep":     ("background:#052e16", "color:#4ade80"),
    }

    def style_signals(row):
        idx = row.name
        if idx >= len(records): return [""] * len(cols)
        rec = records[idx]
        result = []
        for col in cols:
            if col == "Trend":
                result.append(trend_css(rec["trend"]))
            elif col == "1D %":
                result.append(pct_css(rec["chg_1d"]))
            elif col == "7D %":
                result.append(pct_css(rec["chg_7d"]))
            elif col == "30D %":
                result.append(pct_css(rec["chg_30d"]))
            elif col == "B/S":
                result.append(ratio_css(rec["ratio"]))
            elif col == "Status":
                s = rec["status"].upper()
                if s == "ACTIVE":    result.append("background:#2d0a0a; color:#f87171; font-weight:700")
                elif s == "WATCH":   result.append("background:#1c1a00; color:#facc15; font-weight:700")
                elif s == "COOLING": result.append("color:#94a3b8; font-weight:600")
                else:                result.append("")
            elif col == "Type":
                bg, fg = TYPE_BG.get(rec["raw_type"], ("", "color:#38bdf8"))
                result.append(f"{bg}; {fg}; font-weight:600" if bg else f"{fg}")
            else:
                result.append("")
        return result

    st.dataframe(df.style.apply(style_signals, axis=1),
                 use_container_width=True, hide_index=True, height=620)

# -- Session / fetch ----------------------------------------------------------
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


# -- Header -------------------------------------------------------------------
_tw_color, _tw_msg = get_timing()
_cmap = {"green": "#22c55e", "yellow": "#facc15", "red": "#ef4444"}

col_title, col_banner, col_meta, col_btn = st.columns([3, 5, 2, 1])
with col_title:
    st.markdown(
        "<h2 style='margin:0; padding:0; line-height:1.2; "
        "font-size:1.5rem; color:#f1f5f9;'>Owen's GE Tracker</h2>",
        unsafe_allow_html=True,
    )
with col_banner:
    st.markdown(
        f"<div style='background:#1e293b; border-left:4px solid {_cmap[_tw_color]}; "
        f"padding:9px 14px; border-radius:6px; font-size:.84rem; "
        f"color:#e5e7eb; margin-top:2px; line-height:1.4;'>{_tw_msg}</div>",
        unsafe_allow_html=True,
    )
with col_meta:
    # Timestamps shown before data loads -- will be "never" initially
    _p_ago_hdr = fmt_ago(secs_ago(st.session_state.get("price_ts")))
    _v_ago_hdr = fmt_ago(secs_ago(st.session_state.get("volume_ts")))
    st.markdown(
        f"<div style='text-align:right; line-height:1.6; margin-top:4px;'>"
        f"<span style='font-size:.72rem; color:#64748b;'>Prices: </span>"
        f"<span style='font-size:.72rem; color:#94a3b8; font-weight:600;'>{_p_ago_hdr}</span>"
        f"<br>"
        f"<span style='font-size:.72rem; color:#64748b;'>Volumes: </span>"
        f"<span style='font-size:.72rem; color:#94a3b8; font-weight:600;'>{_v_ago_hdr}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
with col_btn:
    manual = st.button("Refresh", type="primary", use_container_width=True)

# -- Data loading -------------------------------------------------------------
with st.spinner("Loading..."):
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
    st.warning("Waiting for data..."); st.stop()

bulk_rows, singular, high_roi, watch, signals, all_rows = data

# -- Tabs ---------------------------------------------------------------------
tab_bulk, tab_sing, tab_roi, tab_shifts, tab_watch, tab_sig = st.tabs([
    "Bulk", "Singular", "High ROI", "Shifts", "Watchlist", "Signals",
])

with tab_bulk:
    st.caption(f"High-volume bulk flips. Updated {fmt_ago(p_ago)}.")
    show_table(bulk_rows,
               ["name","buy_price","sell_price","profit_unit","roi",
                "ge_limit","fq_label","ratio","realistic_profit"], height=520)

with tab_sing:
    st.caption("Low GE-limit, high-value singular flips.")
    show_table(singular,
               ["name","buy_price","sell_price","profit_unit","roi",
                "ge_limit","fq_label","ratio","adj_potential"], height=520)

with tab_roi:
    st.caption("Best ROI % regardless of volume.")
    show_table(high_roi,
               ["name","buy_price","sell_price","profit_unit","roi",
                "fq_label","ratio","ge_limit"], height=520)

# -- Shifts tab ---------------------------------------------------------------
with tab_shifts:
    render_trend_legend()
    st.caption(
        "Each section splits into Gainers (left) and Decliners (right). "
        "% Shift column shows the move and the price it was measured from. "
        "Intraday refreshes every 5 min. Daily refreshes every hour."
    )

    mapping = st.session_state.get("mapping", [])
    if stale("shifts_ts", SHIFTS_INTERVAL) or manual:
        with st.spinner("Fetching shift data (~15-30s)..."):
            do_shifts(all_rows, mapping)

    shifts_ht   = st.session_state.get("shifts_ht",   [])
    shifts_bulk = st.session_state.get("shifts_bulk", [])
    shifts_ago  = fmt_ago(secs_ago(st.session_state.get("shifts_ts")))

    if shifts_ht or shifts_bulk:
        render_top_movers(shifts_ht, shifts_bulk)

    # Section 1 -- Intraday (use 1h as primary)
    render_shifts_section(
        "Section 1 -- Intraday Price Shifts",
        shifts_ht, shifts_bulk,
        pct_key="chg_1h", prev_key="prev_price_1h", pct_label="1h %",
        updated_label=f"Sorted by absolute 1h move. Last: {shifts_ago}.",
    )
    # Section 2 -- 1D
    render_shifts_section(
        "Section 2 -- 1-Day Price Shifts",
        shifts_ht, shifts_bulk,
        pct_key="chg_1d", prev_key="prev_price_1d", pct_label="1D %",
        updated_label=f"Last: {shifts_ago}.",
    )
    # Section 3 -- 7D
    render_shifts_section(
        "Section 3 -- 7-Day Price Shifts",
        shifts_ht, shifts_bulk,
        pct_key="chg_7d", prev_key="prev_price_7d", pct_label="7D %",
        updated_label=f"Last: {shifts_ago}.",
    )
    # Section 4 -- 14D
    render_shifts_section(
        "Section 4 -- 14-Day Price Shifts",
        shifts_ht, shifts_bulk,
        pct_key="chg_14d", prev_key="prev_price_14d", pct_label="14D %",
        updated_label=f"Last: {shifts_ago}.",
    )
    # Section 5 -- 30D
    render_shifts_section(
        "Section 5 -- 30-Day Price Shifts",
        shifts_ht, shifts_bulk,
        pct_key="chg_30d", prev_key="prev_price_30d", pct_label="30D %",
        updated_label=f"Last: {shifts_ago}.",
    )

# -- Watchlist tab ------------------------------------------------------------
with tab_watch:
    render_watchlist(watch)

# -- Signals tab --------------------------------------------------------------
with tab_sig:
    st.caption(
        "Meta-sensitive items flagged by update type and status. "
        "Run an OSRS Signals Sweep to refresh context strings in ge_api.py."
    )
    render_signals(signals)