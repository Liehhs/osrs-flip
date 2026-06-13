import requests

BASE    = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {"User-Agent": "OsrsFlipDashboard/Owen"}
TAX_RATE = 0.02
TAX_CAP  = 5_000_000

# Watchlist -- comprehensive 5M+ bossing/raids drops and endgame gear
WATCHLIST = [
    # -- Chambers of Xeric --
    ("Twisted bow",                   "CoX",         "Ranged BIS -- rarest CoX unique; permanently scarce supply"),
    ("Kodai wand",                    "CoX",         "Mage BIS autocast -- steady demand from mage PvMers"),
    ("Elder maul",                    "CoX",         "Crush BIS -- ToA drives additional demand"),
    ("Ancestral robe top",            "CoX",         "Mage BIS armour -- reactive to mage update announcements"),
    ("Ancestral robe bottom",         "CoX",         "Mage BIS armour -- tied to top demand"),
    ("Ancestral hat",                 "CoX",         "Mage BIS helm -- completes ancestral set"),
    ("Dragon claws",                  "CoX",         "Spec weapon -- high PvP + PvM demand; volatile"),
    ("Dexterous prayer scroll",       "CoX",         "Rigour unlock -- Raids 4 prep driving CoX participation"),
    ("Arcane prayer scroll",          "CoX",         "Augury unlock -- tied to Rigour demand"),
    ("Harmonised orb",                "CoX",         "Mage BIS for NM/PvM -- CoX changes shift supply"),
    ("Volatile orb",                  "CoX",         "High-value spec weapon orb -- spec meta proxy"),
    ("Eldritch orb",                  "CoX",         "Prayer restore spec orb -- niche but stable demand"),
    # -- Theatre of Blood --
    ("Scythe of vitur",               "ToB",         "Melee BIS for slayer/raids -- Raids 4 prep demand active"),
    ("Ghrazi rapier",                 "ToB",         "Stab BIS -- Summer Sweep-Up +4 str buff live now"),
    ("Sanguinesti staff (uncharged)", "ToB",         "Mage BIS -- Summer Sweep-Up 6% DPS buff + cheaper charges"),
    ("Avernic defender hilt",         "ToB",         "Defender upgrade -- tied to ToB/raids participation"),
    ("Justiciar faceguard",           "ToB",         "Tank helm -- set bonus removed in Sweep-Up; demand softening"),
    ("Justiciar chestguard",          "ToB",         "Tank body -- set bonus removal reduces full-set value"),
    ("Justiciar legguards",           "ToB",         "Tank legs -- same set bonus removal impact"),
    # -- Tombs of Amascut --
    ("Tumeken's shadow",              "ToA",         "Mage BIS -- Raids 4 prep meta; confirmed must-have"),
    ("Osmumten's fang",               "ToA",         "Stab BIS -- consistently high ToA activity proxy"),
    ("Elidinis' ward (f)",            "ToA",         "Mage offhand BIS -- completes ToA mage setup"),
    ("Masori body (f)",               "ToA",         "Range BIS armour -- Necklace of Rupture buffs range setups June 30"),
    ("Masori chaps (f)",              "ToA",         "Range BIS legs -- displacement risk from Blood Moon Rises"),
    ("Masori mask (f)",               "ToA",         "Range BIS helm -- completes Masori set"),
    # -- Nex --
    ("Torva platebody",               "Nex",         "Melee BIS body -- Soulreaper axe buff increases melee activity"),
    ("Torva platelegs",               "Nex",         "Melee BIS legs -- melee hype proxy"),
    ("Torva full helm",               "Nex",         "Completes Torva set -- melee demand proxy"),
    ("Zaryte crossbow",               "Nex",         "Range BIS alt -- Necklace of Rupture (June 30) buffs range setups"),
    ("Zaryte vambraces",              "Nex",         "Endgame range gloves BIS -- Nex activity proxy"),
    # -- Nightmare / Phosani --
    ("Inquisitor's mace",             "Nightmare",   "Crush BIS spec -- Sweep-Up standalone buffed; set bonus removed"),
    ("Inquisitor's hauberk",          "Nightmare",   "Set bonus removed -- weaker with mace post-Sweep-Up; price risk"),
    ("Inquisitor's plateskirt",       "Nightmare",   "Same as hauberk -- set synergy gone post-Sweep-Up"),
    ("Nightmare staff",               "Nightmare",   "Mage staff -- base for Harmonised/Volatile/Eldritch orbs"),
    # -- Desert Treasure 2 --
    ("Soulreaper axe",                "DT2",         "Melee BIS -- Summer Sweep-Up major rework; biggest buff in years"),
    ("Virtus robe top",               "DT2",         "DT2 mage hybrid -- scepter DPS buffs boost mage ecosystem"),
    ("Virtus robe bottom",            "DT2",         "DT2 mage hybrid -- tied to Virtus top demand"),
    ("Bellator ring",                 "DT2",         "Melee ring -- Soulreaper buff raises melee demand proxy"),
    ("Venator ring",                  "DT2",         "Range ring -- bow consistency fix in Sweep-Up aids range meta"),
    ("Magus ring",                    "DT2",         "Mage ring -- tied to Shadow + ancestral scepter buff ecosystem"),
    ("Ultor ring",                    "DT2",         "Strength ring -- melee proxy; Soulreaper hype driver"),
    # -- God Wars Dungeon --
    ("Bandos chestplate",             "GWD",         "Melee BIS body at mid-tier -- returning-player demand proxy"),
    ("Bandos tassets",                "GWD",         "Melee BIS legs -- pairs with chestplate demand"),
    ("Armadyl chestplate",            "GWD",         "Range mid-tier body -- solid baseline demand"),
    ("Armadyl chainskirt",            "GWD",         "Range mid-tier legs -- pairs with chestplate"),
    ("Armadyl helmet",                "GWD",         "Range mid-tier helm -- completes Armadyl set"),
    # -- Zulrah --
    ("Tanzanite fang",                "Zulrah",      "Toxic blowpipe component -- universal early-mid BIS range weapon"),
    ("Magic fang",                    "Zulrah",      "Toxic staff upgrade -- budget mage weapon option"),
    ("Serpentine visage",             "Zulrah",      "Serpentine helm component -- slayer/venom utility"),
    ("Zulrah's scales",               "Zulrah",      "Blowpipe/serp helm charge resource -- consumable; constant demand"),
    # -- Cerberus --
    ("Primordial crystal",            "Cerberus",    "Primordial boots component -- BIS melee boots; 1/512 drop rate"),
    ("Eternal crystal",               "Cerberus",    "Eternal boots component -- BIS mage boots; 1/512 drop rate"),
    ("Pegasian crystal",              "Cerberus",    "Pegasian boots component -- BIS range boots; 1/512 drop rate"),
    # -- Dagannoth Kings --
    ("Berserker ring (i)",            "Dagannoth",   "Melee ring upgrade -- imbued; NMZ/slayer demand proxy"),
    ("Archers ring (i)",              "Dagannoth",   "Range ring -- imbued; steady mid-tier demand"),
    ("Seers ring (i)",                "Dagannoth",   "Mage ring -- imbued; mid-tier mage demand proxy"),
    ("Dragon axe",                    "Dagannoth",   "BIS woodcutting axe -- consistent skilling upgrade demand"),
    # -- Moons of Peril / Varlamore --
    ("Eclipse atlatl",                "Varlamore",   "New range weapon -- PvP nerfed in Sweep-Up; PvM use stable"),
    ("Blood moon helm",               "Varlamore",   "Mid-tier melee helm -- Varlamore activity proxy"),
    ("Blood moon chestplate",         "Varlamore",   "Mid-tier melee body -- tied to helm demand"),
    ("Blood moon tassets",            "Varlamore",   "Mid-tier melee legs -- completes Blood Moon set"),
    # -- Raids 4 / Fractured Archive prep --
    ("Enhanced crystal weapon seed",  "Raids/FA",    "Corrupted Gauntlet -- Sweep-Up may increase CG supply"),
    ("Crystal armour seed",           "Raids/FA",    "CG armour seed -- Raids 4 prep increases CG participation"),
    # -- Specialist Weapons --
    ("Dragon hunter lance",           "Specialist",  "Vorkath/KBD BIS -- no rework in current roadmap; stable"),
    ("Dragon hunter crossbow",        "Specialist",  "Vorkath range BIS -- pairs with lance demand patterns"),
    ("Abyssal whip",                  "Specialist",  "Slayer staple melee -- permanent demand floor"),
    ("Abyssal dagger",                "Specialist",  "Spec dagger -- whip complement; stable slayer demand"),
    # -- Accessories --
    ("Necklace of anguish",           "Accessories", "Range BIS neck -- BEING REPLACED June 30 by Necklace of Rupture"),
    ("Tormented bracelet",            "Accessories", "Mage BIS bracelet -- Blood Moon Rises may add hybrid competitor"),
    ("Amulet of torture",             "Accessories", "Melee BIS neck -- Soulreaper buff increases melee demand"),
    ("Elysian spirit shield",         "Accessories", "Prestige tank shield -- fixed supply store-of-value"),
    ("Arcane spirit shield",          "Accessories", "Mage spirit shield -- steady collector demand"),
    ("Spectral spirit shield",        "Accessories", "Prayer/mage def shield -- niche but tracked"),
    # -- High-Ticket Clue Items --
    ("3rd age platebody",             "Prestige",    "Ultra-rare hard/elite clue -- store-of-value; ~1/42K rate"),
    ("3rd age platelegs",             "Prestige",    "Ultra-rare hard clue -- pairs with platebody"),
    ("3rd age full helmet",           "Prestige",    "Ultra-rare hard clue -- completes 3rd age melee set"),
    ("3rd age longsword",             "Prestige",    "Rare hard clue reward -- speculative; low supply"),
    ("3rd age bow",                   "Prestige",    "Ultra-rare elite/master clue -- range prestige item"),
    ("3rd age wand",                  "Prestige",    "Ultra-rare elite clue -- mage prestige item"),
    ("3rd age cloak",                 "Prestige",    "Rare master clue -- complement to 3rd age sets"),
    ("Ranger boots",                  "Prestige",    "Medium clue BIS range boots -- high demand relative to rate"),
    ("Robin hood hat",                "Prestige",    "Hard clue range helm -- consistently desired cosmetic"),
    ("Gilded scimitar",               "Prestige",    "Hard/elite gilded -- cosmetic floor item; collector appeal"),
    ("Gilded platebody",              "Prestige",    "Elite/master gilded armour -- prestige flex item"),
    ("Gilded platelegs",              "Prestige",    "Elite/master gilded -- pairs with platebody"),
    ("Gilded full helm",              "Prestige",    "Elite/master gilded -- completes gilded melee set"),
]

WATCHLIST_NAMES     = [w[0] for w in WATCHLIST]
WATCHLIST_CATALYSTS = {w[0]: w[2] for w in WATCHLIST}
WATCHLIST_CATEGORY  = {w[0]: w[1] for w in WATCHLIST}

# Signals Universe -- TYPE | STATUS | REASON
SIGNALS_UNIVERSE = {
    # ---- ACTIVE: Blood Moon Rises (June 30, 2026) ----
    "Necklace of anguish":          "New Content | ACTIVE | Necklace of Rupture (new BIS range neck) drops June 30 -- direct displacement; sell into hype before release",
    "Soulreaper axe":               "Game Update | ACTIVE | Summer Sweep-Up live: major rework -- +4 str, stacks to 5, 50% acc buff, 12.5% def drain, min 30% spec hit. Clear price catalyst",
    "Sanguinesti staff (uncharged)":"Game Update | ACTIVE | Summer Sweep-Up: 6% DPS buff, heal 1-in-5 (up from 1-in-6), charge cost 3->2 blood runes. Demand spike likely",
    "Ghrazi rapier":                "Game Update | ACTIVE | Summer Sweep-Up: +4 str bonus guarantees extra max hit in all setups. ~2-2.5% DPS buff. Watch for price reaction",
    "Inquisitor's mace":            "Game Update | ACTIVE | Summer Sweep-Up: set bonus REMOVED -- mace standalone buffed (+5 str, +7 crush acc) but net weaker with full Inq set. Inq armour demand likely falls",
    "Inquisitor's hauberk":         "Game Update | ACTIVE | Inquisitor set bonus removed -- pieces no longer synergise with mace. Demand for full set drops; individual pieces may slide",
    "Inquisitor's plateskirt":      "Game Update | ACTIVE | Same as hauberk -- set bonus removal reduces value of wearing with mace. Watch for price decline",
    # ---- ACTIVE: Raids 4 prep demand ----
    "Twisted bow":                  "New Content | ACTIVE | Raids 4 (Autumn 2026) confirmed -- Tbow listed as mandatory prep gear by community. Sustained accumulation phase underway",
    "Tumeken's shadow":             "New Content | ACTIVE | Raids 4 prep -- Shadow confirmed BIS mage for new raid. Community guides recommending it as must-have before release",
    "Scythe of vitur":              "New Content | ACTIVE | Raids 4 prep -- Scythe listed as closest reference weapon for new raid mechanics. Demand building toward Autumn release",
    # ---- WATCH: Blood Moon Rises supply/displacement plays ----
    "Tormented bracelet":           "New Content | WATCH | Blood Moon Rises (June 30) adds Leech Fin -- new melee/hybrid BiS bracelet. Tormented bracelet may see displacement pressure",
    "Osmumten's fang":              "New Content | WATCH | Crimson Bludgeon (new crush BIS spec) drops June 30 -- fang ecosystem unaffected but watch for market-wide high-ticket volatility around release",
    "Zaryte crossbow":              "New Content | WATCH | Necklace of Rupture (new BIS range neck) releases June 30 -- upgrades ranged setups; crossbow demand proxy for range meta activity",
    # ---- WATCH: Summer Sweep-Up ongoing reactions ----
    "Ancestral robe top":           "Game Update | WATCH | Ancient scepters buffed to 10% magic damage (up from 5%) -- indirect mage DPS ecosystem buff; ancestral demand stable or mild uptick",
    "Ancestral robe bottom":        "Game Update | WATCH | Tied to ancestral top -- same indirect mage DPS buff from scepter changes",
    "Virtus robe top":              "Game Update | WATCH | Scepter buffs boost hybrid mage DPS setups -- Virtus benefits from wider mage DPS improvements",
    "Virtus robe bottom":           "Game Update | WATCH | Tied to Virtus top demand",
    "Venator ring":                 "Game Update | WATCH | Summer Sweep-Up: Venator bow made more consistent via new targeting -- ring demand proxy for range meta; watch for uptick",
    "Enhanced crystal weapon seed": "New Content | WATCH | GE added to Corrupted Gauntlet in Sweep-Up blog -- easier CG access may increase Bowfa supply; seed price could soften",
    "Dragon claws":                 "PvP Meta | WATCH | Summer Sweep-Up Eclipse atlatl nerfed 1-tick slower in PvP without full set -- claw spec value in PvP stays high by comparison",
    "Elysian spirit shield":        "Supply Shock | WATCH | Fixed supply store-of-value; Blood Moon Rises hype driving general high-ticket market activity -- floor remains strong",
    # ---- WATCH: Raids 4 ecosystem ----
    "Avernic defender hilt":        "New Content | WATCH | Raids 4 Autumn 2026 -- ToB participation expected to rise as players gear up; Avernic demand proxy for ToB activity",
    "Dexterous prayer scroll":      "New Content | WATCH | CoX participation rising as players prep for Raids 4 -- Rigour scroll demand proxy for CoX activity levels",
    "Arcane prayer scroll":         "New Content | WATCH | Same as Dexterous -- Augury demand proxy for CoX/prep activity",
    "Bellator ring":                "New Content | WATCH | Raids 4 Autumn -- DT2 rings being accumulated as part of endgame gear prep; melee ring proxy",
    "Ultor ring":                   "New Content | WATCH | Same as Bellator -- strength ring proxy for melee prep meta",
    "Magus ring":                   "New Content | WATCH | Mage ring proxy -- benefits from both shadow demand and ancestral/scepter DPS buff discussions",
    # ---- COOLING ----
    "Zaryte vambraces":             "Meta Shift | COOLING | No specific catalyst this cycle; Nex activity stable but no new hype driver. Monitor for Raids 4 range demand proxy",
    "Justiciar faceguard":          "Meta Shift | COOLING | No tank meta catalyst active; Inq set bonus removal may marginally shift attention away from full armour sets",
    "Dragon hunter lance":          "Boss Demand | COOLING | No Vorkath/KBD rework announced; stable demand but no near-term spike catalyst",
    "Dragon hunter crossbow":       "Boss Demand | COOLING | Same as lance -- no Vorkath rework in current roadmap. Hold steady",
}

SHIFTS_HIGH_TICKET_SEEDS = [
    "Twisted bow","Scythe of vitur","Tumeken's shadow","Soulreaper axe",
    "Osmumten's fang","Harmonised orb","Volatile orb","Eldritch orb",
    "Enhanced crystal weapon seed","Ghrazi rapier","Sanguinesti staff (uncharged)",
    "Avernic defender hilt","Torva platebody","Torva platelegs",
    "Masori body (f)","Masori chaps (f)","Ancestral robe top","Ancestral robe bottom",
    "Virtus robe top","Virtus robe bottom","Zaryte crossbow","Dragon hunter lance",
    "Dragon hunter crossbow","Necklace of anguish","Torva full helm",
    "Justiciar faceguard","Elysian spirit shield","3rd age platebody",
    "Inquisitor's mace","Zaryte vambraces","Kodai wand","Elder maul",
    "Dragon claws","Dexterous prayer scroll","Arcane prayer scroll",
    "Ancestral hat","Justiciar chestguard","Justiciar legguards",
    "Elidinis' ward (f)","Masori mask (f)",
    "Inquisitor's hauberk","Inquisitor's plateskirt","Nightmare staff",
    "Bellator ring","Venator ring","Magus ring","Ultor ring",
    "Armadyl chestplate","Armadyl chainskirt","Armadyl helmet",
    "Bandos chestplate","Bandos tassets",
    "Tormented bracelet","Arcane spirit shield",
]

SHIFTS_BULK_SEEDS = [
    "Prayer potion(4)","Super restore(4)","Saradomin brew(4)",
    "Super combat potion(4)","Ranging potion(4)","Magic potion(4)",
    "Antidote++(4)","Stamina potion(4)",
    "Grimy ranarr weed","Grimy snapdragon","Grimy torstol",
    "Grimy toadflax","Grimy kwuarm","Grimy cadantine",
    "Ranarr weed","Snapdragon","Torstol",
    "Magic logs","Yew logs","Mahogany logs","Teak logs",
    "Oak logs","Blisterwood logs",
    "Mahogany plank","Teak plank","Oak plank",
    "Dragon bones","Dagannoth bones","Ourg bones",
    "Wyvern bones","Superior dragon bones",
    "Coal","Iron ore","Mithril ore","Adamantite ore","Runite ore",
    "Nature rune","Death rune","Blood rune","Soul rune","Chaos rune",
    "Raw shark","Raw monkfish","Raw lobster",
    "Shark","Monkfish","Lobster",
    "Cannonball","Steel bar","Gold bar","Mithril bar",
]

# -- HTTP -----------------------------------------------------------------------
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
    try:
        return (_get("/5m") or {}).get("data") or {}
    except Exception:
        return {}

def fetch_timeseries(item_id, timestep="24h"):
    try:
        return (_get(f"/timeseries?timestep={timestep}&id={item_id}") or {}).get("data") or []
    except Exception:
        return []

# -- Pricing helpers ------------------------------------------------------------
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
    if ratio is None:        return 0.3, "No data"
    if 0.8 <= ratio <= 1.5:  return 1.0, "Ideal"
    if 1.5 < ratio <= 3.0:   return 0.7, "High demand"
    if ratio > 3.0:           return 0.4, "Hard to buy"
    if 0.4 <= ratio < 0.8:   return 0.8, "Slight flood"
    return 0.5, "Flooded"

# -- Row builder ----------------------------------------------------------------
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

# -- Trend helpers --------------------------------------------------------------
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
    if ch30 > 15 and ch7 > 5  and ch1 > 2:  return "Extended"
    if ch30 > 5  and ch7 > 0  and ch1 > -1: return "Building"
    if ch30 > 5  and ch7 < 0  and ch1 < 0:  return "Pullback"
    if ch30 <= 0 and ch7 < 0:               return "Weakening"
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
    raw     = []
    ch1     = item.get("chg_1d")
    ch7     = item.get("chg_7d")
    ch30    = item.get("chg_30d")
    roi     = item.get("roi",         0) or 0
    buy_hr  = item.get("buy_qty_hr",  0) or 0
    sell_hr = item.get("sell_qty_hr", 0) or 0
    ratio   = item.get("ratio")
    profit  = item.get("profit_unit", 0) or 0

    if ch1  is not None and abs(ch1)  >= 5:  raw.append("1D shock")
    if ch7  is not None and abs(ch7)  >= 10: raw.append("7D move")
    if ch30 is not None and abs(ch30) >= 15: raw.append("30D regime")
    if roi    >= 8:                           raw.append("Wide spread")
    if profit >= 500_000:                     raw.append("High gp/item")
    if buy_hr + sell_hr >= 500:               raw.append("Liquid")
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
        for k in ("chg_1d","chg_7d","chg_30d","chg_14d",
                  "prev_price_1d","prev_price_7d","prev_price_14d","prev_price_30d"):
            item[k] = None
        item["trend"] = "Flat"
        if ts and len(ts) >= 31:
            highs = [p.get("avgHighPrice") or 0 for p in ts if p.get("avgHighPrice")]
            if len(highs) >= 31:
                cur = highs[-1]
                item["chg_1d"]  = pct_change(cur, highs[-2])
                item["chg_7d"]  = pct_change(cur, highs[-8])
                item["chg_14d"] = pct_change(cur, highs[-15]) if len(highs) >= 15 else None
                item["chg_30d"] = pct_change(cur, highs[-31])
                item["prev_price_1d"]  = int(highs[-2])
                item["prev_price_7d"]  = int(highs[-8])
                item["prev_price_14d"] = int(highs[-15]) if len(highs) >= 15 else None
                item["prev_price_30d"] = int(highs[-31])
                item["trend"] = classify_trend(item["chg_1d"], item["chg_7d"], item["chg_30d"])
        flags, priority = event_flags(item)
        item["flags"]    = " | ".join(flags) if flags else "Quiet"
        item["priority"] = priority
        enriched.append(item)
    return enriched

# -- Intraday helpers -----------------------------------------------------------
def fetch_intraday_shifts(item_ids, fmin_data_all):
    results = {}
    for item_id in item_ids:
        ts = fetch_timeseries(item_id, "5m")
        if not ts or len(ts) < 3:
            results[item_id] = {}
            continue
        highs = [float(p["avgHighPrice"]) for p in ts if p.get("avgHighPrice")]
        if len(highs) < 3:
            results[item_id] = {}
            continue
        cur = highs[-1]
        def _chg(n):
            idx = -1 - n
            if abs(idx) > len(highs): return None
            return pct_change(cur, highs[idx])
        def _prev(n):
            idx = -1 - n
            if abs(idx) > len(highs): return None
            return int(highs[idx])
        results[item_id] = {
            "chg_20m":        _chg(4),
            "chg_40m":        _chg(8),
            "chg_1h":         _chg(12),
            "chg_6h":         _chg(72),
            "chg_12h":        _chg(144),
            "prev_price_20m": _prev(4),
            "prev_price_40m": _prev(8),
            "prev_price_1h":  _prev(12),
            "prev_price_6h":  _prev(72),
            "prev_price_12h": _prev(144),
        }
    return results

# -- Viability filter -----------------------------------------------------------
def is_viable_bulk(r):
    buy_hr    = r.get("buy_qty_hr",     0) or 0
    sell_hr   = r.get("sell_qty_hr",    0) or 0
    ratio     = r.get("ratio")
    ge        = r.get("ge_limit",       0) or 0
    profit    = r.get("profit_unit",    0) or 0
    realistic = r.get("realistic_profit", 0) or 0
    buy_price = r.get("buy_price",      0) or 0
    if buy_hr < 100 or sell_hr < 50:                          return False
    if ratio is None or ratio < 0.5 or ratio > 3.0:           return False
    if min(ge, sell_hr * 4) < max(100, ge * 0.05):            return False
    if profit < 100 or realistic < 100_000 or buy_price < 500: return False
    return True

# -- Shifts data builder --------------------------------------------------------
def build_shifts_data(all_rows, mapping):
    name_map      = {r["name"].lower(): r for r in all_rows}
    ht_seed_lower = {n.lower() for n in SHIFTS_HIGH_TICKET_SEEDS}

    ht_rows = []
    seen_ht = set()
    for r in all_rows:
        nl = r["name"].lower()
        if nl in ht_seed_lower or r.get("sell_price", 0) >= 3_000_000:
            if nl not in seen_ht:
                ht_rows.append(r)
                seen_ht.add(nl)

    bulk_rows = []
    seen_bulk = set()
    for name in SHIFTS_BULK_SEEDS:
        nl = name.lower()
        if nl in name_map and nl not in seen_bulk:
            bulk_rows.append(name_map[nl])
            seen_bulk.add(nl)

    ht_enriched   = enrich_with_trends(ht_rows)
    bulk_enriched = enrich_with_trends(bulk_rows)

    all_enriched = ht_enriched + bulk_enriched
    item_ids     = [r["id"] for r in all_enriched]
    intraday_map = fetch_intraday_shifts(item_ids, {})

    for r in all_enriched:
        intra = intraday_map.get(r["id"], {})
        for k in ("chg_20m","chg_40m","chg_1h","chg_6h","chg_12h",
                  "prev_price_20m","prev_price_40m","prev_price_1h",
                  "prev_price_6h","prev_price_12h"):
            r[k] = intra.get(k)

    ht_ids   = {x["id"] for x in ht_enriched}
    bulk_ids = {x["id"] for x in bulk_enriched}
    return (
        [r for r in all_enriched if r["id"] in ht_ids],
        [r for r in all_enriched if r["id"] in bulk_ids],
    )

# -- Main compute ---------------------------------------------------------------
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
    for w in watch:
        w["category"]       = WATCHLIST_CATEGORY.get(w["name"], "")
        w["signal_context"] = WATCHLIST_CATALYSTS.get(w["name"], "")
        w["catalyst"]       = WATCHLIST_CATALYSTS.get(w["name"], "")
    watch = sorted(watch, key=lambda r: (
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