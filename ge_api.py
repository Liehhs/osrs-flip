import requests

BASE = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {"User-Agent": "OsrsFlipDashboard/Owen"}
TAX_RATE = 0.02
TAX_CAP = 5_000_000

WATCHLIST = [
    ("Twisted bow", "CoX BIS â€” permanently scarce; ranged PvM always relevant"),
    ("Scythe of vitur", "ToB BIS â€” BiS melee for slayer/raids; supply drains via charges"),
    ("Tumeken's shadow", "ToA BIS mage â€” meta-defining; no confirmed replacement"),
    ("Soulreaper axe", "Blood Moon drop; Raids 4 hype driving melee interest"),
    ("Osmumten's fang", "ToA â€” stab BIS; supply pressure from active ToA meta"),
    ("Harmonised orb", "CoX â€” mage BIS for NM/PvM; CoX changes can shift supply/demand"),
    ("Volatile orb", "CoX â€” high-value unique; affected by CoX prayer scroll reweight"),
    ("Eldritch orb", "CoX â€” affected by CoX prayer scroll reweight; supply dynamics shifting"),
    ("Dexterous prayer scroll", "CoX â€” prayer scroll reweight could shift value"),
    ("Arcane prayer scroll", "CoX â€” prayer scroll rate controversy; watch for rebalance"),
    ("Enhanced crystal weapon seed", "Corrupted Gauntlet â€” supply changes affect Bowfa ecosystem"),
    ("Ghrazi rapier", "ToB â€” buff/update-sensitive melee unique"),
    ("Sanguinesti staff (uncharged)", "ToB â€” buff/update-sensitive mage unique"),
    ("Avernic defender hilt", "ToB â€” tied to ToB/raids participation"),
    ("Necklace of anguish", "Ranged neck slot pressure from new gear / replacement risk"),
    ("Masori body (f)", "ToA range BIS â€” future range gear may displace it"),
    ("Masori chaps (f)", "ToA range BIS â€” same displacement risk as body"),
    ("Torva platebody", "Nex melee BIS â€” raid melee hype proxy"),
    ("Torva platelegs", "Nex melee BIS â€” raid melee hype proxy"),
    ("Bandos chestplate", "Mid-tier melee returning-player demand proxy"),
    ("Bandos tassets", "Mid-tier melee returning-player demand proxy"),
    ("Armadyl chestplate", "Mid-tier range baseline demand proxy"),
    ("Armadyl chainskirt", "Mid-tier range baseline demand proxy"),
    ("3rd age platebody", "Store-of-value / status flex; fixed supply"),
]

WATCHLIST_NAMES = [w[0] for w in WATCHLIST]
WATCHLIST_CATALYSTS = {w[0]: w[1] for w in WATCHLIST}

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
    r = requests.get(f"{BASE}{path}", headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()


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


def _vols(hour_bucket, fmin_bucket):
    def extract(b):
        if not b:
            return 0, 0
        if isinstance(b, dict):
            return int(b.get("highPriceVolume") or 0), int(b.get("lowPriceVolume") or 0)
        try:
            v = int(b)
            return v // 2, v // 2
        except (TypeError, ValueError):
            return 0, 0

    bh, sh = extract(hour_bucket)
    if bh > 0 or sh > 0:
        return bh, sh
    b5, s5 = extract(fmin_bucket)
    return b5 * 12, s5 * 12


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
        rows.append({
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
        })
    return rows


def pct_change(cur, prev):
    try:
        cur = float(cur)
        prev = float(prev)
        if prev <= 0:
            return None
        return round(((cur - prev) / prev) * 100, 2)
    except Exception:
        return None


def classify_trend(ch1, ch7, ch30):
    ch1 = ch1 if ch1 is not None else 0
    ch7 = ch7 if ch7 is not None else 0
    ch30 = ch30 if ch30 is not None else 0
    if ch30 > 5 and ch7 < 0 and ch1 < 0:
        return "Pullback"
    if ch30 > 5 and ch7 > 0 and ch1 > -1:
        return "Building"
    if ch30 > 15 and ch7 > 5 and ch1 > 2:
        return "Extended"
    if ch30 <= 0 and ch7 < 0:
        return "Weakening"
    return "Flat"


def event_flags(item):
    flags = []
    ch1 = item.get("chg_1d")
    ch7 = item.get("chg_7d")
    ch30 = item.get("chg_30d")
    roi = item.get("roi", 0) or 0
    buy_hr = item.get("buy_qty_hr", 0) or 0
    sell_hr = item.get("sell_qty_hr", 0) or 0
    ratio = item.get("ratio")
    profit = item.get("profit_unit", 0) or 0

    if ch1 is not None and abs(ch1) >= 5:
        flags.append("1D shock")
    if ch7 is not None and abs(ch7) >= 10:
        flags.append("7D move")
    if ch30 is not None and abs(ch30) >= 15:
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

    return flags[:4], priority


def enrich_with_trends(rows):
    enriched = []
    for r in rows:
        item = dict(r)
        ts = fetch_timeseries(r["id"], "24h")
        item["chg_1d"] = item["chg_7d"] = item["chg_30d"] = None
        item["trend"] = "Flat"
        if ts and len(ts) >= 31:
            highs = [p.get("avgHighPrice") or 0 for p in ts if p.get("avgHighPrice")]
            if len(highs) >= 31:
                cur = highs[-1]
                item["chg_1d"] = pct_change(cur, highs[-2])
                item["chg_7d"] = pct_change(cur, highs[-8])
                item["chg_30d"] = pct_change(cur, highs[-31])
                item["trend"] = classify_trend(item["chg_1d"], item["chg_7d"], item["chg_30d"])
        flags, priority = event_flags(item)
        item["flags"] = ", ".join(flags) if flags else "Quiet"
        item["priority"] = priority
        enriched.append(item)
    return enriched


def is_viable_bulk(r):
    buy_hr = r.get("buy_qty_hr", 0) or 0
    sell_hr = r.get("sell_qty_hr", 0) or 0
    ratio = r.get("ratio")
    ge = r.get("ge_limit", 0) or 0
    profit = r.get("profit_unit", 0) or 0
    realistic = r.get("realistic_profit", 0) or 0
    buy_price = r.get("buy_price", 0) or 0

    if buy_hr < 100 or sell_hr < 50:
        return False
    if ratio is None or ratio < 0.5 or ratio > 3.0:
        return False
    if min(ge, sell_hr * 4) < max(100, ge * 0.05):
        return False
    if profit < 100 or realistic < 100_000 or buy_price < 500:
        return False
    return True


def compute_flips(latest, mapping, hour_vols, fmin_vols):
    rows = build_rows(latest, mapping, hour_vols, fmin_vols)

    bulk = sorted(
        [r for r in rows if r["ge_limit"] >= 1000 and r["total_hr"] >= 200 and is_viable_bulk(r)],
        key=lambda x: (-x["profit_unit"], -x["fq_mult"], -x["ge_limit"], -x["roi"]),
    )[:60]
    singular = sorted(
        [r for r in rows if r["ge_limit"] <= 15 and r["sell_price"] >= 500_000 and r["total_hr"] >= 1],
        key=lambda x: -(x["profit_unit"] * x["fq_mult"]),
    )[:40]
    high_roi = sorted(
        [r for r in rows if r["total_hr"] >= 50 and r["roi"] >= 5],
        key=lambda x: -x["roi"],
    )[:40]

    all_by_name = {r["name"].lower(): r for r in rows}

    watch = [all_by_name[n.lower()] for n in WATCHLIST_NAMES if n.lower() in all_by_name]
    watch = enrich_with_trends(watch)
    watch = sorted(watch, key=lambda r: (-r.get("priority", 0), -r.get("profit_unit", 0), r["name"]))

    watch_names = {w["name"].lower() for w in watch}
    candidates = [
        all_by_name[n.lower()]
        for n in DISCOVERY_UNIVERSE
        if n.lower() in all_by_name and n.lower() not in watch_names
    ]
    candidates = enrich_with_trends(candidates)
    for c in candidates:
        c["candidate_reason"] = DISCOVERY_UNIVERSE.get(c["name"], "")
    candidates = [c for c in candidates if c.get("priority", 0) >= 3]
    candidates = sorted(
        candidates,
        key=lambda r: (-r.get("priority", 0), -abs(r.get("chg_1d") or 0), -abs(r.get("chg_7d") or 0), -r.get("profit_unit", 0)),
    )[:12]

    return bulk, singular, high_roi, watch, candidates, rows