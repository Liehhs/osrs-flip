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


def fetch_latest():
    r = requests.get(f"{BASE}/latest", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json().get("data", {})


def fetch_mapping():
    r = requests.get(f"{BASE}/mapping", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_5m():
    """5-minute bucket — gives highPriceVolume and lowPriceVolume as real trade counts."""
    r = requests.get(f"{BASE}/5m", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json().get("data", {})


def tax_on_sell(price: int) -> int:
    if price < 50:
        return 0
    return int(min(price * GE_TAX_RATE, GE_TAX_CAP))


def _vol_from_bucket(bucket) -> int:
    """Safely extract total trade count from a 5m bucket regardless of shape."""
    if bucket is None:
        return 0
    if isinstance(bucket, dict):
        high = bucket.get("highPriceVolume") or 0
        low = bucket.get("lowPriceVolume") or 0
        return int(high) + int(low)
    try:
        return int(bucket)
    except (TypeError, ValueError):
        return 0


def compute_flips(latest, mapping, fivemin, cash_stack_gp: int, bulk_min_limit: int, min_volume_5m: int):
    """
    Score every tradeable item and return:
      bulk     — high GE limit items ranked by realistic cycle GP
      singular — low limit (≤15) expensive items ranked by post-tax spread
      watch    — WATCHLIST_NAMES snapshots

    Liquidity gate: items must have at least `min_volume_5m` combined trades
    in the last 5-minute bucket before they are ranked. This kills illiquid
    noise (e.g. Unstrung comp bow with 0 buys/hour) regardless of spread size.
    """
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

        # 5-minute real trade velocity
        bucket = fivemin.get(id_str)
        vol_5m = _vol_from_bucket(bucket)
        # Estimated trades per hour (12 × 5-min buckets)
        vol_per_hour = vol_5m * 12

        # How many units we can actually afford per cycle
        affordable = max(1, cash_stack_gp // buy)
        # Cap by GE limit — don't promise more than the limit allows
        effective_limit = min(limit, affordable)

        # Realistic cycle GP = margin × min(effective_limit, estimated hourly fills)
        # Prevents illiquid items from showing fantasy cycle numbers
        realistic_fills = min(effective_limit, max(1, vol_per_hour // 2))
        cycle_gp = margin * realistic_fills

        rows.append({
            "id": int(id_str),
            "name": item["name"],
            "buy": buy,
            "sell": sell,
            "margin": margin,
            "roi": roi,
            "limit": limit,
            "vol_5m": vol_5m,
            "vol_per_hour": vol_per_hour,
            "effective_limit": effective_limit,
            "cycle_gp": cycle_gp,
            "tax_cap": tax == GE_TAX_CAP,
        })

    # ── Bulk flips ────────────────────────────────────────────────────────────
    # High limit items with real liquidity, sorted by realistic cycle GP
    bulk = sorted(
        [r for r in rows
         if r["limit"] >= bulk_min_limit
         and r["vol_5m"] >= min_volume_5m],
        key=lambda x: -x["cycle_gp"]
    )[:25]

    # ── Singular flips ────────────────────────────────────────────────────────
    # Low limit (≤15), price >500k, some real liquidity
    singular = sorted(
        [r for r in rows
         if r["limit"] <= 15
         and r["sell"] > 500_000
         and r["vol_5m"] >= 1],
        key=lambda x: -x["margin"]
    )[:25]

    # ── Watchlist ─────────────────────────────────────────────────────────────
    all_by_name = {r["name"].lower(): r for r in rows}
    watch = [all_by_name[n.lower()] for n in WATCHLIST_NAMES if n.lower() in all_by_name]

    return bulk, singular, watch