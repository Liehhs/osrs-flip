import requests

BASE = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {"User-Agent": "OsrsFlipDashboard/Owen"}
TAX_RATE = 0.02
TAX_CAP = 5_000_000

# Watchlist -- comprehensive raid/boss/clue uniques 500K+
WATCHLIST = [
    # Chambers of Xeric
    ("Twisted bow", "Chambers of Xeric", "Ranged BiS -- rarest CoX unique; permanently scarce supply"),
    ("Kodai wand", "Chambers of Xeric", "Mage BiS autocast -- steady demand from mage PvMers"),
    ("Elder maul", "Chambers of Xeric", "Crush BiS -- update/meta sensitive"),
    ("Ancestral robe top", "Chambers of Xeric", "Mage BiS armour -- reacts to mage balance changes"),
    ("Ancestral robe bottom", "Chambers of Xeric", "Mage BiS armour -- tied to top demand"),
    ("Ancestral hat", "Chambers of Xeric", "Mage BiS helm -- completes ancestral set"),
    ("Dragon claws", "Chambers of Xeric", "Spec weapon -- high PvP + PvM demand; volatile"),
    ("Dexterous prayer scroll", "Chambers of Xeric", "Rigour unlock -- CoX participation proxy"),
    ("Arcane prayer scroll", "Chambers of Xeric", "Augury unlock -- tied to mage demand"),
    ("Olmlet", "Chambers of Xeric", "CoX pet -- collector value"),

    # Theatre of Blood
    ("Scythe of vitur", "Theatre of Blood", "Melee BiS for raids/slayer -- essential endgame weapon"),
    ("Ghrazi rapier", "Theatre of Blood", "Stab BiS -- strengthened by melee rebalance"),
    ("Sanguinesti staff (uncharged)", "Theatre of Blood", "Mage weapon -- buff-sensitive and raid demand linked"),
    ("Avernic defender hilt", "Theatre of Blood", "Defender upgrade -- tied to ToB/raids participation"),
    ("Justiciar faceguard", "Theatre of Blood", "Tank helm -- vulnerable to reduced tank-set relevance"),
    ("Justiciar chestguard", "Theatre of Blood", "Tank body -- demand tied to full set"),
    ("Justiciar legguards", "Theatre of Blood", "Tank legs -- demand tied to full set"),
    ("Scythe of vitur ornament kit", "Theatre of Blood", "HM cosmetic kit -- prestige item"),
    ("Sanguinesti staff ornament kit", "Theatre of Blood", "HM cosmetic kit -- prestige item"),
    ("Sanguine scythe of vitur", "Theatre of Blood", "HM cosmetic prestige item"),
    ("Lil' Zik", "Theatre of Blood", "ToB pet -- collector value"),

    # Tombs of Amascut
    ("Tumeken's shadow", "Tombs of Amascut", "Mage BiS -- major endgame demand anchor"),
    ("Osmumten's fang", "Tombs of Amascut", "Stab BiS -- ToA participation proxy"),
    ("Elidinis' ward (f)", "Tombs of Amascut", "Mage offhand BiS -- completes ToA mage setup"),
    ("Masori body (f)", "Tombs of Amascut", "Range BiS armour -- tied to endgame range meta"),
    ("Masori chaps (f)", "Tombs of Amascut", "Range BiS legs -- paired with body demand"),
    ("Masori mask (f)", "Tombs of Amascut", "Range BiS helm -- completes Masori set"),
    ("Masori body", "Tombs of Amascut", "Range armour -- upgrades to (f)"),
    ("Masori chaps", "Tombs of Amascut", "Range legs -- upgrades to (f)"),
    ("Masori mask", "Tombs of Amascut", "Range helm -- upgrades to (f)"),
    ("Elidinis' ward", "Tombs of Amascut", "Mage offhand -- upgrades to (f)"),
    ("Osmumten's fang (or)", "Tombs of Amascut", "ToA ornamental fang -- prestige variant"),
    ("Tumeken's guardian", "Tombs of Amascut", "ToA pet -- collector value"),

    # Nightmare
    ("Inquisitor's mace", "The Nightmare", "Crush BiS -- patch-sensitive unique"),
    ("Inquisitor's hauberk", "The Nightmare", "Armour piece -- risk if set relevance drops"),
    ("Inquisitor's plateskirt", "The Nightmare", "Armour piece -- risk if set relevance drops"),
    ("Nightmare staff", "The Nightmare", "Staff base for orb upgrades"),
    ("Eldritch nightmare staff", "The Nightmare", "Prayer restore spec weapon"),
    ("Volatile nightmare staff", "The Nightmare", "Mage spec weapon"),
    ("Harmonised nightmare staff", "The Nightmare", "Mage BiS assembled staff"),
    ("Little nightmare", "The Nightmare", "Nightmare pet -- collector value"),

    # Corrupted Gauntlet
    ("Enhanced crystal weapon seed", "Corrupted Gauntlet", "Bowfa component -- early/endgame range staple"),
    ("Crystal armour seed", "Corrupted Gauntlet", "Crystal armour component -- Bowfa ecosystem"),
    ("Youngllef", "Corrupted Gauntlet", "Gauntlet pet -- collector value"),

    # Fortis Colosseum
    ("Tonalztics of ralos", "Fortis Colosseum", "Colosseum mega-rare -- high-end ranged spec weapon"),
    ("Echo crystal", "Fortis Colosseum", "Boot upgrade component -- attached to guardian boots"),
    ("Sunfire fanatic helm", "Fortis Colosseum", "Sunfire set helm -- Colosseum unique"),
    ("Sunfire fanatic cuirass", "Fortis Colosseum", "Sunfire set body -- Colosseum unique"),
    ("Sunfire fanatic chausses", "Fortis Colosseum", "Sunfire set legs -- Colosseum unique"),

    # Nex
    ("Torva platebody", "Nex", "Melee BiS body -- high-end demand proxy"),
    ("Torva platelegs", "Nex", "Melee BiS legs -- high-end demand proxy"),
    ("Torva full helm", "Nex", "Completes Torva set -- high-end melee demand"),
    ("Zaryte crossbow", "Nex", "Endgame ranged weapon -- meta-sensitive"),
    ("Zaryte vambraces", "Nex", "Endgame range gloves BiS"),
    ("Nihil horn", "Nex", "ZCB component -- demand tied to ZCB"),
    ("Ancient hilt", "Nex", "Ancient godsword hilt -- niche but expensive"),

    # DT2 bosses
    ("Soulreaper axe", "Vardorvis", "High-end melee weapon -- heavily balance-sensitive"),
    ("Ultor ring", "Vardorvis", "Strength ring -- melee demand proxy"),
    ("Bellator ring", "The Whisperer", "Melee ring -- endgame demand proxy"),
    ("Magus ring", "Duke Sucellus", "Mage ring -- shadow ecosystem demand"),
    ("Venator ring", "The Leviathan", "Range ring -- endgame demand proxy"),
    ("Virtus robe top", "Duke Sucellus", "Mage hybrid armour -- tied to virtus set demand"),
    ("Virtus robe bottom", "Duke Sucellus", "Mage hybrid armour -- tied to virtus set demand"),
    ("Awakener's orb", "Vardorvis", "Awakened boss unlock item"),
    ("Blood quartz", "Vardorvis", "Ring upgrade component"),
    ("Smoke quartz", "Duke Sucellus", "Ring upgrade component"),
    ("Ice quartz", "The Leviathan", "Ring upgrade component"),
    ("Shadow quartz", "The Whisperer", "Ring upgrade component"),

    # GWD
    ("Bandos chestplate", "General Graardor", "Melee armour staple"),
    ("Bandos tassets", "General Graardor", "Melee armour staple"),
    ("Bandos boots", "General Graardor", "Melee boots"),
    ("Bandos godsword", "General Graardor", "Spec weapon"),
    ("Armadyl chestplate", "Kree'arra", "Range armour staple"),
    ("Armadyl chainskirt", "Kree'arra", "Range armour staple"),
    ("Armadyl helmet", "Kree'arra", "Range armour helm"),
    ("Armadyl godsword", "Kree'arra", "PvP/PvM spec weapon"),
    ("Saradomin godsword", "Commander Zilyana", "SGS utility weapon"),
    ("Saradomin sword", "Commander Zilyana", "Mid-tier melee weapon"),
    ("Zamorak godsword", "K'ril Tsutsaroth", "PvP niche weapon"),
    ("Staff of the dead", "K'ril Tsutsaroth", "Mage staff"),
    ("Steam battlestaff", "K'ril Tsutsaroth", "Mage staff"),
    ("Zamorakian spear", "K'ril Tsutsaroth", "Corp/stab niche weapon"),

    # Zulrah / Vorkath / Cerb / Hydra / Slayer bosses
    ("Tanzanite fang", "Zulrah", "Toxic blowpipe component"),
    ("Magic fang", "Zulrah", "Trident/staff upgrade"),
    ("Serpentine visage", "Zulrah", "Helm component"),
    ("Tanzanite mutagen", "Zulrah", "Rare cosmetic mutagen"),
    ("Magma mutagen", "Zulrah", "Rare cosmetic mutagen"),
    ("Jar of swamp", "Zulrah", "Collector cosmetic"),
    ("Snakeling", "Zulrah", "Pet"),
    ("Dragonbone necklace", "Vorkath", "Prayer necklace"),
    ("Skeletal visage", "Vorkath", "Dragonfire ward component"),
    ("Vorkath's head", "Vorkath", "Assembler component"),
    ("Jar of decay", "Vorkath", "Collector cosmetic"),
    ("Vorki", "Vorkath", "Pet"),
    ("Primordial crystal", "Cerberus", "Primordial boots component"),
    ("Eternal crystal", "Cerberus", "Eternal boots component"),
    ("Pegasian crystal", "Cerberus", "Pegasian boots component"),
    ("Smouldering stone", "Cerberus", "Infernal tool upgrade"),
    ("Hellpuppy", "Cerberus", "Pet"),
    ("Hydra's claw", "Alchemical Hydra", "Dragon hunter lance component"),
    ("Hydra leather", "Alchemical Hydra", "Ferocious gloves component"),
    ("Brimstone ring", "Alchemical Hydra", "Hybrid ring"),
    ("Hydra's eye", "Alchemical Hydra", "Brimstone ring component"),
    ("Hydra's fang", "Alchemical Hydra", "Brimstone ring component"),
    ("Hydra's heart", "Alchemical Hydra", "Brimstone ring component"),
    ("Jar of chemicals", "Alchemical Hydra", "Collector cosmetic"),
    ("Ikkle hydra", "Alchemical Hydra", "Pet"),
    ("Basilisk jaw", "Basilisk Knight", "Faceguard component"),
    ("Venator shard", "Phantom Muspah", "Venator bow component"),
    ("Frozen cache", "Phantom Muspah", "Ancient sceptre upgrade source"),
    ("Charged ice", "Phantom Muspah", "Spell enhancement"),
    ("Muphin", "Phantom Muspah", "Pet"),
    ("Abyssal whip", "Abyssal Demon", "Mid-tier staple weapon"),
    ("Abyssal dagger", "Abyssal Sire", "Spec dagger"),
    ("Abyssal bludgeon", "Abyssal Sire", "Crush weapon"),
    ("Abyssal orphan", "Abyssal Sire", "Pet"),
    ("Trident of the seas (full)", "Kraken", "Mage weapon"),
    ("Kraken tentacle", "Kraken", "Whip upgrade"),
    ("Pet kraken", "Kraken", "Pet"),
    ("Occult necklace", "Thermonuclear Smoke Devil", "Mage neck BiS"),
    ("Smoke battlestaff", "Thermonuclear Smoke Devil", "Mage staff"),
    ("Pet smoke devil", "Thermonuclear Smoke Devil", "Pet"),
    ("Black tourmaline core", "Grotesque Guardians", "Granite upgrade component"),
    ("Granite gloves", "Grotesque Guardians", "Granite upgrade"),
    ("Granite ring", "Grotesque Guardians", "Granite upgrade"),
    ("Granite hammer", "Grotesque Guardians", "Crush weapon"),
    ("Jar of stone", "Grotesque Guardians", "Collector cosmetic"),
    ("Noon", "Grotesque Guardians", "Pet"),

    # Newer bosses
    ("Araxyte fang", "Araxxor", "Araxxor unique -- high-value stab upgrade component"),
    ("Noxious halberd", "Araxxor", "Araxxor unique -- assembled halberd"),
    ("Dragon hunter wand", "Hueycoatl", "Hueycoatl unique -- dragon hunter mage weapon"),
    ("Pendant of ates", "Amoxliatl", "Amoxliatl unique -- Varlamore boss drop"),
    ("Glacial temotli", "Amoxliatl", "Amoxliatl unique weapon"),

    # Moons of Peril
    ("Blood moon helm", "Blood Moon", "Perilous Moons set piece"),
    ("Blood moon chestplate", "Blood Moon", "Perilous Moons set piece"),
    ("Blood moon tassets", "Blood Moon", "Perilous Moons set piece"),
    ("Blue moon spear", "Blue Moon", "Perilous Moons weapon"),
    ("Blue moon helm", "Blue Moon", "Perilous Moons set piece"),
    ("Blue moon chestplate", "Blue Moon", "Perilous Moons set piece"),
    ("Blue moon tassets", "Blue Moon", "Perilous Moons set piece"),
    ("Eclipse moon helm", "Eclipse Moon", "Perilous Moons set piece"),
    ("Eclipse moon chestplate", "Eclipse Moon", "Perilous Moons set piece"),
    ("Eclipse moon tassets", "Eclipse Moon", "Perilous Moons set piece"),

    # Corp / DKs / KQ / KBD / Sarachnis / Skotizo / Wildy / Barrows / misc
    ("Elysian spirit shield", "Corporeal Beast", "Prestige tank shield -- fixed-supply store of value"),
    ("Arcane spirit shield", "Corporeal Beast", "Mage spirit shield"),
    ("Spectral spirit shield", "Corporeal Beast", "Prayer shield"),
    ("Elysian sigil", "Corporeal Beast", "Shield component"),
    ("Arcane sigil", "Corporeal Beast", "Shield component"),
    ("Spectral sigil", "Corporeal Beast", "Shield component"),
    ("Holy elixir", "Corporeal Beast", "Shield component"),
    ("Spirit shield", "Corporeal Beast", "Shield base"),
    ("Berserker ring", "Dagannoth Rex", "Melee ring"),
    ("Archers ring", "Dagannoth Rex", "Range ring"),
    ("Seers ring", "Dagannoth Rex", "Mage ring"),
    ("Warrior ring", "Dagannoth Rex", "Slash ring"),
    ("Dragon axe", "Dagannoth Prime", "Skilling axe"),
    ("Mud battlestaff", "Dagannoth Prime", "Mage staff"),
    ("Seercull", "Dagannoth Supreme", "Ranged weapon"),
    ("Dragon chainbody", "Kalphite Queen", "Mid-tier armour"),
    ("Kalphite princess", "Kalphite Queen", "Pet"),
    ("Jar of sand", "Kalphite Queen", "Collector cosmetic"),
    ("Draconic visage", "King Black Dragon", "Dragonfire shield component"),
    ("Prince black dragon", "King Black Dragon", "Pet"),
    ("Jar of dirt", "King Black Dragon", "Collector cosmetic"),
    ("Sarachnis cudgel", "Sarachnis", "Crush weapon"),
    ("Sraracha", "Sarachnis", "Pet"),
    ("Skotos", "Skotizo", "Pet"),
    ("Odium ward", "Chaos Elemental", "Wilderness offhand"),
    ("Malediction ward", "Chaos Elemental", "Wilderness offhand"),
    ("Dragon 2h sword", "Chaos Elemental", "Wilderness boss drop"),
    ("Dragon pickaxe", "Chaos Elemental", "Skilling staple"),
    ("Thammaron's sceptre", "Calvar'ion", "Wildy weapon"),
    ("Viggora's chainmace", "Calvar'ion", "Wildy weapon"),
    ("Craw's bow", "Calvar'ion", "Wildy weapon"),
    ("Ursine chainmace", "Calvar'ion", "Wildy upgraded weapon"),
    ("Webweaver bow", "Calvar'ion", "Wildy upgraded weapon"),
    ("Accursed sceptre", "Calvar'ion", "Wildy upgraded weapon"),
    ("Venomous fangs", "Scorpia", "Wildy boss unique"),
    ("Odium shard 1", "Scorpia", "Ward component"),
    ("Malediction shard 1", "Scorpia", "Ward component"),
    ("Karil's crossbow", "Barrows", "Barrows weapon"),
    ("Ahrim's robetop", "Barrows", "Barrows mage body"),
    ("Ahrim's robeskirt", "Barrows", "Barrows mage legs"),
    ("Torag's platebody", "Barrows", "Barrows tank body"),
    ("Dharok's greataxe", "Barrows", "Popular Barrows weapon"),
    ("Guthan's warspear", "Barrows", "Self-heal weapon"),
    ("Verac's flail", "Barrows", "Niche utility weapon"),
    ("Mole skin", "Giant Mole", "Giant Mole drop"),
    ("Phoenix", "Wintertodt", "Skilling pet"),
    ("Burnt page", "Wintertodt", "Tome of fire charge"),
    ("Spirit angler's top", "Tempoross", "Fishing outfit piece"),
    ("Tackle box", "Tempoross", "Fishing utility item"),

    # Clues 500k+
    ("3rd age platebody", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age platelegs", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age full helmet", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age kiteshield", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age longsword", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age bow", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age wand", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age robe top", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age robe", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age mage hat", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age range top", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age range legs", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age range coif", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age cloak", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age vambraces", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age amulet", "Treasure Trails", "Ultra-rare clue prestige item"),
    ("3rd age druidic robe top", "Treasure Trails", "Ultra-rare master clue item"),
    ("3rd age druidic robe bottoms", "Treasure Trails", "Ultra-rare master clue item"),
    ("3rd age druidic staff", "Treasure Trails", "Ultra-rare master clue item"),
    ("3rd age druidic cloak", "Treasure Trails", "Ultra-rare master clue item"),
    ("3rd age axe", "Treasure Trails", "Ultra-rare master clue item"),
    ("3rd age pickaxe", "Treasure Trails", "Ultra-rare master clue item"),
    ("Ranger boots", "Treasure Trails", "Medium clue staple"),
    ("Wizard boots", "Treasure Trails", "Medium clue mage boots"),
    ("Holy sandals", "Treasure Trails", "Medium clue prayer boots"),
    ("Gilded scimitar", "Treasure Trails", "Gilded clue cosmetic"),
    ("Gilded boots", "Treasure Trails", "Gilded clue cosmetic"),
    ("Gilded full helm", "Treasure Trails", "Gilded clue cosmetic"),
    ("Gilded platebody", "Treasure Trails", "Gilded clue cosmetic"),
    ("Gilded platelegs", "Treasure Trails", "Gilded clue cosmetic"),
    ("Gilded plateskirt", "Treasure Trails", "Gilded clue cosmetic"),
    ("Gilded kiteshield", "Treasure Trails", "Gilded clue cosmetic"),
    ("Gilded med helm", "Treasure Trails", "Gilded clue cosmetic"),
    ("Gilded chainbody", "Treasure Trails", "Gilded clue cosmetic"),
    ("Gilded sq shield", "Treasure Trails", "Gilded clue cosmetic"),
    ("Robin hood hat", "Treasure Trails", "Clue fashionscape staple"),
    ("Black dragon mask", "Treasure Trails", "Rare clue mask"),
    ("Blue dragon mask", "Treasure Trails", "Rare clue mask"),
    ("Green dragon mask", "Treasure Trails", "Rare clue mask"),
    ("Red dragon mask", "Treasure Trails", "Rare clue mask"),
]

WATCHLIST_NAMES = {name for name, _, _ in WATCHLIST}
WATCHLIST_CATALYSTS = {name: catalyst for name, _, catalyst in WATCHLIST}
WATCHLIST_CATEGORY = {name: category for name, category, _ in WATCHLIST}

SIGNALS_UNIVERSE = {
    "Soulreaper axe": "game update|ACTIVE|Major melee rework made this one of the biggest winners.",
    "Ghrazi rapier": "game update|ACTIVE|Strength buff improved rapier DPS and relevance.",
    "Sanguinesti staff (uncharged)": "game update|ACTIVE|Buffed damage and reduced charge cost improved attractiveness.",
    "Inquisitor's mace": "game update|ACTIVE|Standalone value improved relative to old set dependence.",
    "Inquisitor's hauberk": "price risk|ACTIVE|Set synergy weakened, creating downside risk.",
    "Inquisitor's plateskirt": "price risk|ACTIVE|Set synergy weakened, creating downside risk.",
    "Necklace of anguish": "price risk|WATCH|Rupture necklace competition threatens current BIS position.",
    "Zaryte crossbow": "meta shift|WATCH|Range meta upgrades support endgame ranged demand.",
    "Masori body (f)": "meta shift|WATCH|Range-focused setups remain strong into new content cycles.",
    "Masori chaps (f)": "meta shift|WATCH|Range-focused setups remain strong into new content cycles.",
    "Masori mask (f)": "meta shift|WATCH|Range-focused setups remain strong into new content cycles.",
    "Zaryte vambraces": "meta shift|WATCH|Range meta remains supportive for BiS glove demand.",
    "Twisted bow": "raids prep|WATCH|Top-end gear often tightens ahead of new raid releases.",
    "Tumeken's shadow": "raids prep|WATCH|Shadow is a key accumulation candidate into future raid prep.",
    "Scythe of vitur": "raids prep|WATCH|Top-end melee raid gear often moves ahead of major content.",
    "Kodai wand": "raids prep|WATCH|Mage-side raid prep can support Kodai demand and speculation.",
    "Justiciar faceguard": "price risk|ACTIVE|Tank set erosion weakens full Justiciar pricing.",
    "Justiciar chestguard": "price risk|ACTIVE|Tank set erosion weakens full Justiciar pricing.",
    "Justiciar legguards": "price risk|ACTIVE|Tank set erosion weakens full Justiciar pricing.",
    "Araxyte fang": "new content|WATCH|New boss price discovery still settling but demand is strong.",
    "Dragon hunter wand": "new content|WATCH|New dragon-hunter niche creates sustained attention.",
}

SHIFTS_HIGH_TICKET_SEEDS = [
    "Twisted bow", "Tumeken's shadow", "Scythe of vitur", "Soulreaper axe", "Torva platebody",
    "Torva platelegs", "Torva full helm", "Zaryte crossbow", "Elysian spirit shield",
    "Tonalztics of ralos", "Ancestral robe top", "Ancestral robe bottom", "Ghrazi rapier",
    "Sanguinesti staff (uncharged)", "Masori body (f)", "Masori chaps (f)", "Masori mask (f)",
    "Inquisitor's mace", "Ultor ring", "Magus ring", "Bellator ring", "Venator ring",
    "Dragon hunter wand", "Araxyte fang", "Noxious halberd"
]

SHIFTS_BULK_SEEDS = [
    "Blood rune", "Death rune", "Soul rune", "Nature rune", "Dragon darts", "Dragon arrows",
    "Zulrah's scales", "Cannonball", "Saradomin brew(4)", "Super restore(4)", "Shark",
    "Manta ray", "Dragon bones", "Amylase crystal", "Burnt page", "Mole skin"
]


def _get(path, params=None):
    try:
        r = requests.get(f"{BASE}/{path}", headers=HEADERS, params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def fetch_latest():
    return _get("latest") or {}


def fetch_mapping():
    data = _get("mapping") or []
    return data if isinstance(data, list) else []


def fetch_volumes():
    h = _get("1h") or {}
    f = _get("5m") or {}
    return h.get("data", {}) if isinstance(h, dict) else {}, f.get("data", {}) if isinstance(f, dict) else {}


def fetch_timeseries(item_id, timestep="24h"):
    data = _get(f"timeseries", params={"id": item_id, "timestep": timestep}) or {}
    return data.get("data", []) if isinstance(data, dict) else []


def pct_change(cur, prev):
    try:
        cur, prev = float(cur), float(prev)
        if prev <= 0:
            return None
        return round(((cur - prev) / prev) * 100, 2)
    except Exception:
        return None


def classify_trend(ch1, ch7, ch30):
    ch1 = ch1 if ch1 is not None else 0
    ch7 = ch7 if ch7 is not None else 0
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
    "1D shock": "Price shock (1D)",
    "7D move": "Big move (7D)",
    "30D regime": "Regime shift (30D)",
    "Wide spread": "Fat margin",
    "High gp/item": "High GP/item",
    "Liquid": "Liquid market",
    "Flow imbalance": "Buy/sell skew",
}


def event_flags(item):
    raw = []
    ch1 = item.get("chg_1d")
    ch7 = item.get("chg_7d")
    ch30 = item.get("chg_30d")
    roi = item.get("roi", 0) or 0
    buy_hr = item.get("buy_qty_hr", 0) or 0
    sell_hr = item.get("sell_qty_hr", 0) or 0
    ratio = item.get("ratio")
    profit = item.get("profit_unit", 0) or 0

    if ch1 is not None and abs(ch1) >= 5:
        raw.append("1D shock")
    if ch7 is not None and abs(ch7) >= 10:
        raw.append("7D move")
    if ch30 is not None and abs(ch30) >= 15:
        raw.append("30D regime")
    if roi >= 8:
        raw.append("Wide spread")
    if profit >= 500_000:
        raw.append("High gp/item")
    if buy_hr + sell_hr >= 500:
        raw.append("Liquid")
    if ratio is not None and (ratio >= 2.0 or ratio <= 0.6):
        raw.append("Flow imbalance")

    priority = 0
    if "1D shock" in raw:
        priority += 3
    if "7D move" in raw:
        priority += 2
    if "30D regime" in raw:
        priority += 2
    if "Wide spread" in raw:
        priority += 2
    if "High gp/item" in raw:
        priority += 1
    if "Liquid" in raw:
        priority += 1
    if "Flow imbalance" in raw:
        priority += 1

    readable = [_FLAG_LABELS.get(f, f) for f in raw[:4]]
    return readable, priority


def enrich_with_trends(rows):
    enriched = []
    for r in rows:
        item = dict(r)
        ts = fetch_timeseries(r["id"], "24h")
        for k in ("chg_1d", "chg_7d", "chg_30d", "chg_14d", "prev_price_1d", "prev_price_7d", "prev_price_14d", "prev_price_30d"):
            item[k] = None
        item["trend"] = "Flat"
        if ts and len(ts) >= 31:
            highs = [p.get("avgHighPrice") or 0 for p in ts if p.get("avgHighPrice")]
            if len(highs) >= 31:
                cur = highs[-1]
                item["chg_1d"] = pct_change(cur, highs[-2])
                item["chg_7d"] = pct_change(cur, highs[-8])
                item["chg_14d"] = pct_change(cur, highs[-15]) if len(highs) >= 15 else None
                item["chg_30d"] = pct_change(cur, highs[-31])
                item["prev_price_1d"] = int(highs[-2])
                item["prev_price_7d"] = int(highs[-8])
                item["prev_price_14d"] = int(highs[-15]) if len(highs) >= 15 else None
                item["prev_price_30d"] = int(highs[-31])
                item["trend"] = classify_trend(item["chg_1d"], item["chg_7d"], item["chg_30d"])
        flags, priority = event_flags(item)
        item["flags"] = " | ".join(flags) if flags else "Quiet"
        item["priority"] = priority
        if item["name"] in SIGNALS_UNIVERSE:
            item["signal_context"] = SIGNALS_UNIVERSE[item["name"]]
        item["catalyst"] = WATCHLIST_CATALYSTS.get(item["name"], "")
        item["category"] = WATCHLIST_CATEGORY.get(item["name"], item.get("category", "Other"))
        enriched.append(item)
    return enriched


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
            if abs(idx) > len(highs):
                return None
            return pct_change(cur, highs[idx])

        def _prev(n):
            idx = -1 - n
            if abs(idx) > len(highs):
                return None
            return int(highs[idx])

        results[item_id] = {
            "chg_20m": _chg(4),
            "chg_40m": _chg(8),
            "chg_1h": _chg(12),
            "chg_6h": _chg(72),
            "chg_12h": _chg(144),
            "prev_price_20m": _prev(4),
            "prev_price_40m": _prev(8),
            "prev_price_1h": _prev(12),
            "prev_price_6h": _prev(72),
            "prev_price_12h": _prev(144),
        }
    return results


def _apply_tax(price):
    return int(min(price * TAX_RATE, TAX_CAP))


def _ge_limit_for(name):
    low_name = name.lower()
    if any(k in low_name for k in ["bow", "shadow", "scythe", "torva", "masori", "ancestral", "elysian", "3rd age", "zaryte", "soulreaper", "tonalztics"]):
        return 8
    return 70


def compute_flips(latest, mapping, hour_vols, fmin_vols):
    latest_data = latest.get("data", {}) if isinstance(latest, dict) else {}
    mapping_by_name = {m.get("name", ""): m for m in mapping}

    all_rows = []
    for name, meta in mapping_by_name.items():
        item_id = meta.get("id")
        if item_id is None or str(item_id) not in latest_data:
            continue
        market = latest_data[str(item_id)]
        buy_price = market.get("high")
        sell_price = market.get("low")
        if not buy_price or not sell_price or sell_price <= buy_price:
            continue
        tax = _apply_tax(sell_price)
        profit_unit = sell_price - buy_price - tax
        if profit_unit <= 0:
            continue
        roi = round((profit_unit / buy_price) * 100, 2) if buy_price else 0
        buy_qty_hr = (hour_vols.get(str(item_id), {}) or {}).get("highPriceVolume", 0) or 0
        sell_qty_hr = (hour_vols.get(str(item_id), {}) or {}).get("lowPriceVolume", 0) or 0
        daily_volume = buy_qty_hr * 24
        ratio = round((buy_qty_hr / sell_qty_hr), 2) if sell_qty_hr else None
        ge_limit = _ge_limit_for(name)

        if ratio is None:
            fq_label = "No data"
        elif 0.8 <= ratio <= 1.5:
            fq_label = "Ideal"
        elif 0.6 <= ratio < 0.8:
            fq_label = "Slight flood"
        elif ratio < 0.6:
            fq_label = "Flooded"
        elif 1.5 < ratio <= 2.25:
            fq_label = "High demand"
        else:
            fq_label = "Hard to buy"

        realistic_units = min(ge_limit, sell_qty_hr * 4 if sell_qty_hr else ge_limit)
        potential_profit = profit_unit * ge_limit
        realistic_profit = profit_unit * max(realistic_units, 1)
        adj_potential = int(realistic_profit * (1 + min(roi, 25) / 100))

        row = {
            "id": item_id,
            "name": name,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "tax": tax,
            "profit_unit": profit_unit,
            "roi": roi,
            "buy_qty_hr": buy_qty_hr,
            "sell_qty_hr": sell_qty_hr,
            "daily_volume": daily_volume,
            "ratio": ratio,
            "fq_label": fq_label,
            "ge_limit": ge_limit,
            "potential_profit": potential_profit,
            "adj_potential": adj_potential,
            "realistic_profit": realistic_profit,
            "category": WATCHLIST_CATEGORY.get(name, "Other"),
        }
        all_rows.append(row)

    enriched = enrich_with_trends(all_rows)
    name_map = {r["name"]: r for r in enriched}

    bulk_rows = [r for r in enriched if r["buy_qty_hr"] >= 100 and r["sell_qty_hr"] >= 50 and r["ge_limit"] >= 70]
    bulk_rows = sorted(bulk_rows, key=lambda r: (r["realistic_profit"], r["profit_unit"]), reverse=True)[:200]

    singular = [r for r in enriched if r["ge_limit"] <= 8 or r["sell_price"] >= 3_000_000]
    singular = sorted(singular, key=lambda r: (r["adj_potential"], r["profit_unit"]), reverse=True)[:200]

    high_roi = [r for r in enriched if r["buy_qty_hr"] + r["sell_qty_hr"] >= 50]
    high_roi = sorted(high_roi, key=lambda r: (r["roi"], r["profit_unit"]), reverse=True)[:200]

    watch = [name_map[n] for n in WATCHLIST_NAMES if n in name_map and (name_map[n].get("sell_price") or 0) >= 500_000]
    watch = sorted(watch, key=lambda r: ((r.get("priority") or 0), (r.get("sell_price") or 0)), reverse=True)

    signals = [r for r in watch if r.get("name") in SIGNALS_UNIVERSE]
    signals = sorted(signals, key=lambda r: (("ACTIVE" in (r.get("signal_context") or "")), r.get("priority") or 0), reverse=True)

    return bulk_rows, singular, high_roi, watch, signals, enriched


def build_shifts_data(all_rows, mapping):
    name_map = {r["name"].lower(): r for r in all_rows}
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

    ht_enriched = enrich_with_trends(ht_rows)
    bulk_enriched = enrich_with_trends(bulk_rows)

    all_enriched = ht_enriched + bulk_enriched
    item_ids = [r["id"] for r in all_enriched]
    intraday_map = fetch_intraday_shifts(item_ids, {})

    for r in all_enriched:
        intra = intraday_map.get(r["id"], {})
        for k in (
            "chg_20m", "chg_40m", "chg_1h", "chg_6h", "chg_12h",
            "prev_price_20m", "prev_price_40m", "prev_price_1h", "prev_price_6h", "prev_price_12h"
        ):
            r[k] = intra.get(k)

    ht_ids = {x["id"] for x in ht_enriched}
    bulk_ids = {x["id"] for x in bulk_enriched}
    return [r for r in all_enriched if r["id"] in ht_ids], [r for r in all_enriched if r["id"] in bulk_ids]