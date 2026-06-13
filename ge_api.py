import requests

BASE    = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {"User-Agent": "OsrsFlipDashboard/Owen"}
TAX_RATE = 0.02
TAX_CAP  = 5_000_000

# ── Watchlist ──────────────────────────────────────────────────────────────────
WATCHLIST = [
    ("Twisted bow",                   "CoX BIS \u2014 permanently scarce; ranged PvM always relevant"),
    ("Scythe of vitur",               "ToB BIS \u2014 BiS melee for slayer/raids; supply drains via charges"),
    ("Tumeken's shadow",              "ToA BIS mage \u2014 meta-defining; no confirmed replacement"),
    ("Soulreaper axe",                "Blood Moon drop; Raids 4 hype driving melee interest"),
    ("Osmumten's fang",               "ToA \u2014 stab BIS; supply pressure from active ToA meta"),
    ("Harmonised orb",                "CoX \u2014 mage BIS for NM/PvM; CoX changes can shift supply/demand"),
    ("Volatile orb",                  "CoX \u2014 high-value unique; affected by CoX prayer scroll reweight"),
    ("Eldritch orb",                  "CoX \u2014 prayer scroll reweight; supply dynamics shifting"),
    ("Dexterous prayer scroll",       "CoX \u2014 prayer scroll reweight could shift value"),
    ("Arcane prayer scroll",          "CoX \u2014 prayer scroll rate controversy; watch for rebalance"),
    ("Enhanced crystal weapon seed",  "Corrupted Gauntlet \u2014 supply changes affect Bowfa ecosystem"),
    ("Ghrazi rapier",                 "ToB \u2014 buff/update-sensitive melee unique"),
    ("Sanguinesti staff (uncharged)", "ToB \u2014 buff/update-sensitive mage unique"),
    ("Avernic defender hilt",         "ToB \u2014 tied to ToB/raids participation"),
    ("Necklace of anguish",           "Ranged neck slot \u2014 new gear displacement risk"),
    ("Masori body (f)",               "ToA range BIS \u2014 future range gear may displace it"),
    ("Masori chaps (f)",              "ToA range BIS \u2014 same displacement risk as body"),
    ("Torva platebody",               "Nex melee BIS \u2014 raid melee hype proxy"),
    ("Torva platelegs",               "Nex melee BIS \u2014 raid melee hype proxy"),
    ("Bandos chestplate",             "Mid-tier melee \u2014 returning-player demand proxy"),
    ("Bandos tassets",                "Mid-tier melee \u2014 returning-player demand proxy"),
    ("Armadyl chestplate",            "Mid-tier range \u2014 baseline demand proxy"),
    ("Armadyl chainskirt",            "Mid-tier range \u2014 baseline demand proxy"),
    ("3rd age platebody",             "Store-of-value / status flex; fixed supply"),
]

WATCHLIST_NAMES     = [w[0] for w in WATCHLIST]
WATCHLIST_CATALYSTS = {w[0]: w[1] for w in WATCHLIST}

# ── Signals Universe ───────────────────────────────────────────────────────────
SIGNALS_UNIVERSE = {
    "Soulreaper axe":          "Game update | Active | Raids 4 rework buffed melee; axe demand spiking",
    "Zaryte crossbow":         "Meta shift | Watch | Range BIS alternative; reacts to range meta changes",
    "Dragon hunter lance":     "Boss demand | Watch | KBD/Vorkath proxy; spikes on boss hype",
    "Dragon hunter crossbow":  "Boss demand | Watch | Vorkath BiS; reacts to Vorkath/DT2 activity",
    "Ancestral robe top":      "Meta shift | Watch | Mage BIS; reacts to mage update announcements",
    "Ancestral robe bottom":   "Meta shift | Watch | Mage BIS; tied to ancestral top demand",
    "Virtus robe top":         "Game update | Watch | DT2 mage hybrid; reacts to DT2 meta",
    "Virtus robe bottom":      "Game update | Watch | DT2 mage hybrid; tied to top demand",
    "Torva full helm":         "Meta shift | Watch | Completes Torva set; melee hype proxy",
    "Justiciar faceguard":     "Meta shift | Watch | Tank/ToB; reacts to tanking meta discussions",
    "Elysian spirit shield":   "Prestige | Watch | Fixed supply store-of-value; slow mover",
    "Zaryte vambraces":        "Meta shift | Watch | Endgame range gloves; Nex activity proxy",
    "Inquisitor's mace":       "Boss demand | Watch | Crush BIS; Nightmare/ToA crush meta proxy",
    "Inquisitor's hauberk":    "Boss demand | Watch | Inquisitor set demand proxy",
    "Inquisitor's plateskirt": "Boss demand | Watch | Inquisitor set demand proxy",
}

# ── Shifts tab item pools ──────────────────────────────────────────────────────
# High-ticket items tracked in the Shifts tab (sell price >= 3M).
# These are pulled dynamically from market data by price threshold,
# but this seed list ensures key items are always included even if below threshold temporarily.
SHIFTS_HIGH_TICKET_SEEDS = [
    "Twisted bow", "Scythe of vitur", "Tumeken's shadow", "Soulreaper axe",
    "Osmumten's fang", "Harmonised orb", "Volatile orb", "Eldritch orb",
    "Enhanced crystal weapon seed", "Ghrazi rapier", "Sanguinesti staff (uncharged)",
    "Avernic defender hilt", "Torva platebody", "Torva platelegs",
    "Masori body (f)", "Masori chaps (f)", "Ancestral robe top", "Ancestral robe bottom",
    "Virtus robe top", "Virtus robe bottom", "Zaryte crossbow", "Dragon hunter lance",
    "Dragon hunter crossbow", "Necklace of anguish", "Torva full helm",
    "Justiciar faceguard", "Elysian spirit shield", "3rd age platebody",
    "Inquisitor's mace", "Zaryte vambraces",
]

# Bulk commodity items tracked in the Shifts tab.
SHIFTS_BULK_SEEDS = [
    "Prayer potion(4)", "Super restore(4)", "Saradomin brew(4)",
    "Super combat potion(4)", "Ranging potion(4)", "Magic potion(4)",
    "Antidote++(4)", "Stamina potion(4)",
    "Grimy ranarr weed", "Grimy snapdragon", "Grimy torstol",
    "Grimy toadflax", "Grimy kwuarm", "Grimy cadantine",
    "Ranarr weed", "Snapdragon", "Torstol",
    "Magic logs", "Yew logs", "Mahogany logs", "Teak logs",
    "Oak logs", "Blisterwood logs",
    "Mahogany plank", "Teak plank", "Oak plank",
    "Dragon bones", "Dagannoth bones", "Ourg bones",
    "Wyvern bones", "Superior dragon bones",
    "Coal", "Iron ore", "Mithril ore", "Adamantite ore", "Runite ore",
    "Nature rune", "Death rune", "Blood rune", "Soul rune", "Chaos rune",
    "Raw shark", "Raw monkfish", "Raw lobster",
    "Shark", "Monkfish", "Lobster",
    "Cannonball", "Steel bar", "Gold bar", "Mithril bar",
]


# ── HTTP ───────────────────────────────────────────────────────────────────────
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

def fetch_5m():
    """Return 5-minute bucket data for intraday calculations."""
    try:
        return (_get("/5m") or {}).get("data") or {}
    except Exception:
        return {}

def fetch_timeseries(item_id, timestep="24h"):
    try:
        return (_get(f"/timeseries?timestep={timestep}&id={item_id}") or {}).get("data") or []
    except Exception:
        return []


# ── Pricing helpers ────────────────────────────────────────────────────────────
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
            v = int(b); return v // 2, v // 2
        except (TypeError, ValueError):
            return 0, 0
    bh, sh = extract(hour_bucket)
    if bh > 0 or sh > 0:
        return bh, sh
    b5, s5 = extract(fmin_bucket)
    return b5 * 12, s5 * 12

def fill_quality(ratio):
    if ratio is None:           return 0.3, "No data"
    if 0.8  <= ratio <= 1.5:   return 1.0, "Ideal"
    if 1.5  < ratio  <= 3.0:   return 0.7, "High demand"
    if ratio > 3.0:             return 0.4, "Hard to buy"
    if 0.4  <= ratio <  0.8:   return 0.8, "Slight flood"
    return 0.5, "Flooded"


# ── Row builder ────────────────────────────────────────────────────────────────
def build_rows(latest, mapping, hour_vols, fmin_vols):
    mapping_by_id = {item["id"]: item for item in mapping}
    rows = []
    for id_str, quote in latest.items():
        item = mapping_by_id.get(int(id_str))
        if not item:
            continue
        buy_price  = quote.get("low")  or 0
        sell_price = quote.get("high") or 0
        ge_limit   = item.get("limit") or 0
        if not buy_price or not sell_price or not ge_limit or sell_price <= buy_price:
            continue
        item_tax    = tax(sell_price)
        profit_unit = sell_price - buy_price - item_tax
        if profit_unit <= 0:
            continue
        roi = (profit_unit / buy_price) * 100
        buy_qty_hr, sell_qty_hr = _vols(hour_vols.get(id_str), fmin_vols.get(id_str))
        total_hr = buy_qty_hr + sell_qty_hr
        ratio    = round(buy_qty_hr / sell_qty_hr, 2) if sell_qty_hr > 0 else None
        fq_mult, fq_label = fill_quality(ratio)
        potential_profit  = profit_unit * ge_limit
        adj_potential     = potential_profit * fq_mult
        fills_4hr         = sell_qty_hr * 4
        realistic_units   = min(ge_limit, max(1, fills_4hr)) if fills_4hr > 0 else ge_limit
        realistic_profit  = profit_unit * realistic_units
        rows.append({
            "id":               int(id_str),
            "name":             item["name"],
            "buy_price":        buy_price,
            "sell_price":       sell_price,
            "tax":              item_tax,
            "profit_unit":      profit_unit,
            "roi":              round(roi, 2),
            "buy_qty_hr":       buy_qty_hr,
            "sell_qty_hr":      sell_qty_hr,
            "total_hr":         total_hr,
            "ratio":            ratio,
            "fq_label":         fq_label,
            "fq_mult":          fq_mult,
            "ge_limit":         ge_limit,
            "potential_profit": potential_profit,
            "adj_potential":    adj_potential,
            "realistic_profit": realistic_profit,
            "tax_cap":          item_tax == TAX_CAP,
            "daily_volume":     total_hr * 24,
        })
    return rows


# ── Trend helpers ──────────────────────────────────────────────────────────────
def pct_change(cur, prev):
    try:
        cur, prev = float(cur), float(prev)
        if prev <= 0:
            return None
        return round(((cur - prev) / prev) * 100, 2)
    except Exception:
        return None

def classify_trend(ch1, ch7, ch30):
    ch1  = ch1  if ch1  is not None else 0
    ch7  = ch7  if ch7  is not None else 0
    ch30 = ch30 if ch30 is not None else 0
    if ch30 > 15 and ch7 > 5 and ch1 > 2:
        return "Extended"
    if ch30 > 5 and ch7 > 0 and ch1 > -1:
        return "Building"
    if ch30 > 5 and ch7 < 0 and ch1 < 0:
        return "Pullback"
    if ch30 <= 0 and ch7 < 0:
        return "Weakening"
    return "Flat"

_FLAG_LABELS = {
    "1D shock":       "Price shock (1D)",
    "7D move":        "Big move (7D)",
    "30D regime":     "Regime shift (30D)",
    "Wide spread":    "Fat margin",
    "High gp/item":   "High GP/item",
    "Liquid":         "Liquid market",
    "Flow imbalance": "Buy/sell skew",
}

def event_flags(item):
    raw = []
    ch1     = item.get("chg_1d")
    ch7     = item.get("chg_7d")
    ch30    = item.get("chg_30d")
    roi     = item.get("roi", 0) or 0
    buy_hr  = item.get("buy_qty_hr", 0) or 0
    sell_hr = item.get("sell_qty_hr", 0) or 0
    ratio   = item.get("ratio")
    profit  = item.get("profit_unit", 0) or 0

    if ch1  is not None and abs(ch1)  >= 5:  raw.append("1D shock")
    if ch7  is not None and abs(ch7)  >= 10: raw.append("7D move")
    if ch30 is not None and abs(ch30) >= 15: raw.append("30D regime")
    if roi    >= 8:                          raw.append("Wide spread")
    if profit >= 500_000:                    raw.append("High gp/item")
    if buy_hr + sell_hr >= 500:              raw.append("Liquid")
    if ratio is not None and (ratio >= 2.0 or ratio <= 0.6):
        raw.append("Flow imbalance")

    priority = 0
    if "1D shock"       in raw: priority += 3
    if "7D move"        in raw: priority += 2
    if "30D regime"     in raw: priority += 2
    if "Wide spread"    in raw: priority += 2
    if "High gp/item"   in raw: priority += 1
    if "Liquid"         in raw: priority += 1
    if "Flow imbalance" in raw: priority += 1

    readable = [_FLAG_LABELS.get(f, f) for f in raw[:4]]
    return readable, priority

def enrich_with_trends(rows):
    enriched = []
    for r in rows:
        item = dict(r)
        ts   = fetch_timeseries(r["id"], "24h")
        item["chg_1d"] = item["chg_7d"] = item["chg_30d"] = item["chg_14d"] = None
        item["trend"]  = "Flat"
        if ts and len(ts) >= 31:
            highs = [p.get("avgHighPrice") or 0 for p in ts if p.get("avgHighPrice")]
            if len(highs) >= 31:
                cur = highs[-1]
                item["chg_1d"]  = pct_change(cur, highs[-2])
                item["chg_7d"]  = pct_change(cur, highs[-8])
                item["chg_14d"] = pct_change(cur, highs[-15]) if len(highs) >= 15 else None
                item["chg_30d"] = pct_change(cur, highs[-31])
                item["trend"]   = classify_trend(item["chg_1d"], item["chg_7d"], item["chg_30d"])
        flags, priority = event_flags(item)
        item["flags"]    = " | ".join(flags) if flags else "Quiet"
        item["priority"] = priority
        enriched.append(item)
    return enriched


# ── Intraday helpers ───────────────────────────────────────────────────────────
def _avg_high(bucket):
    """Extract avgHighPrice from a 5m or 1h bucket dict."""
    if not bucket or not isinstance(bucket, dict):
        return None
    v = bucket.get("avgHighPrice")
    return float(v) if v else None

def fetch_intraday_shifts(item_ids, fmin_data_all):
    """
    For each item_id, fetch 5m timeseries and compute:
      20min, 40min, 1hr, 6hr, 12hr % shifts.
    Uses the /5m bucket for current price + timeseries for history.
    Returns dict: {item_id: {chg_20m, chg_40m, chg_1h, chg_6h, chg_12h}}
    """
    results = {}
    for item_id in item_ids:
        ts = fetch_timeseries(item_id, "5m")
        if not ts or len(ts) < 3:
            results[item_id] = {}
            continue
        highs = []
        for p in ts:
            v = p.get("avgHighPrice")
            if v:
                highs.append(float(v))
        if len(highs) < 3:
            results[item_id] = {}
            continue
        cur = highs[-1]
        # 5m buckets: 4 = 20min, 8 = 40min, 12 = 1hr, 72 = 6hr, 144 = 12hr
        def _chg(n):
            idx = -1 - n
            if abs(idx) > len(highs):
                return None
            prev = highs[idx]
            return pct_change(cur, prev)
        results[item_id] = {
            "chg_20m":  _chg(4),
            "chg_40m":  _chg(8),
            "chg_1h":   _chg(12),
            "chg_6h":   _chg(72),
            "chg_12h":  _chg(144),
        }
    return results


# ── Viability filter ───────────────────────────────────────────────────────────
def is_viable_bulk(r):
    buy_hr    = r.get("buy_qty_hr", 0)  or 0
    sell_hr   = r.get("sell_qty_hr", 0) or 0
    ratio     = r.get("ratio")
    ge        = r.get("ge_limit", 0)    or 0
    profit    = r.get("profit_unit", 0) or 0
    realistic = r.get("realistic_profit", 0) or 0
    buy_price = r.get("buy_price", 0)   or 0
    if buy_hr < 100 or sell_hr < 50:                           return False
    if ratio is None or ratio < 0.5 or ratio > 3.0:            return False
    if min(ge, sell_hr * 4) < max(100, ge * 0.05):             return False
    if profit < 100 or realistic < 100_000 or buy_price < 500: return False
    return True


# ── Shifts tab data builder ────────────────────────────────────────────────────
def build_shifts_data(all_rows, mapping):
    """
    Build high-ticket and bulk item lists for the Shifts tab.
    Returns (high_ticket_rows, bulk_rows) — each pre-enriched with
    daily trends (chg_1d/7d/14d/30d) AND intraday shifts (chg_20m/40m/1h/6h/12h).
    """
    name_map = {r["name"].lower(): r for r in all_rows}

    ht_seed_lower  = {n.lower() for n in SHIFTS_HIGH_TICKET_SEEDS}
    bulk_seed_lower = {n.lower() for n in SHIFTS_BULK_SEEDS}

    # High ticket: seeds + any item in market data with sell_price >= 3M
    ht_rows = []
    seen_ht = set()
    for r in all_rows:
        nl = r["name"].lower()
        if nl in ht_seed_lower or r.get("sell_price", 0) >= 3_000_000:
            if nl not in seen_ht:
                ht_rows.append(r)
                seen_ht.add(nl)

    # Bulk: seeds that exist in market data
    bulk_rows = []
    seen_bulk = set()
    for name in SHIFTS_BULK_SEEDS:
        nl = name.lower()
        if nl in name_map and nl not in seen_bulk:
            bulk_rows.append(name_map[nl])
            seen_bulk.add(nl)

    # Enrich both with daily trends (fetches 24h timeseries per item)
    ht_enriched   = enrich_with_trends(ht_rows)
    bulk_enriched = enrich_with_trends(bulk_rows)

    # Enrich with intraday data (fetches 5m timeseries per item)
    all_enriched = ht_enriched + bulk_enriched
    item_ids     = [r["id"] for r in all_enriched]
    intraday_map = fetch_intraday_shifts(item_ids, {})

    for r in all_enriched:
        intra = intraday_map.get(r["id"], {})
        r["chg_20m"] = intra.get("chg_20m")
        r["chg_40m"] = intra.get("chg_40m")
        r["chg_1h"]  = intra.get("chg_1h")
        r["chg_6h"]  = intra.get("chg_6h")
        r["chg_12h"] = intra.get("chg_12h")

    ht_enriched   = [r for r in all_enriched if r["id"] in {x["id"] for x in ht_enriched}]
    bulk_enriched = [r for r in all_enriched if r["id"] in {x["id"] for x in bulk_enriched}]

    return ht_enriched, bulk_enriched


# ── Main compute ───────────────────────────────────────────────────────────────
_TREND_ORDER = {"Extended": 0, "Building": 1, "Pullback": 2, "Weakening": 3, "Flat": 4}

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

    watch_raw = [all_by_name[n.lower()] for n in WATCHLIST_NAMES if n.lower() in all_by_name]
    watch     = enrich_with_trends(watch_raw)
    watch     = sorted(watch, key=lambda r: (
        _TREND_ORDER.get(r.get("trend", "Flat"), 5),
        -abs(r.get("chg_7d") or 0),
        -r.get("profit_unit", 0),
    ))

    signals_raw = [all_by_name[n.lower()] for n in SIGNALS_UNIVERSE if n.lower() in all_by_name]
    signals     = enrich_with_trends(signals_raw)
    for s in signals:
        s["signal_context"] = SIGNALS_UNIVERSE.get(s["name"], "")
    signals = sorted(signals, key=lambda r: (
        _TREND_ORDER.get(r.get("trend", "Flat"), 5),
        -abs(r.get("chg_7d") or 0),
        -r.get("profit_unit", 0),
    ))

    return bulk, singular, high_roi, watch, signals, rows