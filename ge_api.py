import requests

BASE     = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS  = {"User-Agent": "OsrsFlipDashboard/Owen"}
TAX_RATE = 0.02
TAX_CAP  = 5_000_000

# ── Watchlist — always-on anchors + update-driven catalyst items ──────────────
# Catalyst column explains WHY each item is on the watchlist.
WATCHLIST = [
    # (item name,                       catalyst note)
    ("Twisted bow",           "CoX BIS — permanently scarce; ranged PvM always relevant"),
    ("Scythe of vitur",       "ToB BIS — BiS melee for slayer/raids; supply drains via charges"),
    ("Tumeken's shadow",      "ToA BIS mage — meta-defining; no confirmed replacement"),
    ("Soulreaper axe",        "Blood Moon drop; Raids 4 hype driving melee interest"),
    ("Osmumten's fang",       "ToA — stab BIS; supply pressure from active ToA meta"),
    ("Harmonised orb",        "CoX — mage BIS for NM/PvM; Summer Sweep-Up CoX changes = supply shift"),
    ("Volatile orb",          "CoX — high-value unique; affected by CoX prayer scroll reweight (Summer 2026)"),
    ("Eldritch orb",          "CoX — affected by CoX prayer scroll reweight; supply dynamics shifting"),
    ("Dexterous prayer scroll","CoX — prayer scroll reweight in Summer 2026 could push Dex up if arcane/dex rate cut"),
    ("Arcane prayer scroll",  "CoX — Summer 2026 CM Cox reweight: 58% drop rate controversy; watch for rate change"),
    ("Enhanced crystal weapon seed","Corrupted Gauntlet — Summer Sweep-Up stackable resources buff = faster CG = more supply"),
    ("Ghrazi rapier",         "ToB — Sang/Rapier buffed in Summer Sweep-Up 2026; +17.98% in May 2026"),
    ("Sanguinesti staff (uncharged)","ToB — buffed in Summer Sweep-Up; +6% in May; rising interest"),
    ("Avernic defender hilt", "ToB — always tied to ToB meta; Raids 4 player resurgence likely"),
    ("Necklace of anguish",   "Ranged BiS neck — Necklace of Pursuit (Blood Moon, Jun 30 2026) replaces it; SELL signal"),
    ("Masori body (f)",       "ToA range BiS — Raids 4 new range gear may displace; watch for replacement"),
    ("Masori chaps (f)",      "ToA range BiS — same Raids 4 range gear displacement risk as body"),
    ("Torva platebody",       "Nex melee BIS — Raids 4 may introduce melee upgrade; pre-raid hold"),
    ("Torva platelegs",       "Nex melee BIS — same Raids 4 melee thesis as platebody"),
    ("Bandos chestplate",     "Mid-tier melee — Raids 4 new players returning will gear up through Bandos tier"),
    ("Bandos tassets",        "Mid-tier melee — same returning player thesis as chestplate"),
    ("Armadyl chestplate",    "Mid-tier range — new players gearing for ToA/CoX; demand baseline"),
    ("Armadyl chainskirt",    "Mid-tier range — same thesis as chestplate"),
    ("3rd age platebody",     "Store-of-value / status flex; fixed supply, grows with playerbase wealth"),
]

WATCHLIST_NAMES     = [w[0] for w in WATCHLIST]
WATCHLIST_CATALYSTS = {w[0]: w[1] for w in WATCHLIST}


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
    if 0.8 <= ratio <= 1.5:   return 1.0, "Ideal"
    elif 1.5 < ratio <= 3.0:  return 0.7, "High demand"
    elif ratio > 3.0:          return 0.4, "Hard to buy"
    elif 0.4 <= ratio < 0.8:  return 0.8, "Slight flood"
    else:                      return 0.5, "Flooded"

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
        total_hr    = buy_qty_hr + sell_qty_hr
        ratio       = round(buy_qty_hr / sell_qty_hr, 2) if sell_qty_hr > 0 else None
        fq_mult, fq_label = fill_quality(ratio)
        potential_profit = profit_unit * ge_limit
        adj_potential    = potential_profit * fq_mult
        fills_4hr        = sell_qty_hr * 4
        realistic_units  = min(ge_limit, max(1, fills_4hr)) if fills_4hr > 0 else ge_limit
        realistic_profit = profit_unit * realistic_units
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



def pct_change(cur, prev):
    try:
        cur = float(cur); prev = float(prev)
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

def enrich_watchlist_with_trends(watch_rows):
    enriched = []
    for r in watch_rows:
        item = dict(r)
        ts = fetch_timeseries(r["id"], "24h")
        if ts and len(ts) >= 31:
            highs = [p.get("avgHighPrice") or 0 for p in ts if p.get("avgHighPrice")]
            if len(highs) >= 31:
                cur = highs[-1]
                d1 = highs[-2]
                d7 = highs[-8]
                d30 = highs[-31]
                item["chg_1d"] = pct_change(cur, d1)
                item["chg_7d"] = pct_change(cur, d7)
                item["chg_30d"] = pct_change(cur, d30)
                item["trend"] = classify_trend(item["chg_1d"], item["chg_7d"], item["chg_30d"])
            else:
                item["chg_1d"] = item["chg_7d"] = item["chg_30d"] = None
                item["trend"] = "Flat"
        else:
            item["chg_1d"] = item["chg_7d"] = item["chg_30d"] = None
            item["trend"] = "Flat"
        enriched.append(item)
    return enriched

def is_viable_bulk(r):
    buy_hr    = r.get("buy_qty_hr", 0) or 0
    sell_hr   = r.get("sell_qty_hr", 0) or 0
    ratio     = r.get("ratio")
    ge        = r.get("ge_limit", 0) or 0
    profit    = r.get("profit_unit", 0) or 0
    realistic = r.get("realistic_profit", 0) or 0
    buy_price = r.get("buy_price", 0) or 0

    # Needs actual two-sided market activity.
    if buy_hr < 100 or sell_hr < 50:
        return False

    # Ratio can't be absurdly one-sided if we want a realistic bulk flip.
    if ratio is None or ratio < 0.5 or ratio > 3.0:
        return False

    # Must be able to move at least a meaningful chunk of the GE limit in 4 hours.
    if min(ge, sell_hr * 4) < max(100, ge * 0.05):
        return False

    # Avoid ultra-thin or trivial-value items even if percentage ROI looks huge.
    if profit < 100:
        return False
    if realistic < 100_000:
        return False
    if buy_price < 500:
        return False

    return True

def compute_flips(latest, mapping, hour_vols, fmin_vols):
    rows = build_rows(latest, mapping, hour_vols, fmin_vols)
    bulk = sorted(
        [r for r in rows if r["ge_limit"] >= 1000 and r["total_hr"] >= 200 and is_viable_bulk(r)],
        key=lambda x: (-x["profit_unit"], -x["fq_mult"], -x["ge_limit"], -x["roi"])
    )[:60]
    singular = sorted(
        [r for r in rows if r["ge_limit"] <= 15 and r["sell_price"] >= 500_000 and r["total_hr"] >= 1],
        key=lambda x: -(x["profit_unit"] * x["fq_mult"])
    )[:40]
    high_roi = sorted(
        [r for r in rows if r["total_hr"] >= 50 and r["roi"] >= 5],
        key=lambda x: -x["roi"]
    )[:40]
    all_by_name = {r["name"].lower(): r for r in rows}
    watch = [all_by_name[n.lower()] for n in WATCHLIST_NAMES if n.lower() in all_by_name]
    watch = enrich_watchlist_with_trends(watch)
    return bulk, singular, high_roi, watch, rows