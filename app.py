import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from formatters import fmt_ago, fmt_gp, fmt_int, fmt_pct, get_timing, now_ts, secs_ago
from ge_api import WATCHLIST_CATALYSTS, compute_flips, fetch_latest, fetch_mapping, fetch_timeseries, fetch_volumes
from theme import THEME, inject_theme
from ui_helpers import add_score, compute_score, ratio_state, status_badge, style_dataframe, to_df, trend_state

st.set_page_config(page_title="OSRS GE Dashboard", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

PRICE_INTERVAL = 60
VOLUME_INTERVAL = 300
MAPPING_KEY = "mapping_loaded"

TAB_COPY = {
    "Bulk": "Bulk focuses on higher-limit flips where repeatability and fill rate matter more than any one item. Use this tab to find scalable trades with strong realistic profit potential.",
    "Singular": "Singular highlights lower-limit, higher-value items where each successful flip carries more GP per item. Use it when you want fewer positions with bigger individual outcomes.",
    "High ROI": "High ROI surfaces trades with strong percentage return relative to buy price. This view is useful for finding efficient capital deployment, especially on smaller stacks.",
    "Watchlist": "Watchlist tracks your core high-interest items and adds catalyst context so you can judge why movement may matter. It is the best tab for monitoring names you already care about day to day.",
    "Signals": "Signals is your discovery tab for non-core items that still fired enough movement, spread, or event conditions to deserve attention. It helps you catch opportunities outside the main watchlist before they become obvious.",
}


def load_mapping():
    if MAPPING_KEY not in st.session_state:
        st.session_state["mapping"] = fetch_mapping()
        st.session_state[MAPPING_KEY] = True


def do_prices():
    st.session_state["latest"] = fetch_latest()
    st.session_state["price_ts"] = now_ts()


def do_volumes():
    hour_vols, fmin_vols = fetch_volumes()
    st.session_state["hour_vols"] = hour_vols
    st.session_state["fmin_vols"] = fmin_vols
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


def render_header(price_age, volume_age):
    timing_kind, timing_title, timing_body = get_timing()
    st.markdown(
        f"""
        <div class="hero-card">
            <div>{status_badge('accent', 'OSRS Project')}{status_badge(timing_kind, timing_title)}</div>
            <div class="hero-title">Grand Exchange Opportunity Dashboard</div>
            <div class="hero-subtitle">A decision-first OSRS flipping dashboard for scalable trades, high-value uniques, momentum watchlist names, and emerging signals.</div>
            <div style="margin-top:0.45rem;">{timing_body}</div>
            <div class="small-note">Prices updated {fmt_ago(price_age)} · Volumes updated {fmt_ago(volume_age)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_controls(all_rows):
    st.sidebar.title("Controls")
    min_profit = st.sidebar.number_input("Min profit / item", min_value=0, value=1000, step=100)
    min_volume = st.sidebar.number_input("Min total volume / hr", min_value=0, value=50, step=10)
    max_buy = st.sidebar.number_input("Max buy price", min_value=0, value=500_000_000, step=100_000)
    trend_filter = st.sidebar.multiselect(
        "Trend states",
        ["Building", "Pullback", "Extended", "Weakening", "Flat"],
        default=["Building", "Pullback", "Extended", "Weakening", "Flat"],
    )
    tax_cap_only = st.sidebar.checkbox("Tax-cap items only", value=False)
    st.sidebar.caption("Filters apply to the main ranked tables so you can narrow opportunities without changing the underlying market logic.")

    filtered = []
    for row in all_rows:
        if (row.get("profit_unit", 0) or 0) < min_profit:
            continue
        if (row.get("total_hr", 0) or 0) < min_volume:
            continue
        if (row.get("buy_price", 0) or 0) > max_buy:
            continue
        if row.get("trend", "Flat") not in trend_filter:
            continue
        if tax_cap_only and not row.get("tax_cap"):
            continue
        filtered.append(row)
    return filtered


def render_tab_intro(tab_name):
    st.markdown(f'<div class="section-subtitle tab-intro">{TAB_COPY[tab_name]}</div>', unsafe_allow_html=True)


def render_table(rows, title, columns, formatters, height=540):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if not rows:
        st.info("No items matched the current view.")
        return
    df = to_df(rows, columns)
    st.dataframe(style_dataframe(df, formatters=formatters), use_container_width=True, height=height)


def render_watchlist(rows):
    st.markdown('<div class="section-title">Core watchlist</div>', unsafe_allow_html=True)
    if not rows:
        st.info("Watchlist data is not available yet.")
        return
    for row in rows[:12]:
        ratio_kind, ratio_label = ratio_state(row.get("ratio"))
        c1, c2 = st.columns([3.2, 1.2])
        with c1:
            st.markdown(f"### {row['name']}")
            st.markdown(
                status_badge(trend_state(row.get("trend", "Flat")), row.get("trend", "Flat"))
                + status_badge(ratio_kind, ratio_label)
                + status_badge("accent", f"Score {compute_score(row)}"),
                unsafe_allow_html=True,
            )
            st.caption(WATCHLIST_CATALYSTS.get(row["name"], ""))
            st.write(
                f"Spread {fmt_gp(row.get('profit_unit'))} | ROI {fmt_pct(row.get('roi'))} | "
                f"1D {fmt_pct(row.get('chg_1d'))} | 7D {fmt_pct(row.get('chg_7d'))} | 30D {fmt_pct(row.get('chg_30d'))}"
            )
            st.write(f"Flags: {row.get('flags', 'Quiet')}")
        with c2:
            st.metric("Buy", fmt_gp(row.get("buy_price")))
            st.metric("Sell", fmt_gp(row.get("sell_price")))
            st.metric("Daily volume", fmt_int(row.get("daily_volume")))
        st.divider()


def render_signals(rows):
    st.markdown('<div class="section-title">Signal board</div>', unsafe_allow_html=True)
    if not rows:
        st.info("No signal names met the current threshold.")
        return
    data = []
    for row in rows:
        data.append(
            {
                "Item": row.get("name"),
                "Reason": row.get("candidate_reason", ""),
                "Score": compute_score(row),
                "Trend": row.get("trend"),
                "1D": row.get("chg_1d"),
                "7D": row.get("chg_7d"),
                "Profit": row.get("profit_unit"),
                "Flags": row.get("flags"),
            }
        )
    df = pd.DataFrame(data)
    st.dataframe(
        style_dataframe(df, formatters={"1D": fmt_pct, "7D": fmt_pct, "Profit": fmt_gp, "Score": lambda x: f"{x:.2f}"}),
        use_container_width=True,
        height=420,
    )


def render_timeseries_chart(item_name, rows):
    options = {row["name"]: row["id"] for row in rows}
    if not options:
        return
    names = list(options.keys())
    default_name = item_name if item_name in options else names[0]
    selected = st.selectbox("Chart item", options=names, index=names.index(default_name))
    series = fetch_timeseries(options[selected], timestep="24h")
    if not series:
        st.info("No historical data returned for this item.")
        return
    df = pd.DataFrame(series)
    if df.empty or "timestamp" not in df.columns:
        st.info("Historical series is incomplete.")
        return
    df["dt"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.tz_convert("America/New_York")
    fig = go.Figure()
    if "avgHighPrice" in df.columns:
        fig.add_trace(go.Scatter(x=df["dt"], y=df["avgHighPrice"], mode="lines", name="Avg High", line=dict(color=THEME["accent"], width=3)))
    if "avgLowPrice" in df.columns:
        fig.add_trace(go.Scatter(x=df["dt"], y=df["avgLowPrice"], mode="lines", name="Avg Low", line=dict(color=THEME["positive"], width=2)))
    fig.update_layout(
        height=360,
        paper_bgcolor=THEME["panel"],
        plot_bgcolor=THEME["panel"],
        font=dict(color=THEME["text"]),
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,0.12)"),
    )
    st.plotly_chart(fig, use_container_width=True)


def main():
    inject_theme(st)
    st_autorefresh(interval=60_000, key="dashboard_refresh")
    load_mapping()
    if stale("price_ts", PRICE_INTERVAL):
        do_prices()
    if stale("volume_ts", VOLUME_INTERVAL):
        do_volumes()
    recompute()

    bulk, singular, high_roi, watch, signals, all_rows = st.session_state.get("data", ([], [], [], [], [], []))
    bulk = add_score(bulk)
    singular = add_score(singular)
    high_roi = add_score(high_roi)
    watch = add_score(watch)
    signals = add_score(signals)
    all_rows = add_score(all_rows)

    filtered_all = sidebar_controls(all_rows)
    filtered_names = {row["name"] for row in filtered_all}
    filtered_bulk = [row for row in bulk if row["name"] in filtered_names]
    filtered_singular = [row for row in singular if row["name"] in filtered_names]
    filtered_high_roi = [row for row in high_roi if row["name"] in filtered_names]

    render_header(secs_ago(st.session_state.get("price_ts")), secs_ago(st.session_state.get("volume_ts")))

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Bulk ideas", len(filtered_bulk))
    with k2:
        st.metric("Singular ideas", len(filtered_singular))
    with k3:
        top_profit = max([row.get("realistic_profit", 0) or 0 for row in filtered_all], default=0)
        st.metric("Top realistic profit", fmt_gp(top_profit))
    with k4:
        avg_roi = round(pd.Series([row.get("roi", 0) or 0 for row in filtered_all]).mean(), 2) if filtered_all else 0
        st.metric("Average ROI", f"{avg_roi}%")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Bulk", "Singular", "High ROI", "Watchlist", "Signals"])

    with tab1:
        render_tab_intro("Bulk")
        render_table(
            sorted(filtered_bulk, key=lambda row: (-row.get("score", 0), -row.get("realistic_profit", 0))),
            "Bulk flips",
            ["name", "score", "buy_price", "sell_price", "profit_unit", "roi", "ge_limit", "total_hr", "ratio", "realistic_profit"],
            {"score": lambda x: f"{x:.2f}", "buy_price": fmt_gp, "sell_price": fmt_gp, "profit_unit": fmt_gp, "roi": fmt_pct, "ge_limit": fmt_int, "total_hr": fmt_int, "ratio": lambda x: "—" if x is None else f"{x:.2f}", "realistic_profit": fmt_gp},
        )
        render_timeseries_chart(filtered_bulk[0]["name"] if filtered_bulk else "", filtered_bulk or bulk)

    with tab2:
        render_tab_intro("Singular")
        render_table(
            sorted(filtered_singular, key=lambda row: (-row.get("score", 0), -row.get("profit_unit", 0))),
            "Singular flips",
            ["name", "score", "buy_price", "sell_price", "profit_unit", "roi", "ge_limit", "total_hr", "ratio", "adj_potential"],
            {"score": lambda x: f"{x:.2f}", "buy_price": fmt_gp, "sell_price": fmt_gp, "profit_unit": fmt_gp, "roi": fmt_pct, "ge_limit": fmt_int, "total_hr": fmt_int, "ratio": lambda x: "—" if x is None else f"{x:.2f}", "adj_potential": fmt_gp},
        )

    with tab3:
        render_tab_intro("High ROI")
        render_table(
            sorted(filtered_high_roi, key=lambda row: (-row.get("score", 0), -row.get("roi", 0))),
            "High ROI opportunities",
            ["name", "score", "buy_price", "sell_price", "profit_unit", "roi", "total_hr", "ratio", "ge_limit"],
            {"score": lambda x: f"{x:.2f}", "buy_price": fmt_gp, "sell_price": fmt_gp, "profit_unit": fmt_gp, "roi": fmt_pct, "total_hr": fmt_int, "ratio": lambda x: "—" if x is None else f"{x:.2f}", "ge_limit": fmt_int},
        )

    with tab4:
        render_tab_intro("Watchlist")
        render_watchlist(watch)

    with tab5:
        render_tab_intro("Signals")
        render_signals(signals)


if __name__ == "__main__":
    main()