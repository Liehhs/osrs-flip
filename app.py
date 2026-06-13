import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
from ge_api import fetch_latest, fetch_mapping, fetch_volumes, compute_flips

WATCHLIST = [
    "Tumeken's shadow", "Twisted bow", "Torva platebody", "Torva platelegs",
    "Bandos chestplate", "Bandos tassets", "Armadyl chestplate",
    "Armadyl chainskirt", "Scythe of vitur", "Soulreaper axe"
]

st.set_page_config(page_title="OSRS Flip Dashboard", layout="wide", page_icon="📈")
st.title("OSRS Grand Exchange — Live Flip Dashboard")

# Sidebar controls
with st.sidebar:
    st.header("Filters")
    cash_stack = st.number_input("Cash stack (GP)", min_value=1_000_000, step=1_000_000, value=50_000_000)
    bulk_min_limit = st.number_input("Bulk min GE limit", min_value=100, step=100, value=2000)
    min_roi = st.slider("Min ROI %", 0.0, 20.0, 3.0, 0.1)
    min_volume = st.number_input("Min daily volume", min_value=0, step=100, value=500)
    refresh = st.button("🔄 Update live data", use_container_width=True)

def get_timing():
    est = pytz.timezone("America/New_York")
    now = datetime.now(est)
    h = now.hour
    if 14 <= h < 22:
        return "🟢 Sell window", "Peak US/EU overlap. Best to exit positions."
    elif 6 <= h < 14:
        return "🟡 Transition window", "Moderate activity. Selective orders OK."
    else:
        return "🔴 Buy window", "Off-peak. Place buy offers overnight."

# Run on first load OR button press
if refresh or "data" not in st.session_state:
    with st.spinner("Fetching live GE data..."):
        latest = fetch_latest()
        mapping = fetch_mapping()
        volumes = fetch_volumes()
        bulk, singular = compute_flips(latest, mapping, volumes, cash_stack, bulk_min_limit, min_roi, min_volume)
        all_by_name = {r["name"].lower(): r for r in bulk + singular}
        watch = [all_by_name.get(n.lower()) for n in WATCHLIST if all_by_name.get(n.lower())]
        st.session_state["data"] = (bulk, singular, watch)
        st.session_state["updated"] = datetime.now().strftime("%b %d, %Y %I:%M %p")

if "data" not in st.session_state:
    st.info("Click 'Update live data' to load the market.")
    st.stop()

bulk, singular, watch = st.session_state["data"]
st.caption(f"Last updated: {st.session_state.get('updated', '—')}")

# Timing
tw_label, tw_copy = get_timing()
st.info(f"**{tw_label}** — {tw_copy}")

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Best bulk cycle GP", f"{bulk[0]['cycle_gp']:,.0f} gp" if bulk else "—", bulk[0]["name"] if bulk else "")
c2.metric("Best singular spread", f"{singular[0]['margin']:,.0f} gp" if singular else "—", singular[0]["name"] if singular else "")
c3.metric("Watchlist items found", str(len(watch)))
c4.metric("Cash stack", f"{cash_stack:,.0f} gp")

# Bulk table
st.subheader("Best bulk flips — ranked by 4-hour cycle GP")
if bulk:
    df_bulk = pd.DataFrame(bulk)[["name","buy","sell","margin","roi","limit","volume","cycle_gp","tax_cap"]]
    df_bulk.columns = ["Item","Buy","Sell","Margin","ROI %","GE Limit","Volume","Cycle GP","Tax Cap"]
    st.dataframe(df_bulk.style.format({"Buy":"{:,.0f}","Sell":"{:,.0f}","Margin":"{:,.0f}","ROI %":"{:.2f}","Volume":"{:,.0f}","Cycle GP":"{:,.0f}"}), use_container_width=True)

    fig = px.bar(df_bulk.head(10), x="Item", y="Cycle GP", title="Top 10 bulk items — cycle GP", color="ROI %", color_continuous_scale="Teal")
    st.plotly_chart(fig, use_container_width=True)

# Singular table
st.subheader("Best singular flips — ranked by post-tax spread")
if singular:
    df_sing = pd.DataFrame(singular)[["name","buy","sell","margin","roi","limit","volume","tax_cap"]]
    df_sing.columns = ["Item","Buy","Sell","Margin","ROI %","Limit","Volume","Tax Cap"]
    st.dataframe(df_sing.style.format({"Buy":"{:,.0f}","Sell":"{:,.0f}","Margin":"{:,.0f}","ROI %":"{:.2f}","Volume":"{:,.0f}"}), use_container_width=True)

# Watchlist
st.subheader("Investment watchlist — live snapshot")
if watch:
    df_watch = pd.DataFrame(watch)[["name","sell","buy","margin","roi","limit","volume"]]
    df_watch.columns = ["Item","Price (sell)","Buy","Spread","ROI %","Limit","Volume"]
    st.dataframe(df_watch.style.format({"Price (sell)":"{:,.0f}","Buy":"{:,.0f}","Spread":"{:,.0f}","ROI %":"{:.2f}","Volume":"{:,.0f}"}), use_container_width=True)