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

# Bulk = genuinely high-volume consumables and supplies.
# GE limit >= 1000 AND estimated trades/hr >= 500.
BULK_MIN_LIMIT = 1000
BULK_MIN_HOURLY = 500

# Singular = expensive slow items with a fat spread.
SINGULAR_MAX_LIMIT = 15
SINGULAR_MIN_PRICE = 500_000


def _get(path, timeout=12):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_latest():
    data = _get("/latest")
    return data.get("data") or {}


def fetch_mapping():
    return _get("/mapping") or []


def fetch_5m():
    data = _get("/5m")
    return data.get("data") or {}


def tax_on_sell(price):
    if price < 50:
        return 0
    return int(min(price * GE_TAX_RATE, GE_TAX_CAP))


def _vol_5m(bucket):
    if not bucket:
        return 0
    if isinstance(bucket, dict):
        return int(bucket.get("highPriceVolume") or 0) + int(bucket.get("lowPriceVolume") or 0)
    try:
        return int(bucket)
    except (TypeError, ValueError):
        return 0


def compute_flips(latest, mapping, fivemin, cash_stack_gp):
    mapping_by_id = {item["id"]: item for item in mapping}
    rows = []

    for id_str, quote in latest.items():
        item = mapping_by_id.get(int(id_str))
        if not item:
            continue
        buy = quote.get("low") or 0
        sell = quote.get("high") or 0
        limit = item.get("limit") or 0
        if not buy or not sell or not limit or sell <= buy:
            continue

        tax = tax_on_sell(sell)
        margin = sell - buy - tax
        if margin <= 0:
            continue

        roi = (margin / buy) * 100
        vol_5m = _vol_5m(fivemin.get(id_str))
        vol_per_hour = vol_5m * 12

        affordable = max(1, cash_stack_gp // buy)
        effective_limit = min(limit, affordable)
        realistic_fills = min(effective_limit, max(1, vol_per_hour // 2))
        cycle_gp = margin * realistic_fills

        rows.append({
            "id":             int(id_str),
            "name":           item["name"],
            "buy":            buy,
            "sell":           sell,
            "margin":         margin,
            "roi":            roi,
            "limit":          limit,
            "vol_5m":         vol_5m,
            "vol_per_hour":   vol_per_hour,
            "effective_limit": effective_limit,
            "cycle_gp":       cycle_gp,
            "tax_cap":        tax == GE_TAX_CAP,
        })

    # Bulk: high limit + genuinely liquid (herbs, pots, runes, supplies)
    bulk = sorted(
        [r for r in rows
         if r["limit"] >= BULK_MIN_LIMIT
         and r["vol_per_hour"] >= BULK_MIN_HOURLY],
        key=lambda x: -x["cycle_gp"]
    )[:30]

    # Singular: low limit, expensive, any real recent activity
    singular = sorted(
        [r for r in rows
         if r["limit"] <= SINGULAR_MAX_LIMIT
         and r["sell"] >= SINGULAR_MIN_PRICE
         and r["vol_5m"] >= 1],
        key=lambda x: -x["margin"]
    )[:25]

    # Watchlist: always pull from full rows regardless of filters
    all_by_name = {r["name"].lower(): r for r in rows}
    watch = [all_by_name[n.lower()] for n in WATCHLIST_NAMES if n.lower() in all_by_name]

    return bulk, singular, watch