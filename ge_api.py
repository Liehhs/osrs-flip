import requests

BASE = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {"User-Agent": "OsrsFlipDashboard/Owen"}
GE_TAX_RATE = 0.02
GE_TAX_CAP = 5_000_000

WATCHLIST_NAMES = [
    "Tumeken's shadow", "Twisted bow", "Torva platebody", "Torva platelegs",
    "Bandos chestplate", "Bandos tassets", "Armadyl chestplate",
    "Armadyl chainskirt", "Scythe of vitur", "Soulreaper axe"
]

# Bulk = high GE limit consumables/supplies with real hourly liquidity
BULK_MIN_LIMIT   = 1000
BULK_MIN_HOURLY  = 300   # estimated trades/hr floor

# Singular = expensive, low-limit slow flips
SINGULAR_MAX_LIMIT = 15
SINGULAR_MIN_PRICE = 500_000


def _get(path, timeout=12):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_latest():
    return (_get("/latest") or {}).get("data") or {}


def fetch_mapping():
    return _get("/mapping") or []


def fetch_5m():
    return (_get("/5m") or {}).get("data") or {}


def tax_on_sell(price):
    if price < 50:
        return 0
    return int(min(price * GE_TAX_RATE, GE_TAX_CAP))


def _extract_vol(bucket):
    """Safely pull trade count from a 5m bucket — handles dict or raw int."""
    if not bucket:
        return 0, 0
    if isinstance(bucket, dict):
        high = int(bucket.get("highPriceVolume") or 0)
        low  = int(bucket.get("lowPriceVolume")  or 0)
        return high, low
    try:
        v = int(bucket)
        return v // 2, v // 2
    except (TypeError, ValueError):
        return 0, 0


def _build_row(id_str, quote, item, bucket):
    """Return a scored row dict, or None if item is not worth showing."""
    buy   = quote.get("low")  or 0
    sell  = quote.get("high") or 0
    limit = item.get("limit") or 0

    if not buy or not sell or not limit or sell <= buy:
        return None

    tax    = tax_on_sell(sell)
    profit = sell - buy - tax   # post-tax profit per unit
    if profit <= 0:
        return None

    roi = (profit / buy) * 100

    # 5-minute volumes → per-hour estimates
    high_vol_5m, low_vol_5m = _extract_vol(bucket)
    buy_qty_hr  = high_vol_5m * 12   # how many people are buying  (insta-buy fills)
    sell_qty_hr = low_vol_5m  * 12   # how many people are selling (insta-sell fills)
    total_hr    = buy_qty_hr + sell_qty_hr

    # Buy/Sell ratio — below 1.0 means more sellers than buyers (bad for flipping)
    ratio = round(buy_qty_hr / sell_qty_hr, 2) if sell_qty_hr > 0 else None

    # 4-hour window potential:
    # max units you can move = min(GE limit, what you can afford, realistic fills in 4 hrs)
    # realistic fills in 4 hrs ≈ sell_qty_hr * 4  (you're buying what sellers are selling)
    affordable_units   = max(1, 0)   # placeholder; cash stack applied in compute_flips
    fills_4hr          = sell_qty_hr * 4
    # cycle_potential is set per-item in compute_flips with cash_stack applied

    return {
        "id":           int(id_str),
        "name":         item["name"],
        "current_price": sell,          # last known price
        "offer_price":  buy,            # what you offer to buy at
        "sell_price":   sell,           # what you list to sell at
        "tax":          tax,
        "profit":       profit,         # post-tax profit per unit
        "roi":          roi,
        "limit":        limit,
        "buy_qty_hr":   buy_qty_hr,
        "sell_qty_hr":  sell_qty_hr,
        "total_hr":     total_hr,
        "ratio":        ratio,
        "fills_4hr":    fills_4hr,
        "tax_cap":      tax == GE_TAX_CAP,
    }


def compute_flips(latest, mapping, fivemin, cash_stack_gp):
    mapping_by_id = {item["id"]: item for item in mapping}
    rows = []

    for id_str, quote in latest.items():
        item = mapping_by_id.get(int(id_str))
        if not item:
            continue
        row = _build_row(id_str, quote, item, fivemin.get(id_str))
        if row is None:
            continue

        # Apply cash stack to cap units affordable
        affordable = max(1, cash_stack_gp // row["offer_price"])
        # 4-hour window: limited by GE limit, what we can afford, and realistic fills
        fills_4hr   = row["fills_4hr"] if row["fills_4hr"] > 0 else row["limit"]
        cycle_units = min(row["limit"], affordable, max(1, fills_4hr))
        row["cycle_units"]  = cycle_units
        row["cycle_profit"] = row["profit"] * cycle_units   # total post-tax profit in window

        rows.append(row)

    # ── Bulk ──────────────────────────────────────────────────────────────────
    # High-limit, genuinely liquid items (herbs, pots, runes, bars, etc.)
    # Ranked by total post-tax profit over the 4-hour GE window
    bulk = sorted(
        [r for r in rows
         if r["limit"] >= BULK_MIN_LIMIT
         and r["total_hr"] >= BULK_MIN_HOURLY],
        key=lambda x: -x["cycle_profit"]
    )[:30]

    # ── Singular ──────────────────────────────────────────────────────────────
    # Low-limit expensive items — ranked by profit per unit (since limit is tiny)
    singular = sorted(
        [r for r in rows
         if r["limit"] <= SINGULAR_MAX_LIMIT
         and r["sell_price"] >= SINGULAR_MIN_PRICE
         and (r["buy_qty_hr"] + r["sell_qty_hr"]) >= 1],
        key=lambda x: -x["profit"]
    )[:25]

    # ── Watchlist ─────────────────────────────────────────────────────────────
    # Always pulled from full rows — no liquidity filter
    all_by_name = {r["name"].lower(): r for r in rows}
    watch = [all_by_name[n.lower()] for n in WATCHLIST_NAMES if n.lower() in all_by_name]

    return bulk, singular, watch