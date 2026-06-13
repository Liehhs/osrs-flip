import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
from ge_api import fetch_latest, fetch_mapping, fetch_5m, compute_flips, WATCHLIST_NAMES

st.set_page_config(page_title="OSRS Flip Dashboard", layout="wide", page_icon="📈")

st.markdown("""
<style>
  html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
  section[data-testid="stSidebar"] { background: #0f172a; }
  section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
  section[data-testid="stSidebar"] label {
    font-size: 0.7rem !important; text-transform: uppercase;
    letter-spacing: 0.07em; color: #94a3b8 !important;
  }
  [data-testid="stMetric"] {
    background: #1e293b; border: 1px solid #334155;
    border-radius: 10px; padding: 1rem 1.25rem;
  }
  [data-testid="stMetricLabel"] { font-size: 0.7rem !important; text-transform: uppercase; color: #94a3b8 !important; }
  [data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 700; color: #f1f5f9 !important; }
  .section-label {
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.1em;
    color: #475569; border-bottom: 1px solid #1e293b;
    padding-bottom: 0.3rem; margin: 1.6rem 0 0.5rem 0;
  }
  .note { font-size: 0.75rem; color: #64748b; margin-bottom: 0.75rem; }
  .timing-green  { background:#052e16; border:1px solid #166534; border-radius:8px; padding:0.6rem 1rem; color:#bbf7d0; font-size:0.85rem; }
  .timing-yellow { background:#1c1700; border:1px solid #92400e; border-radius:8px; padding:0.6rem 1rem; color:#fde68a; font-size:0.85rem; }
  .timing-red    { background:#1f0606; border:1px solid #991b1b; border-radius:8px; padding:0.6rem 1rem; color:#fecaca; font-size:0.85rem; }
  div[data-testid="stSidebar"] .stButton button {
    background: #2563eb; color: white; border: none;
    border-radius: 8px; font-weight: 600; width: 100%; padding: 0.65rem; margin-top: 0.75rem;
  }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


def fmt_gp(n):
    if n is None: return "—"
    n = int(n)
    if n >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:     return f"{n/1_000_000:.2f}M"
    if n >= 1_000:         return f"{n/1_000:.1f}K"
    return f"{n:,}"

def get_timing():
    est = pytz.timezone("America/New_York")
    now = datetime.now(est)
    h, ts = now.hour, now.strftime("%I:%M %p ET")
    if 14 <= h < 22:
        return "green",  f"🟢  Sell window — Peak US/EU overlap. Best time to exit positions. ({ts})"
    elif 6 <= h < 14:
        return "yellow", f"🟡  Transition window — Moderate activity. Selective orders fine. ({ts})"
    else:
        return "red",    f"🔴  Buy window — Off-peak. Place buy offers now, sell into the afternoon. ({ts})"

def ratio_str(r):
    """Color-coded ratio display. ~1.0 = ideal, extremes = warnings."""
    if r is None: return "— no data"
    if 0.8 <= r <= 1.5:   return f"✅ {r:.2f}"
    elif 1.5 < r <= 3.0:  return f"🔼 {r:.2f}"
    elif r > 3.0:          return f"🔴 {r:.2f}"
    elif 0.4 <= r < 0.8:  return f"🟡 {r:.2f}"
    else:                  return f"🔴 {r:.2f}"

def fq_str(label, mult):
    icons = {
        "Ideal":        "✅ Ideal",
        "High demand":  "🔼 High demand",
        "Hard to buy":  "🔴 Hard to buy",
        "Slight flood": "🟡 Slight flood",
        "Flooded":      "🔴 Flooded",
        "No data":      "— No data",
    }
    return icons.get(label, label)

def to_df(rows, include_window=False):
    out = []
    for r in rows:
        row = {
            "Item":             r["name"],
            "Offer Price":      r["offer_price"],
            "Sell Price":       r["sell_price"],
            "Tax (gp)":         r["tax"],
            "Profit / unit":    r["profit_unit"],
            "ROI %":            round(r["roi"], 2),
            "Buy Qty / hr":     r["buy_qty_hr"],
            "Sell Qty / hr":    r["sell_qty_hr"],
            "B/S Ratio":        ratio_str(r["ratio"]),
            "Fill Quality":     fq_str(r["fq_label"], r["fq_mult"]),
            "GE Limit":         r["ge_limit"],
        }
        if include_window:
            row["4hr Window Profit"] = r["window_profit"]
            row["Adj. Profit"]       = r["adjusted_profit"]
        out.append(row)
    return pd.DataFrame(out)

NUM_FMT = {
    "Offer Price":       "{:,.0f}",
    "Sell Price":        "{:,.0f}",
    "Tax (gp)":          "{:,.0f}",
    "Profit / unit":     "{:,.0f}",
    "ROI %":             "{:.2f}",
    "Buy Qty / hr":      "{:,.0f}",
    "Sell Qty / hr":     "{:,.0f}",
    "GE Limit":          "{:,.0f}",
    "4hr Window Profit": "{:,.0f}",
    "Adj. Profit":       "{:,.0f}",
}


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚔️ FlipOSRS")
    st.markdown("<div style='font-size:0.74rem;color:#475569;margin-bottom:1.5rem'>Live Grand Exchange Scanner</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Cash Stack</div>", unsafe_allow_html=True)
    cash_m = st.number_input(
        "Amount in millions of GP",
        min_value=1.0, max_value=100000.0, value=100.0, step=0.5,
        help="100 = 100M GP. Decimals OK (e.g. 150.7 = 150.7M)"
    )
    cash_stack_gp = int(cash_m * 1_000_000)
    st.caption(f"= {cash_stack_gp:,} GP")
    st.markdown("<div class='section-label'>Actions</div>", unsafe_allow_html=True)
    refresh = st.button("🔄  Update live data", use_container_width=True)
    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.68rem;color:#334155;line-height:1.9'>"
        "<b>B/S Ratio = buy qty ÷ sell qty</b><br>"
        "✅ 0.8–1.5 → Ideal (balanced fills)<br>"
        "🔼 1.5–3.0 → High demand (slow to buy in)<br>"
        "🔴 &gt;3.0 → Hard to buy (buy offer sits)<br>"
        "🟡 0.4–0.8 → Slight flood (harder to sell)<br>"
        "🔴 &lt;0.4 → Flooded (selling is painful)<br><br>"
        "Ranked by <b>Adj. Profit</b> = 4hr window × fill quality multiplier<br><br>"
        "Tax: 2% on seller · 5M GP hard cap<br>"
        "Trades/hr = 5-min bucket × 12"
        "</div>", unsafe_allow_html=True
    )


# ── Header ────────────────────────────────────────────────────────────────────
col_h, col_ts = st.columns([3, 1])
with col_h:
    st.markdown("## OSRS Grand Exchange — Live Flip Dashboard")
with col_ts:
    if "updated" in st.session_state:
        st.markdown(
            f"<div style='text-align:right;color:#475569;font-size:0.75rem;padding-top:0.7rem'>"
            f"Last updated: {st.session_state['updated']}</div>",
            unsafe_allow_html=True
        )

tw_color, tw_msg = get_timing()
st.markdown(f"<div class='timing-{tw_color}'>{tw_msg}</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)


# ── Data fetch ────────────────────────────────────────────────────────────────
if refresh or "data" not in st.session_state:
    with st.spinner("Fetching live GE data…"):
        try:
            latest  = fetch_latest()
            mapping = fetch_mapping()
            fivemin = fetch_5m()
            result  = compute_flips(latest, mapping, fivemin, cash_stack_gp)
            st.session_state["data"]    = result
            st.session_state["updated"] = datetime.now().strftime("%b %d %Y, %I:%M %p")
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

if "data" not in st.session_state:
    st.info("👆 Click **Update live data** to begin.")
    st.stop()

bulk, singular, watch = st.session_state["data"]


# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Best Bulk — Adj. Profit",   fmt_gp(bulk[0]["adjusted_profit"]) if bulk else "—",   bulk[0]["name"] if bulk else "")
k2.metric("Best Bulk — ROI",           f"{bulk[0]['roi']:.2f}%" if bulk else "—",             f"{fmt_gp(bulk[0]['profit_unit'])} / unit" if bulk else "")
k3.metric("Best Singular — Profit",    fmt_gp(singular[0]["profit_unit"]) if singular else "—", singular[0]["name"] if singular else "")
k4.metric("Watchlist Items Found",     str(len(watch)),                                        f"of {len(WATCHLIST_NAMES)} tracked")
k5.metric("Cash Stack",                f"{cash_m:,.1f}M GP",                                   f"{cash_stack_gp:,} GP")

st.markdown("<br>", unsafe_allow_html=True)


# ── Legend ────────────────────────────────────────────────────────────────────
with st.expander("📖  B/S Ratio & Fill Quality guide", expanded=False):
    st.markdown("""
| B/S Ratio | Label | What it means | Action |
|---|---|---|---|
| ✅ 0.8 – 1.5 | **Ideal** | Balanced market — both sides fill predictably | Best candidates |
| 🔼 1.5 – 3.0 | **High demand** | More buyers than sellers — item sells fast but buy offers may sit | OK — factor in wait time |
| 🔴 > 3.0 | **Hard to buy** | Extreme demand spike — buy offers will sit a long time | Avoid unless patient |
| 🟡 0.4 – 0.8 | **Slight flood** | More sellers than buyers — sells slower, price may drift down | Proceed with caution |
| 🔴 < 0.4 | **Flooded** | Market dumped — very hard to sell at your listed price | Avoid |

**Adj. Profit** = 4-hour window profit × fill quality multiplier. Items ranked by this — not raw profit — so a high-spread item in a flooded market ranks below a moderate-spread item with balanced fills.
    """)


# ── Bulk flips ────────────────────────────────────────────────────────────────
st.markdown("<div class='section-label'>Recommended bulk flips — herbs, pots, runes, supplies</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='note'>"
    "GE limit ≥1,000 · ≥300 trades/hr · ranked by <b>Adj. Profit</b> "
    "(4hr window profit × fill quality multiplier) — not raw spread"
    "</div>",
    unsafe_allow_html=True
)

if bulk:
    df_b = to_df(bulk, include_window=True)
    st.dataframe(
        df_b.style.format({k: v for k, v in NUM_FMT.items() if k in df_b.columns}),
        use_container_width=True, hide_index=True,
    )
    fig = px.bar(
        df_b.head(12), x="Item", y="Adj. Profit",
        color="ROI %", color_continuous_scale="teal",
        title="Top 12 bulk flips — demand-adjusted 4hr profit",
        template="plotly_dark",
    )
    fig.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
        title_font_size=13, xaxis_tickangle=-35, margin=dict(t=45, b=70),
        yaxis_title="Adj. Profit (gp)"
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No bulk items found. 5-min data may be sparse — try refreshing in a moment.")


# ── Singular flips ────────────────────────────────────────────────────────────
st.markdown("<div class='section-label'>Best singular flips — low limit, high profit per unit</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='note'>"
    "GE limit ≤15 · price >500K GP · ranked by demand-adjusted profit per unit · slow fills expected"
    "</div>",
    unsafe_allow_html=True
)

if singular:
    df_s = to_df(singular, include_window=False)
    st.dataframe(
        df_s.style.format({k: v for k, v in NUM_FMT.items() if k in df_s.columns}),
        use_container_width=True, hide_index=True,
    )
else:
    st.info("No singular items found in this data pull.")


# ── Watchlist ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-label'>Investment watchlist — live snapshot</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='note'>"
    "Tumeken's Shadow · Twisted Bow · Torva · Bandos · Armadyl · Scythe · Soulreaper Axe"
    "</div>",
    unsafe_allow_html=True
)

if watch:
    df_w = to_df(watch, include_window=False)
    st.dataframe(
        df_w.style.format({k: v for k, v in NUM_FMT.items() if k in df_w.columns}),
        use_container_width=True, hide_index=True,
    )
    fig_w = px.bar(
        df_w, x="Item", y="Profit / unit",
        color="ROI %", color_continuous_scale="oranges",
        title="Watchlist — post-tax profit per unit",
        template="plotly_dark",
    )
    fig_w.update_layout(
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font_color="#cbd5e1",
        title_font_size=13, xaxis_tickangle=-30, margin=dict(t=45, b=80),
        yaxis_title="Profit / unit (gp)"
    )
    fig_w.update_traces(marker_line_width=0)
    st.plotly_chart(fig_w, use_container_width=True)
else:
    st.info("No watchlist items returned in this pull.")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='font-size:0.7rem;color:#334155;text-align:center'>"
    "OSRS Wiki Real-Time Prices API · 2% GE tax (5M GP cap) · "
    "Trades/hr = 5-min bucket × 12 · Adj. Profit = window profit × fill quality · Fills not guaranteed"
    "</div>", unsafe_allow_html=True
)