import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import pytz
import streamlit as st

from ge_api import (
    WATCHLIST_CATALYSTS,
    compute_flips,
    fetch_latest,
    fetch_mapping,
    fetch_timeseries,
    fetch_volumes,
)

st.set_page_config(
    page_title="Owen's GE Tracker",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="collapsed",
)

PRICE_INTERVAL = 60
VOLUME_INTERVAL = 300
MAPPING_KEY = "mapping_loaded"


def fmt_gp(n):
    if n is None:
        return "—"
    try:
        n = int(n)
    except Exception:
        return "—"
    if abs(n) >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,}"


def now_ts():
    return time.time()


def secs_ago(ts):
    return int(now_ts() - ts) if ts else None


def fmt_ago(s):
    if s is None:
        return "never"
    if s < 60:
        return f"{s}s ago"
    return f"{s//60}m {s%60}s ago"


def get_timing():
    est = pytz.timezone("America/New_York")
    now = datetime.now(est)
    h, ts = now.hour, now.strftime("%I:%M %p ET")
    if 14 <= h < 22:
        return "green", f"Sell window — US/EU peak overlap. Best time to exit positions. ({ts})"
    if 6 <= h < 14:
        return "yellow", f"Transition window — Moderate activity. Good for placing buy orders. ({ts})"
    return "red", f"Buy window — Off-peak. Place buy orders now, sell into afternoon. ({ts})"


def ratio_fmt(r):
    return "—" if r is None else f"{r:.2f}"


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
        "Ideal": "color:#4ade80",
        "High demand": "color:#fb923c",
        "Hard to buy": "color:#f87171",
        "Slight flood": "color:#facc15",
        "Flooded": "color:#f87171",
        "No data": "color:#64748b",
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
        "Pullback": "color:#facc15; font-weight:600",
        "Building": "color:#4ade80; font-weight:600",
        "Extended": "color:#fb923c; font-weight:600",
        "Weakening": "color:#ef4444; font-weight:600",
        "Flat": "color:#94a3b8",
    }.get(t, "")


def flag_css(flags):
    if flags == "Quiet":
        return "color:#64748b"
    if "1D shock" in flags or "7D move" in flags:
        return "color:#fbbf24; font-weight:600"
    if "Wide spread" in flags or "High gp/item" in flags:
        return "color:#4ade80; font-weight:600"
    return "color:#cbd5e1"


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


def render_basic_table(rows, title, cols, height=520):
    st.markdown(f"<div class='section-label'>{title}</div>", unsafe_allow_html=True)
    data = []
    for r in rows:
        data.append({
            "Item": r["name"],
            "Buy": fmt_gp(r.get("buy_price")),
            "Sell": fmt_gp(r.get("sell_price")),
            "Profit/item": fmt_gp(r.get("profit_unit")),
            "ROI %": f"{r.get('roi', 0):.1f}%",
            "Buy/hr": f"{int(r.get('buy_qty_hr', 0)):,}",
            "Sell/hr": f"{int(r.get('sell_qty_hr', 0)):,}",
            "B/S": ratio_fmt(r.get("ratio")),
            "Fill": r.get("fq_label", "No data"),
            "GE Lmt": f"{int(r.get('ge_limit', 0)):,}",
            "Realistic 4hr": fmt_gp(r.get("realistic_profit")),
        })
    df = pd.DataFrame(data)
    if df.empty:
        st.info("No rows available.")
        return

    def style_row(row):
        idx = row.name
        r = rows[idx]
        out = []
        for col in df.columns:
            if col == "B/S":
                out.append(ratio_css(r.get("ratio")))
            elif col == "Fill":
                out.append(fq_css(r.get("fq_label", "No data")))
            else:
                out.append("")
        return out

    st.dataframe(df.style.apply(style_row, axis=1), use_container_width=True, hide_index=True, height=height)


st.markdown(
    """
    <style>
    .section-label {font-size:0.9rem; text-transform:uppercase; letter-spacing:0.08em; color:#94a3b8; margin:0.6rem 0 0.45rem 0;}
    .banner-green,.banner-yellow,.banner-red {padding:0.8rem 1rem; border-radius:14px; font-weight:600; margin:0.7rem 0 1rem 0;}
    .banner-green {background:#052e16; color:#bbf7d0; border:1px solid #14532d;}
    .banner-yellow {background:#3b2f08; color:#fde68a; border:1px solid #854d0e;}
    .banner-red {background:#3f0d12; color:#fecaca; border:1px solid #7f1d1d;}
    .card-note {background:#111827; border:1px solid #1f2937; border-radius:14px; padding:0.9rem 1rem; margin:0.7rem 0 1rem 0; color:#cbd5e1;}
    </style>
    """,
    unsafe_allow_html=True,
)

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

p_ago = secs_ago(st.session_state.get("price_ts"))
v_ago = secs_ago(st.session_state.get("volume_ts"))
with h2:
    st.markdown(
        f"<div style='text-align:right;color:#94a3b8;padding-top:0.5rem'>Prices: <b>{fmt_ago(p_ago)}</b> &nbsp;·&nbsp; Volumes: <b>{fmt_ago(v_ago)}</b></div>",
        unsafe_allow_html=True,
    )

if "data" not in st.session_state:
    st.info("Loading data…")
    st.stop()

data_bundle = st.session_state["data"]
if len(data_bundle) == 6:
    bulk, singular, high_roi, watch, candidates, all_rows = data_bundle
else:
    bulk, singular, high_roi, watch, all_rows = data_bundle
    candidates = []

tw_color, tw_msg = get_timing()
st.markdown(f"<div class='banner-{tw_color}'>{tw_msg}</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='card-note'><b>Design logic:</b> Investment Watchlist membership is stable and manual. Live market changes appear as event flags on those same items. New names surface in Candidate Intake and only become watchlist items when you deliberately add them.</div>",
    unsafe_allow_html=True,
)

t_sing, t_bulk, t_roi, t_watch, t_candidates, t_guide = st.tabs([
    "Singular / High Margin",
    "Bulk Flips",
    "High ROI",
    "Investment Watchlist",
    "Candidate Intake",
    "Guide",
])

with t_sing:
    render_basic_table(singular, "Best singular / low-limit flips", ["name"])

with t_bulk:
    render_basic_table(bulk, "Best bulk flips", ["name"])

with t_roi:
    render_basic_table(high_roi, "Highest ROI items", ["name"])

with t_watch:
    if watch:
        records = []
        for r in watch:
            records.append({
                "Item": r["name"],
                "Flags": r.get("flags", "Quiet"),
                "Trend": r.get("trend", "Flat"),
                "1D %": "—" if r.get("chg_1d") is None else f"{r['chg_1d']:+.1f}%",
                "7D %": "—" if r.get("chg_7d") is None else f"{r['chg_7d']:+.1f}%",
                "30D %": "—" if r.get("chg_30d") is None else f"{r['chg_30d']:+.1f}%",
                "Buy": fmt_gp(r.get("buy_price")),
                "Sell": fmt_gp(r.get("sell_price")),
                "Profit/item": fmt_gp(r.get("profit_unit")),
                "ROI %": f"{r.get('roi', 0):.1f}%",
                "Catalyst": WATCHLIST_CATALYSTS.get(r["name"], ""),
            })
        df = pd.DataFrame(records)

        def style_watch(row):
            idx = row.name
            r = watch[idx]
            out = []
            for col in df.columns:
                if col == "Flags":
                    out.append(flag_css(r.get("flags", "Quiet")))
                elif col == "Trend":
                    out.append(trend_css(r.get("trend", "Flat")))
                elif col == "1D %":
                    out.append(pct_css(r.get("chg_1d")))
                elif col == "7D %":
                    out.append(pct_css(r.get("chg_7d")))
                elif col == "30D %":
                    out.append(pct_css(r.get("chg_30d")))
                else:
                    out.append("")
            return out

        st.dataframe(
            df.style.apply(style_watch, axis=1),
            use_container_width=True,
            hide_index=True,
            height=560,
            column_config={
                "Catalyst": st.column_config.TextColumn("Catalyst", width="large"),
                "Item": st.column_config.TextColumn("Item", width="medium"),
                "Flags": st.column_config.TextColumn("Flags", width="medium"),
            },
        )

        st.markdown("<div class='section-label'>90-day price history</div>", unsafe_allow_html=True)
        selected = st.selectbox("Select watchlist item", [r["name"] for r in watch], key="watch_item")
        sel_row = next((r for r in watch if r["name"] == selected), None)
        if sel_row:
            ts_data = fetch_timeseries(sel_row["id"], "24h")
            if ts_data:
                ts_df = pd.DataFrame(ts_data)
                ts_df["date"] = pd.to_datetime(ts_df["timestamp"], unit="s")
                fig_ts = go.Figure()
                fig_ts.add_trace(go.Scatter(x=ts_df["date"], y=ts_df["avgHighPrice"], name="Sell (high)", line=dict(color="#38bdf8")))
                fig_ts.add_trace(go.Scatter(x=ts_df["date"], y=ts_df["avgLowPrice"], name="Buy (low)", line=dict(color="#818cf8")))
                fig_ts.update_layout(template="plotly_dark", height=420, title=f"{selected} — 90-day price history")
                st.plotly_chart(fig_ts, use_container_width=True)
            st.caption(WATCHLIST_CATALYSTS.get(selected, ""))
    else:
        st.info("No watchlist items found in this pull.")

with t_candidates:
    if candidates:
        st.markdown("<div class='section-label'>Candidate intake queue</div>", unsafe_allow_html=True)
        st.caption("This is the discovery layer. Items appear here because they triggered event flags strongly enough to merit review. They do not auto-enter your watchlist.")
        records = []
        for r in candidates:
            records.append({
                "Item": r["name"],
                "Flags": r.get("flags", "Quiet"),
                "Trend": r.get("trend", "Flat"),
                "1D %": "—" if r.get("chg_1d") is None else f"{r['chg_1d']:+.1f}%",
                "7D %": "—" if r.get("chg_7d") is None else f"{r['chg_7d']:+.1f}%",
                "30D %": "—" if r.get("chg_30d") is None else f"{r['chg_30d']:+.1f}%",
                "Profit/item": fmt_gp(r.get("profit_unit")),
                "ROI %": f"{r.get('roi', 0):.1f}%",
                "Reason": r.get("candidate_reason", ""),
            })
        df = pd.DataFrame(records)

        def style_candidates(row):
            idx = row.name
            r = candidates[idx]
            out = []
            for col in df.columns:
                if col == "Flags":
                    out.append(flag_css(r.get("flags", "Quiet")))
                elif col == "Trend":
                    out.append(trend_css(r.get("trend", "Flat")))
                elif col == "1D %":
                    out.append(pct_css(r.get("chg_1d")))
                elif col == "7D %":
                    out.append(pct_css(r.get("chg_7d")))
                elif col == "30D %":
                    out.append(pct_css(r.get("chg_30d")))
                else:
                    out.append("")
            return out

        st.dataframe(
            df.style.apply(style_candidates, axis=1),
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={"Reason": st.column_config.TextColumn("Reason", width="large")},
        )
    else:
        st.info("No candidate items are currently triggering strong event flags.")

with t_guide:
    st.markdown(
        """
### How to use this
- Investment Watchlist is your stable coverage universe.
- Flags are the live signal layer; they tell you what changed without removing the item from coverage.
- Candidate Intake is your discovery queue for newly interesting names.
- Only promote a candidate into the watchlist when you have a real thesis, not just a short-term move.
- Use Bulk and Singular tabs for execution; use Watchlist and Candidate Intake for thesis management.
        """
    )