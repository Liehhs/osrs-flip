import time
from datetime import datetime

import pandas as pd
import pytz
import streamlit as st

from ge_api import (
    WATCHLIST_CATALYSTS,
    SIGNALS_UNIVERSE,
    compute_flips,
    fetch_latest,
    fetch_mapping,
    fetch_volumes,
)

st.set_page_config(
    page_title="Owen's GE Tracker",
    layout="wide",
    page_icon="\U0001f4c8",
    initial_sidebar_state="collapsed",
)

PRICE_INTERVAL = 60
VOLUME_INTERVAL = 300
MAPPING_KEY = "mapping_loaded"

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_gp(n):
    if n is None:
        return "--"
    try:
        n = int(n)
    except Exception:
        return "--"
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,}"


def fmt_pct(v):
    if v is None:
        return "--"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.2f}%"


def now_ts():
    return time.time()


def secs_ago(ts):
    return int(now_ts() - ts) if ts else None


def fmt_ago(s):
    if s is None:
        return "never"
    if s < 60:
        return f"{s}s ago"
    return f"{s // 60}m {s % 60}s ago"


def get_timing():
    est = pytz.timezone("America/New_York")
    now = datetime.now(est)
    h = now.hour
    ts = now.strftime("%I:%M %p ET")
    if 14 <= h < 22:
        return "green", f"Sell window -- US/EU peak overlap. Best time to exit positions. ({ts})"
    if 6 <= h < 14:
        return "yellow", f"Transition window -- Moderate activity. Good for placing buy orders. ({ts})"
    return "red", f"Buy window -- Off-peak. Place buy orders now, sell into afternoon. ({ts})"


# ---------------------------------------------------------------------------
# CSS helpers
# ---------------------------------------------------------------------------

def ratio_fmt(r):
    return "--" if r is None else f"{r:.2f}"


def ratio_css(r):
    if r is None:
        return "color:#64748b"
    if 0.8 <= r <= 1.5:
        return "color:#4ade80"
    if 1.5 < r <= 3.0:
        return "color:#fb923c"
    if r > 3.0:
        return "color:#f87171"
    if 0.4 <= r < 0.8:
        return "color:#facc15"
    return "color:#f87171"


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
    if v is None:
        return "color:#64748b"
    if v >= 10:
        return "color:#22c55e; font-weight:600"
    if v > 0:
        return "color:#86efac"
    if v <= -10:
        return "color:#ef4444; font-weight:600"
    if v < 0:
        return "color:#fca5a5"
    return "color:#cbd5e1"


def trend_css(t):
    return {
        "Pullback":   "color:#facc15; font-weight:600",
        "Building":   "color:#4ade80; font-weight:600",
        "Extended":   "color:#fb923c; font-weight:600",
        "Weakening":  "color:#ef4444; font-weight:600",
        "Flat":       "color:#94a3b8",
    }.get(t, "")


def flag_css(flags):
    if flags == "Quiet":
        return "color:#64748b"
    if "1D shock" in flags or "7D move" in flags:
        return "color:#fbbf24; font-weight:600"
    if "Wide spread" in flags or "High gp/item" in flags:
        return "color:#4ade80; font-weight:600"
    return "color:#cbd5e1"


# ---------------------------------------------------------------------------
# Data loading / session state
# ---------------------------------------------------------------------------

def load_mapping():
    if MAPPING_KEY not in st.session_state:
        st.session_state["mapping"] = fetch_mapping()
        st.session_state[MAPPING_KEY] = True


def do_prices():
    st.session_state["latest"] = fetch_latest()
    st.session_state["price_ts"] = now_ts()


def do_volumes():
    h, f = fetch_volumes()
    st.session_state["hour_vols"] = h
    st.session_state["fmin_vols"] = f
    st.session_state["volume_ts"] = now_ts()


def stale(key, interval):
    last = st.session_state.get(key)
    return last is None or (now_ts() - last) >= interval


def recompute():
    st.session_state["data"] = compute_flips(
        st.session_state.get("latest", {}),
        st.session_state.get("mapping", []),
        st.session_state.get("hour_vols", {}),
        st.session_state.get("fmin_vols", {}),
    )


# ---------------------------------------------------------------------------
# Table renderers
# ---------------------------------------------------------------------------

def render_basic_table(rows, title, cols, height=520):
    st.markdown(f"<h4 style='margin-bottom:6px'>{title}</h4>", unsafe_allow_html=True)
    if not rows:
        st.info("No items found.")
        return
    df = pd.DataFrame(rows)
    disp = pd.DataFrame()
    col_labels = {
        "name":             "Item",
        "buy_price":        "Buy",
        "sell_price":       "Sell",
        "profit_unit":      "Profit/ea",
        "roi":              "ROI %",
        "ge_limit":         "GE Limit",
        "total_hr":         "Vol/hr",
        "fq_label":         "Fill Quality",
        "ratio":            "B/S Ratio",
        "realistic_profit": "Real. Profit",
        "adj_potential":    "Adj. Potential",
    }
    for c in cols:
        if c not in df.columns:
            continue
        label = col_labels.get(c, c)
        if c in ("buy_price", "sell_price", "profit_unit", "realistic_profit", "adj_potential"):
            disp[label] = df[c].map(fmt_gp)
        elif c == "roi":
            disp[label] = df[c].map(lambda v: f"{v:.2f}%" if v is not None else "--")
        elif c in ("ge_limit", "total_hr"):
            disp[label] = df[c].map(lambda v: f"{int(v):,}" if v is not None else "--")
        elif c == "ratio":
            disp[label] = df[c].map(ratio_fmt)
        else:
            disp[label] = df[c]
    st.dataframe(disp, use_container_width=True, hide_index=True, height=height)


def render_watch_signals_table(rows, context_key="catalyst"):
    """Shared renderer for Investment Watchlist and Signals tabs."""
    if not rows:
        st.info("No items found.")
        return

    trend_icon = {
        "Building":  "\U0001f7e2",  # green circle
        "Extended":  "\U0001f7e0",  # orange circle
        "Pullback":  "\U0001f7e1",  # yellow circle
        "Weakening": "\U0001f534",  # red circle
        "Flat":      "\u26aa",       # grey circle
    }

    rows_out = []
    for r in rows:
        trend = r.get("trend", "Flat")
        icon = trend_icon.get(trend, "\u26aa")
        ch1  = r.get("chg_1d")
        ch7  = r.get("chg_7d")
        ch30 = r.get("chg_30d")
        rows_out.append({
            "Item":       r.get("name", ""),
            "Trend":      f"{icon} {trend}",
            "1D %":       fmt_pct(ch1),
            "7D %":       fmt_pct(ch7),
            "30D %":      fmt_pct(ch30),
            "Buy":        fmt_gp(r.get("buy_price")),
            "Sell":       fmt_gp(r.get("sell_price")),
            "Profit/ea":  fmt_gp(r.get("profit_unit")),
            "ROI %":      f"{r.get('roi', 0):.2f}%" if r.get("roi") is not None else "--",
            "Vol/hr":     f"{int(r.get('total_hr', 0)):,}",
            "Flags":      r.get("flags", "Quiet"),
            "Context":    r.get(context_key, ""),
        })

    disp = pd.DataFrame(rows_out)
    st.dataframe(disp, use_container_width=True, hide_index=True, height=600)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    # ---- global CSS injection ----
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0f172a; }
    [data-testid="stHeader"] { background-color: #0f172a; }
    body, .stMarkdown, .stDataFrame, .stMetric { color: #e5e7eb !important; }
    .block-container { padding-top: 1rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        color: #94a3b8;
        border-radius: 6px 6px 0 0;
        padding: 6px 18px;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #334155 !important;
        color: #38bdf8 !important;
        font-weight: 600;
    }
    div[data-testid="metric-container"] {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 10px 16px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---- header ----
    col_title, col_timing = st.columns([3, 2])
    with col_title:
        st.markdown("## Owen's GE Tracker")
    with col_timing:
        tw_color, tw_msg = get_timing()
        color_map = {"green": "#22c55e", "yellow": "#facc15", "red": "#ef4444"}
        st.markdown(
            f"<div style='background:#1e293b;border-left:4px solid {color_map[tw_color]};"
            f"padding:10px 14px;border-radius:6px;font-size:0.85rem;color:#e5e7eb'>"
            f"{tw_msg}</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ---- data loading ----
    load_mapping()
    with st.spinner("Refreshing prices..."):
        if stale("price_ts", PRICE_INTERVAL):
            do_prices()
        if stale("volume_ts", VOLUME_INTERVAL):
            do_volumes()

    if not st.session_state.get("latest"):
        st.warning("Waiting for price data...")
        st.stop()

    recompute()
    data = st.session_state.get("data")
    if not data:
        st.error("compute_flips returned no data.")
        st.stop()

    bulk, singular, high_roi, watch, signals, all_rows = data

    # ---- KPI bar ----
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    price_ago = fmt_ago(secs_ago(st.session_state.get("price_ts")))
    vol_ago   = fmt_ago(secs_ago(st.session_state.get("volume_ts")))
    k1.metric("Bulk Flips",       len(bulk))
    k2.metric("Singular Flips",   len(singular))
    k3.metric("High ROI",         len(high_roi))
    k4.metric("Watchlist Items",  len(watch))
    k5.metric("Prices Updated",   price_ago)
    k6.metric("Volumes Updated",  vol_ago)

    st.divider()

    # ---- tabs ----
    tab_bulk, tab_sing, tab_roi, tab_watch, tab_sig = st.tabs([
        "\U0001f4e6  Bulk",
        "\U0001f48e  Singular",
        "\U0001f4c8  High ROI",
        "\U0001f4bc  Investment Watchlist",
        "\U0001f4e1  Signals",
    ])

    with tab_bulk:
        st.caption(f"High-volume bulk flips -- items you can move in quantity. Updated {price_ago}.")
        render_basic_table(
            bulk, "Bulk Flips",
            ["name", "buy_price", "sell_price", "profit_unit", "roi",
             "ge_limit", "total_hr", "fq_label", "ratio", "realistic_profit"],
        )

    with tab_sing:
        st.caption("Low GE-limit, high-value singular items. One at a time, big margin.")
        render_basic_table(
            singular, "Singular Flips",
            ["name", "buy_price", "sell_price", "profit_unit", "roi",
             "ge_limit", "total_hr", "fq_label", "ratio", "adj_potential"],
        )

    with tab_roi:
        st.caption("Best ROI % regardless of volume. Good for smaller bankrolls.")
        render_basic_table(
            high_roi, "High ROI",
            ["name", "buy_price", "sell_price", "profit_unit", "roi",
             "total_hr", "ge_limit", "fq_label", "ratio"],
        )

    with tab_watch:
        st.caption(
            "Curated investment-grade items. Always displayed -- shows Building, Flat, and Weakening trends. "
            "Use 1D/7D/30D % to track momentum over time."
        )
        render_watch_signals_table(watch, context_key="catalyst")

    with tab_sig:
        st.caption(
            "Meta-sensitive items -- affected by game updates, dev blogs, hype, and patch notes. "
            "Always displayed. Sorted by trend activity. Use alongside patch notes and community discussion."
        )
        # Inject signal_context from SIGNALS_UNIVERSE into each row for display
        for s in signals:
            if "catalyst" not in s:
                s["catalyst"] = s.get("signal_context", SIGNALS_UNIVERSE.get(s.get("name", ""), ""))
        render_watch_signals_table(signals, context_key="catalyst")


if __name__ == "__main__":
    main()