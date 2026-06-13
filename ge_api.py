import requests

BASE = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {"User-Agent": "OsrsFlipDashboard/Owen"}
GE_TAX_RATE = 0.02
GE_TAX_CAP  = 5_000_000

WATCHLIST_NAMES = [
    "Tumeken's shadow", "Twisted bow", "Torva platebody", "Torva platelegs",
    "Bandos chestplate", "Bandos tassets", "Armadyl chestplate",
    "Armadyl chainskirt", "Scythe of vitur", "Soulreaper axe",
]

BULK_MIN_LIMIT  = 1000
BULK_MIN_HOURLY = 300
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

def _vols(bucket):
    """Return (buy_qty_per_5m, sell_qty_per_5m) safely."""
    if not bucket:
        return 0, 0
    if isinstance(bucket, dict):
        return int(bucket.get("highPriceVolume") or 0), int(bucket.get("lowPriceVolume") or 0)
    try:
        v = int(bucket)
        return v // 2, v // 2
    except (TypeError, ValueError):
        return 0, 0


def compute_flips(latest, mapping, fivemin, cash_stack_gp):
    mapping_by_id = {item["id"]: item for item in mapping}
    rows = []

    for id_str, quote in latest.items():
        item = mapping_by_id.get(int(id_str))
        if not item:
            continue

        offer_price = quote.get("low")  or 0
        sell_price  = quote.get("high") or 0
        ge_limit    = item.get("limit") or 0

        if not offer_price or not sell_price or not ge_limit or sell_price <= offer_price:
            continue

        tax         = tax_on_sell(sell_price)
        profit_unit = sell_price - offer_price - tax
        if profit_unit <= 0:
            continue

        roi = (profit_unit / offer_price) * 100

        buy_5m, sell_5m = _vols(fivemin.get(id_str))
        buy_qty_hr  = buy_5m  * 12
        sell_qty_hr = sell_5m * 12
        total_hr    = buy_qty_hr + sell_qty_hr

        ratio = round(buy_qty_hr / sell_qty_hr, 2) if sell_qty_hr > 0 else None

        # 4-hour window: cap by GE limit, cash stack, and realistic seller-side fills
        affordable    = max(1, cash_stack_gp // offer_price)
        fills_4hr     = max(1, sell_qty_hr * 4)   # sellers available over 4 hrs
        cycle_units   = min(ge_limit, affordable, fills_4hr)
        window_profit = profit_unit * cycle_units  # total post-tax profit in 4-hr window

        rows.append({
            "name":         item["name"],
            "current_price": sell_price,
            "offer_price":  offer_price,
            "sell_price":   sell_price,
            "tax":          tax,
            "profit_unit":  profit_unit,
            "roi":          roi,
            "buy_qty_hr":   buy_qty_hr,
            "sell_qty_hr":  sell_qty_hr,
            "total_hr":     total_hr,
            "ratio":        ratio,
            "ge_limit":     ge_limit,
            "cycle_units":  cycle_units,
            "window_profit": window_profit,
            "tax_cap":      tax == GE_TAX_CAP,
        })

    bulk = sorted(
        [r for r in rows if r["ge_limit"] >= BULK_MIN_LIMIT and r["total_hr"] >= BULK_MIN_HOURLY],
        key=lambda x: -x["window_profit"]
    )[:30]

    singular = sorted(
        [r for r in rows
         if r["ge_limit"] <= SINGULAR_MAX_LIMIT
         and r["sell_price"] >= SINGULAR_MIN_PRICE
         and r["total_hr"] >= 1],
        key=lambda x: -x["profit_unit"]
    )[:25]

    all_by_name = {r["name"].lower(): r for r in rows}
    watch = [all_by_name[n.lower()] for n in WATCHLIST_NAMES if n.lower() in all_by_name]

    return bulk, singular, watch