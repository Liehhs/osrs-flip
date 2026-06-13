import pandas as pd
import streamlit as st

from ge_api import WATCHLIST_CATALYSTS, compute_flips, fetch_latest, fetch_mapping, fetch_volumes

st.set_page_config(page_title="OSRS GE Dashboard", page_icon="📈", layout="wide")


def fmt_gp(value):
    if value is None:
        return "—"
    try:
        value = int(value)
    except Exception:
        return "—"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,}"


def fmt_pct(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "—"


@st.cache_data(ttl=60)
def load_prices():
    return fetch_latest()


@st.cache_data(ttl=3600)
def load_mapping():
    return fetch_mapping()


@st.cache_data(ttl=300)
def load_volumes():
    return fetch_volumes()


def main():
    st.title("OSRS GE Dashboard")
    st.caption("Simple stable version to confirm dashboard rendering and data flow.")

    try:
        latest = load_prices()
        mapping = load_mapping()
        hour_vols, fmin_vols = load_volumes()

        bulk, singular, high_roi, watch, signals, rows = compute_flips(
            latest, mapping, hour_vols, fmin_vols
        )
    except Exception as e:
        st.error(f"App error: {type(e).__name__}: {e}")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("All rows", len(rows))
    c2.metric("Bulk", len(bulk))
    c3.metric("Singular", len(singular))
    c4.metric("High ROI", len(high_roi))
    c5.metric("Watchlist", len(watch))

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Bulk", "Singular", "High ROI", "Watchlist", "Signals"]
    )

    with tab1:
        st.subheader("Bulk flips")
        if bulk:
            df = pd.DataFrame(bulk)[
                ["name", "buy_price", "sell_price", "profit_unit", "roi", "ge_limit", "total_hr", "realistic_profit"]
            ].copy()
            df["buy_price"] = df["buy_price"].map(fmt_gp)
            df["sell_price"] = df["sell_price"].map(fmt_gp)
            df["profit_unit"] = df["profit_unit"].map(fmt_gp)
            df["roi"] = df["roi"].map(fmt_pct)
            df["ge_limit"] = df["ge_limit"].map(lambda x: f"{int(x):,}")
            df["total_hr"] = df["total_hr"].map(lambda x: f"{int(x):,}")
            df["realistic_profit"] = df["realistic_profit"].map(fmt_gp)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No bulk items found.")

    with tab2:
        st.subheader("Singular flips")
        if singular:
            df = pd.DataFrame(singular)[
                ["name", "buy_price", "sell_price", "profit_unit", "roi", "ge_limit", "total_hr", "adj_potential"]
            ].copy()
            df["buy_price"] = df["buy_price"].map(fmt_gp)
            df["sell_price"] = df["sell_price"].map(fmt_gp)
            df["profit_unit"] = df["profit_unit"].map(fmt_gp)
            df["roi"] = df["roi"].map(fmt_pct)
            df["ge_limit"] = df["ge_limit"].map(lambda x: f"{int(x):,}")
            df["total_hr"] = df["total_hr"].map(lambda x: f"{int(x):,}")
            df["adj_potential"] = df["adj_potential"].map(fmt_gp)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No singular items found.")

    with tab3:
        st.subheader("High ROI")
        if high_roi:
            df = pd.DataFrame(high_roi)[
                ["name", "buy_price", "sell_price", "profit_unit", "roi", "total_hr", "ge_limit"]
            ].copy()
            df["buy_price"] = df["buy_price"].map(fmt_gp)
            df["sell_price"] = df["sell_price"].map(fmt_gp)
            df["profit_unit"] = df["profit_unit"].map(fmt_gp)
            df["roi"] = df["roi"].map(fmt_pct)
            df["total_hr"] = df["total_hr"].map(lambda x: f"{int(x):,}")
            df["ge_limit"] = df["ge_limit"].map(lambda x: f"{int(x):,}")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No high ROI items found.")

    with tab4:
        st.subheader("Watchlist")
        if watch:
            for row in watch[:15]:
                with st.container():
                    st.markdown(f"### {row['name']}")
                    st.write(WATCHLIST_CATALYSTS.get(row["name"], ""))
                    st.write(
                        f"Buy: {fmt_gp(row.get('buy_price'))} | "
                        f"Sell: {fmt_gp(row.get('sell_price'))} | "
                        f"Profit: {fmt_gp(row.get('profit_unit'))} | "
                        f"ROI: {fmt_pct(row.get('roi'))}"
                    )
                    st.write(
                        f"Trend: {row.get('trend', 'Flat')} | "
                        f"1D: {fmt_pct(row.get('chg_1d'))} | "
                        f"7D: {fmt_pct(row.get('chg_7d'))} | "
                        f"30D: {fmt_pct(row.get('chg_30d'))}"
                    )
                    st.write(f"Flags: {row.get('flags', 'Quiet')}")
                    st.divider()
        else:
            st.warning("No watchlist items found.")

    with tab5:
        st.subheader("Signals")
        if signals:
            signal_rows = []
            for row in signals:
                signal_rows.append(
                    {
                        "name": row.get("name"),
                        "reason": row.get("candidate_reason", ""),
                        "trend": row.get("trend"),
                        "1d": fmt_pct(row.get("chg_1d")),
                        "7d": fmt_pct(row.get("chg_7d")),
                        "profit": fmt_gp(row.get("profit_unit")),
                        "flags": row.get("flags"),
                    }
                )
            df = pd.DataFrame(signal_rows)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No signals found.")


if __name__ == "__main__":
    main()