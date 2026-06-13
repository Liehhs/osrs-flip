import requests

BASE = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {"User-Agent": "OsrsFlipDashboard/Owen"}
GE_TAX_RATE = 0.02
GE_TAX_CAP = 5_000_000

def fetch_latest():
    return requests.get(f"{BASE}/latest", headers=HEADERS).json()["data"]

def fetch_mapping():
    return requests.get(f"{BASE}/mapping", headers=HEADERS).json()

def fetch_volumes():
    return requests.get(f"{BASE}/volumes", headers=HEADERS).json()["data"]

def fetch_timeseries(item_id, timestep="24h"):
    return requests.get(f"{BASE}/timeseries", headers=HEADERS, params={"timestep": timestep, "id": item_id}).json()

def tax_on_sell(price):
    if price < 50:
        return 0
    return min(price * GE_TAX_RATE, GE_TAX_CAP)

def compute_flips(latest, mapping, volumes, cash_stack=50_000_000, bulk_min_limit=2000, min_roi=3.0, min_volume=500):
    mapping_by_id = {item["id"]: item for item in mapping}
    rows = []
    for id_str, quote in latest.items():
        item_id = int(id_str)
        item = mapping_by_id.get(item_id)
        if not item or not quote.get("high") or not quote.get("low"):
            continue
        buy = quote["low"]
        sell = quote["high"]
        limit = item.get("limit", 0)
        if not limit or sell <= buy:
            continue
        tax = tax_on_sell(sell)
        margin = sell - buy - tax
        if margin <= 0:
            continue
        roi = (margin / buy) * 100
        volume = volumes.get(id_str, {})
        daily_vol = (volume.get("highPriceVolume", 0) or 0) + (volume.get("lowPriceVolume", 0) or 0)
        effective_limit = min(limit, max(1, int(cash_stack // buy)))
        rows.append({
            "id": item_id, "name": item["name"], "buy": buy, "sell": sell,
            "margin": margin, "roi": roi, "limit": limit, "volume": daily_vol,
            "cycle_gp": margin * effective_limit, "tax_cap": tax == GE_TAX_CAP,
            "effective_limit": effective_limit
        })
    bulk = sorted([r for r in rows if r["limit"] >= bulk_min_limit and r["roi"] >= min_roi and r["volume"] >= min_volume], key=lambda x: -x["cycle_gp"])[:20]
    singular = sorted([r for r in rows if r["limit"] <= 15 and r["sell"] > 500_000 and r["roi"] > 0.5], key=lambda x: -x["margin"])[:20]
    return bulk, singular