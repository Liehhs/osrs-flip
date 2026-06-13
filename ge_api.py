import requests

BASE = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {"User-Agent": "OsrsFlipDashboard/Owen"}
TAX_RATE = 0.02
TAX_CAP = 5_000_000

WATCHLIST = [
    ("Twisted bow", "CoX BIS — permanently scarce; ranged PvM always relevant"),
    ("Scythe of vitur", "ToB BIS — BiS melee for slayer/raids; supply drains via charges"),
    ("Tumeken's shadow", "ToA BIS mage — meta-defining; no confirmed replacement"),
    ("Soulreaper axe", "Blood Moon drop; Raids 4 hype driving melee interest"),
    ("Osmumten's fang", "ToA — stab BIS; supply pressure from active ToA meta"),
    ("Harmonised orb", "CoX — mage BIS for NM/PvM; CoX changes can shift supply/demand"),
    ("Volatile orb", "CoX — high-value unique; affected by CoX prayer scroll reweight"),
    ("Eldritch orb", "CoX — affected by CoX prayer scroll reweight; supply dynamics shifting"),
    ("Dexterous prayer scroll", "CoX — prayer scroll reweight could shift value"),
    ("Arcane prayer scroll", "CoX — prayer scroll rate controversy; watch for rebalance"),
    ("Enhanced crystal weapon seed", "Corrupted Gauntlet — supply changes affect Bowfa ecosystem"),
    ("Ghrazi rapier", "ToB — buff/update-sensitive melee unique"),
    ("Sanguinesti staff (uncharged)", "ToB — buff/update-sensitive mage unique"),
    ("Avernic defender hilt", "ToB — tied to ToB/raids participation"),
    ("Necklace of anguish", "Ranged neck slot pressure from new gear / replacement risk"),
    ("Masori body (f)", "ToA range BIS — future range gear may displace it"),
    ("Masori chaps (f)", "ToA range BIS — same displacement risk as body"),
    ("Torva platebody", "Nex melee BIS — raid melee hype proxy"),
    ("Torva platelegs", "Nex melee BIS — raid melee hype proxy"),
    ("Bandos chestplate", "Mid-tier melee returning-player demand proxy"),
    ("Bandos tassets", "Mid-tier melee returning-player demand proxy"),
    ("Armadyl chestplate", "Mid-tier range baseline demand proxy"),
    ("Armadyl chainskirt", "Mid-tier range baseline demand proxy"),
    ("3rd age platebody", "Store-of-value / status flex; fixed supply"),
]

WATCHLIST_NAMES = [name for name, _ in WATCHLIST]
WATCHLIST_CATALYSTS = {name: catalyst for name, catalyst in WATCHLIST}

DISCOVERY_UNIVERSE = {
    "Zaryte crossbow": "High-end ranged utility; reacts to range meta shifts",
    "Dragon hunter lance": "Boss-specific melee demand proxy",
    "Dragon hunter crossbow": "Boss-specific ranged demand proxy",
    "Ancestral robe top": "Mage gear demand proxy",
    "Ancestral robe bottom": "Mage gear demand proxy",
    "Virtus robe top": "Mage hybrid demand proxy",
    "Virtus robe bottom": "Mage hybrid demand proxy",
    "Torva full helm": "Top-end melee demand proxy",
    "Justiciar faceguard": "Tank/melee demand proxy",
    "Elysian spirit shield": "Defensive prestige item / slow-moving high-value unique",
    "Zaryte vambraces": "Endgame ranged accessory proxy",
    "Inquisitor's mace": "Crush meta / boss demand proxy",
    "Inquisitor's hauberk": "Crush gear set demand proxy",
    "Inquisitor's plateskirt": "Crush gear set demand proxy",
}


def _get(path, timeout=14):
    response = requests.get(f"{BASE}{path}", headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_latest():
    return (_get("/latest") or {}).get("data") or {}


def fetch_mapping():
    return _get("/mapping") or []


def fetch_volumes():
    hour = (_get("/1h") or {}).get("data") or {}
    fmin = (_get("/5m") or {}).get("data") or {}
    return hour, fmin


def fetch_timeseries(item_id, timestep="24h"):
    try:
        return (_get(f"/timeseries?timestep={timestep}&id={item_id}") or {}).get("data") or []
    except Exception:
        return []


def tax(price):
    if price < 50:
        return 0
    return int(min(price * TAX_RATE, TAX_CAP))


def _extract_volume(bucket):
    if not bucket:
        return 0, 0
    if isinstance(bucket, dict):
        return int(bucket.get("highPriceVolume") or 0), int(bucket.get("lowPriceVolume") or 0)
    try:
        value = int(bucket)
        return value // 2, value // 2
    except (TypeError, ValueError):
        return 0, 0


def _vols(hour_bucket, fmin_bucket):
    buy_hour, sell_hour = _extract_volume(hour_bucket)
    if buy_hour > 0 or sell_hour > 0:
        return buy_hour, sell_hour
    buy_five, sell_five = _extract_volume(fmin_bucket)
    return buy_five * 12, sell_five * 12


def fill_quality(ratio):
    if ratio is None:
        return 0.3, "No data"
    if 0.8 <= ratio <= 1.5:
        return 1.0, "Ideal"
    if 1.5 < ratio <= 3.0:
        return 0.7, "High demand"
    if ratio > 3.0:
        return 0.4, "Hard to buy"
    if 0.4 <= ratio < 0.8:
        return 0.8, "Slight flood"
    return 0.5, "Flooded"


def build_rows(latest, mapping, hour_vols, fmin_vols):
    mapping_by_id = {item["id"]: item for item in mapping}
    rows = []

    for id_str, quote in latest.items():
        item = mapping_by_id.get(int(id_str))
        if not item:
            continue

        buy_price = quote.get("low") or 0
        sell_price = quote.get("high") or 0
        ge_limit = item.get("limit") or 0
        if not buy_price or not sell_price or not ge_limit or sell_price <= buy_price:
            continue

        item_tax = tax(sell_price)
        profit_unit = sell_price - buy_price - item_tax
        if profit_unit <= 0:
            continue

        roi = (profit_unit / buy_price) * 100
        buy_qty_hr, sell_qty_hr = _vols(hour_vols.get(id_str), fmin_vols.get(id_str))
        total_hr = buy_qty_hr + sell_qty_hr
        ratio = round(buy_qty_hr / sell_qty_hr, 2) if sell_qty_hr > 0 else None
        fq_mult, fq_label = fill_quality(ratio)
        potential_profit = profit_unit * ge_limit
        adj_potential = potential_profit * fq_mult
        fills_4hr = sell_qty_hr * 4
        realistic_units = min(ge_limit, max(1, fills_4hr)) if fills_4hr > 0 else ge_limit
        realistic_profit = profit_unit * realistic_units

        rows.append(
            {
                "id": int(id_str),
                "name": item["name"],
                "buy_price": buy_price,
                "sell_price": sell_price,
                "tax": item_tax,
                "profit_unit": profit_unit,
                "roi": round(roi, 2),
                "buy_qty_hr": buy_qty_hr,
                "sell_qty_hr": sell_qty_hr,
                "total_hr": total_hr,
                "ratio": ratio,
                "fq_label": fq_label,
                "fq_mult": fq_mult,
                "ge_limit": ge_limit,
                "potential_profit": potential_profit,
                "adj_potential": adj_potential,
                "realistic_profit": realistic_profit,
                "tax_cap": item_tax == TAX_CAP,
                "daily_volume": total_hr * 24,
                "trend": "Flat",
                "chg_1d": None,
                "chg_7d": None,
                "chg_30d": None,
                "flags": "Quiet",
                "priority": 0,
            }
        )
    return rows


def pct_change(current, previous):
    try:
        current = float(current)
        previous = float(previous)
        if previous <= 0:
            return None
        return round(((current - previous) / previous) * 100, 2)
    except Exception:
        return None


def classify_trend(chg_1d, chg_7d, chg_30d):
    chg_1d = chg_1d if chg_1d is not None else 0
    chg_7d = chg_7d if chg_7d is not None else 0
    chg_30d = chg_30d if chg_30d is not None else 0
    if chg_30d > 5 and chg_7d < 0 and chg_1d < 0:
        return "Pullback"
    if chg_30d > 15 and chg_7d > 5 and chg_1d > 2:
        return "Extended"
    if chg_30d > 5 and chg_7d > 0 and chg_1d > -1:
        return "Building"
    if chg_30d <= 0 and chg_7d < 0:
        return "Weakening"
    return "Flat"


def event_flags(item):
    flags = []
    chg_1d = item.get("chg_1d")
    chg_7d = item.get("chg_7d")
    chg_30d = item.get("chg_30d")
    roi = item.get("roi", 0) or 0
    buy_hr = item.get("buy_qty_hr", 0) or 0
    sell_hr = item.get("sell_qty_hr", 0) or 0
    ratio = item.get("ratio")
    profit = item.get("profit_unit", 0) or 0

    if chg_1d is not None and abs(chg_1d) >= 5:
        flags.append("1D shock")
    if chg_7d is not None and abs(chg_7d) >= 10:
        flags.append("7D move")
    if chg_30d is not None and abs(chg_30d) >= 15:
        flags.append("30D regime")
    if roi >= 8:
        flags.append("Wide spread")
    if profit >= 500_000:
        flags.append("High gp/item")
    if buy_hr + sell_hr >= 500:
        flags.append("Liquid")
    if ratio is not None and (ratio >= 2.0 or ratio <= 0.6):
        flags.append("Flow imbalance")

    priority = 0
    if "1D shock" in flags:
        priority += 3
    if "7D move" in flags:
        priority += 2
    if "30D regime" in flags:
        priority += 2
    if "Wide spread" in flags:
        priority += 2
    if "High gp/item" in flags:
        priority += 1
    if "Liquid" in flags:
        priority += 1
    if "Flow imbalance" in flags:
        priority += 1

    return ", ".join(flags[:4]) if flags else "Quiet", priority


def enrich_with_trends(rows):
    enriched = []
    for row in rows:
        item = dict(row)
        ts = fetch_timeseries(row["id"], "24h")
        if ts and len(ts) >= 31:
            highs = [point.get("avgHighPrice") or 0 for point in ts if point.get("avgHighPrice")]
            if len(highs) >= 31:
                current = highs[-1]
                item["chg_1d"] = pct_change(current, highs[-2])
                item["chg_7d"] = pct_change(current, highs[-8])
                item["chg_30d"] = pct_change(current, highs[-31])
                item["trend"] = classify_trend(item["chg_1d"], item["chg_7d"], item["chg_30d"])
        item["flags"], item["priority"] = event_flags(item)
        enriched.append(item)
    return enriched


def is_viable_bulk(row):
    buy_hr = row.get("buy_qty_hr", 0) or 0
    sell_hr = row.get("sell_qty_hr", 0) or 0
    ratio = row.get("ratio")
    ge_limit = row.get("ge_limit", 0) or 0
    profit = row.get("profit_unit", 0) or 0
    realistic_profit = row.get("realistic_profit", 0) or 0
    buy_price = row.get("buy_price", 0) or 0

    if buy_hr < 100 or sell_hr < 50:
        return False
    if ratio is None or ratio < 0.5 or ratio > 3.0:
        return False
    if min(ge_limit, sell_hr * 4) < max(100, ge_limit * 0.05):
        return False
    if profit < 100 or realistic_profit < 100_000 or buy_price < 500:
        return False
    return True


def compute_flips(latest, mapping, hour_vols, fmin_vols):
    rows = build_rows(latest, mapping, hour_vols, fmin_vols)
    rows_with_trends = enrich_with_trends(rows)

    bulk = sorted(
        [row for row in rows_with_trends if row["ge_limit"] >= 1000 and row["total_hr"] >= 200 and is_viable_bulk(row)],
        key=lambda row: (-row["profit_unit"], -row["fq_mult"], -row["ge_limit"], -row["roi"]),
    )[:60]

    singular = sorted(
        [row for row in rows_with_trends if row["ge_limit"] <= 15 and row["sell_price"] >= 500_000 and row["total_hr"] >= 1],
        key=lambda row: -(row["profit_unit"] * row["fq_mult"]),
    )[:40]

    high_roi = sorted(
        [row for row in rows_with_trends if row["total_hr"] >= 50 and row["roi"] >= 5],
        key=lambda row: -row["roi"],
    )[:40]

    all_by_name = {row["name"].lower(): row for row in rows_with_trends}
    watch = [all_by_name[name.lower()] for name in WATCHLIST_NAMES if name.lower() in all_by_name]
    watch = sorted(watch, key=lambda row: (-row.get("priority", 0), -row.get("profit_unit", 0), row["name"]))

    watch_names = {row["name"].lower() for row in watch}
    signals = [
        all_by_name[name.lower()]
        for name in DISCOVERY_UNIVERSE
        if name.lower() in all_by_name and name.lower() not in watch_names
    ]
    for signal in signals:
        signal["candidate_reason"] = DISCOVERY_UNIVERSE.get(signal["name"], "")
    signals = [signal for signal in signals if signal.get("priority", 0) >= 3]
    signals = sorted(
        signals,
        key=lambda row: (-row.get("priority", 0), -abs(row.get("chg_1d") or 0), -abs(row.get("chg_7d") or 0), -row.get("profit_unit", 0)),
    )[:12]

    return bulk, singular, high_roi, watch, signals, rows_with_trends