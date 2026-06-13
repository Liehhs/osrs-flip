import requests

BASE    = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {"User-Agent": "OsrsFlipDashboard/Owen"}
TAX_RATE = 0.02
TAX_CAP  = 5_000_000

# Watchlist -- comprehensive 5M+ bossing/raids drops and endgame gear
WATCHLIST = [
    # ======================================================================
    # RAID UNIQUES
    # ======================================================================
    # -- Chambers of Xeric --
    ("Twisted bow",                    "Chambers of Xeric",  "Ranged BIS -- rarest CoX unique; permanently scarce supply"),
    ("Kodai wand",                     "Chambers of Xeric",  "Mage BIS autocast -- steady demand from mage PvMers"),
    ("Elder maul",                     "Chambers of Xeric",  "Crush BIS -- ToA drives additional demand"),
    ("Ancestral robe top",             "Chambers of Xeric",  "Mage BIS armour -- reactive to mage update announcements"),
    ("Ancestral robe bottom",          "Chambers of Xeric",  "Mage BIS armour -- tied to top demand"),
    ("Ancestral hat",                  "Chambers of Xeric",  "Mage BIS helm -- completes ancestral set"),
    ("Dragon claws",                   "Chambers of Xeric",  "Spec weapon -- high PvP + PvM demand; volatile"),
    ("Dexterous prayer scroll",        "Chambers of Xeric",  "Rigour unlock -- CoX participation proxy"),
    ("Arcane prayer scroll",           "Chambers of Xeric",  "Augury unlock -- tied to Rigour demand"),
    ("Harmonised orb",                 "Chambers of Xeric",  "Mage BIS for NM/PvM -- CoX changes shift supply"),
    ("Volatile orb",                   "Chambers of Xeric",  "High-value spec weapon orb -- spec meta proxy"),
    ("Eldritch orb",                   "Chambers of Xeric",  "Prayer restore spec orb -- niche but stable demand"),
    ("Olmlet",                         "Chambers of Xeric",  "CoX pet -- collector value; tracks CoX activity"),
    # -- Theatre of Blood --
    ("Scythe of vitur",                "Theatre of Blood",   "Melee BIS for slayer/raids -- essential endgame weapon"),
    ("Ghrazi rapier",                  "Theatre of Blood",   "Stab BIS -- Summer Sweep-Up +4 str buff live now"),
    ("Sanguinesti staff (uncharged)",  "Theatre of Blood",   "Mage BIS -- Summer Sweep-Up 6% DPS buff + cheaper charges"),
    ("Avernic defender hilt",          "Theatre of Blood",   "Defender upgrade -- tied to ToB/raids participation"),
    ("Justiciar faceguard",            "Theatre of Blood",   "Tank helm -- set bonus removed in Sweep-Up; demand softening"),
    ("Justiciar chestguard",           "Theatre of Blood",   "Tank body -- set bonus removal reduces full-set value"),
    ("Justiciar legguards",            "Theatre of Blood",   "Tank legs -- same set bonus removal impact"),
    ("Sanguine scythe of vitur",       "Theatre of Blood",   "HM cosmetic -- rare ToB Hard Mode prestige item"),
    ("Scythe of vitur ornament kit",   "Theatre of Blood",   "HM cosmetic kit -- ToB Hard Mode prestige"),
    ("Sanguinesti staff ornament kit", "Theatre of Blood",   "HM cosmetic kit -- ToB Hard Mode prestige"),
    ("Lil' Zik",                       "Theatre of Blood",   "ToB pet -- collector value; tracks ToB activity"),
    # -- Tombs of Amascut --
    ("Tumeken's shadow",               "Tombs of Amascut",  "Mage BIS -- Raids 4 prep meta; confirmed must-have"),
    ("Osmumten's fang",                "Tombs of Amascut",  "Stab BIS -- consistently high ToA activity proxy"),
    ("Elidinis' ward (f)",             "Tombs of Amascut",  "Mage offhand BIS -- completes ToA mage setup"),
    ("Masori body (f)",                "Tombs of Amascut",  "Range BIS armour -- benefits from Necklace of Rupture range meta"),
    ("Masori chaps (f)",               "Tombs of Amascut",  "Range BIS legs -- paired with body demand"),
    ("Masori mask (f)",                "Tombs of Amascut",  "Range BIS helm -- completes Masori set"),
    ("Masori body",                    "Tombs of Amascut",  "Range armour -- upgrades to (f) with thread"),
    ("Masori chaps",                   "Tombs of Amascut",  "Range legs -- upgrades to (f) with thread"),
    ("Masori mask",                    "Tombs of Amascut",  "Range helm -- upgrades to (f) with thread"),
    ("Elidinis' ward",                 "Tombs of Amascut",  "Mage offhand -- upgrades to (f) with arcane sigil"),
    ("Osmumten's fang (or)",           "Tombs of Amascut",  "ToA ornamental fang -- prestige variant"),
    ("Tumeken's guardian",             "Tombs of Amascut",  "ToA pet -- collector value; tracks ToA activity"),
    # -- The Nightmare / Phosani's Nightmare --
    ("Inquisitor's mace",              "The Nightmare",     "Crush BIS -- Sweep-Up standalone buffed; set bonus removed"),
    ("Inquisitor's hauberk",           "The Nightmare",     "Set bonus removed -- weaker with mace post-Sweep-Up; price risk"),
    ("Inquisitor's plateskirt",        "The Nightmare",     "Same as hauberk -- set synergy gone post-Sweep-Up"),
    ("Nightmare staff",                "The Nightmare",     "Mage staff -- base for Harmonised/Volatile/Eldritch orbs"),
    ("Eldritch nightmare staff",       "The Nightmare",     "Prayer restore spec -- assembled from staff + Eldritch orb"),
    ("Volatile nightmare staff",       "The Nightmare",     "Mage spec weapon -- assembled from staff + Volatile orb"),
    ("Harmonised nightmare staff",     "The Nightmare",     "Mage BIS assembled staff -- staff + Harmonised orb"),
    ("Little nightmare",               "The Nightmare",     "Nightmare pet -- collector value"),
    # -- Corrupted Gauntlet / Crystalline --
    ("Enhanced crystal weapon seed",   "Corrupted Gauntlet", "Bowfa component -- universal early endgame range weapon"),
    ("Crystal armour seed",            "Corrupted Gauntlet", "CG armour seed -- Raids 4 prep drives CG participation"),
    ("Youngllef",                      "Corrupted Gauntlet", "Gauntlet pet -- collector; tracks CG activity"),
    # ======================================================================
    # BOSS UNIQUES
    # ======================================================================
    # -- Nex --
    ("Torva platebody",                "Nex",                "Melee BIS body -- Soulreaper axe buff increases melee activity"),
    ("Torva platelegs",                "Nex",                "Melee BIS legs -- melee hype proxy"),
    ("Torva full helm",                "Nex",                "Completes Torva set -- melee demand proxy"),
    ("Zaryte crossbow",                "Nex",                "Range BIS alt -- benefits from Necklace of Rupture range meta"),
    ("Zaryte vambraces",               "Nex",                "Endgame range gloves BIS -- Nex activity proxy"),
    ("Nihil horn",                     "Nex",                "Zaryte crossbow component -- demand tied to ZCB"),
    ("Ancient hilt",                   "Nex",                "Ancient godsword component -- niche PvP/flex item"),
    # -- Desert Treasure II --
    ("Soulreaper axe",                 "Vardorvis",          "Melee BIS -- Summer Sweep-Up major rework; biggest melee buff in years"),
    ("Virtus robe top",                "Duke Sucellus",      "DT2 mage hybrid -- scepter DPS buffs boost mage ecosystem"),
    ("Virtus robe bottom",             "Duke Sucellus",      "DT2 mage hybrid -- tied to Virtus top demand"),
    ("Bellator ring",                  "The Whisperer",      "Melee ring -- Soulreaper buff raises melee demand proxy"),
    ("Venator ring",                   "The Leviathan",      "Range ring -- bow consistency fix in Sweep-Up aids range meta"),
    ("Magus ring",                     "Duke Sucellus",      "Mage ring -- tied to Shadow + ancestral scepter buff ecosystem"),
    ("Ultor ring",                     "Vardorvis",          "Strength ring -- melee proxy; Soulreaper hype driver"),
    ("Awakener's orb",                 "Vardorvis",          "Awakened boss unlock -- needed for all 4 DT2 awakened variants"),
    # -- God Wars Dungeon --
    ("Bandos chestplate",              "General Graardor",   "Melee BIS body at mid-tier -- returning-player demand proxy"),
    ("Bandos tassets",                 "General Graardor",   "Melee BIS legs -- pairs with chestplate demand"),
    ("Bandos godsword",                "General Graardor",   "Spec weapon -- 10% defence drain; PvP + PvM demand"),
    ("Armadyl chestplate",             "Kree'arra",           "Range mid-tier body -- solid baseline demand"),
    ("Armadyl chainskirt",             "Kree'arra",           "Range mid-tier legs -- pairs with chestplate"),
    ("Armadyl helmet",                 "Kree'arra",           "Range mid-tier helm -- completes Armadyl set"),
    ("Armadyl godsword",               "Kree'arra",           "Spec weapon -- 25% spec; PvP staple"),
    ("Saradomin godsword",             "Commander Zilyana",  "SGS spec -- prayer restore; PvP utility + BIS for some styles"),
    ("Zamorak godsword",               "K'ril Tsutsaroth",   "ZGS spec -- massive str boost; PvP niche"),
    ("Steam battlestaff",              "K'ril Tsutsaroth",   "Mage staff -- steady mid-tier mage demand"),
    ("Staff of the dead",              "K'ril Tsutsaroth",   "Mage staff -- damage reduction spec; enduring demand"),
    ("Ancient hilt",                   "Nex",                "Ancient godsword hilt -- niche PvP/collector item"),
    # -- Zulrah --
    ("Tanzanite fang",                 "Zulrah",             "Toxic blowpipe component -- universal early-mid BIS range weapon"),
    ("Magic fang",                     "Zulrah",             "Toxic staff upgrade -- budget mage weapon"),
    ("Serpentine visage",              "Zulrah",             "Serpentine helm component -- slayer/venom utility"),
    ("Uncut onyx",                     "Zulrah",             "Amulet of fury component -- consistent demand from onyx amulet upgrades"),
    ("Tanzanite mutagen",              "Zulrah",             "Blowpipe cosmetic swap -- rare prestige item"),
    ("Magma mutagen",                  "Zulrah",             "Helm cosmetic swap -- rare prestige item"),
    # -- Vorkath --
    ("Dragonbone necklace",            "Vorkath",            "Prayer necklace -- niche prayer-heavy build demand"),
    ("Skeletal visage",                "Vorkath",            "Dragonfire ward component -- anti-dragon shield upgrade"),
    ("Jar of decay",                   "Vorkath",            "Vorkath cosmetic -- collector item"),
    # -- Cerberus --
    ("Primordial crystal",             "Cerberus",           "Primordial boots component -- BIS melee boots; 1/512 drop"),
    ("Eternal crystal",                "Cerberus",           "Eternal boots component -- BIS mage boots; 1/512 drop"),
    ("Pegasian crystal",               "Cerberus",           "Pegasian boots component -- BIS range boots; 1/512 drop"),
    ("Smouldering stone",              "Cerberus",           "Dragon axe/pickaxe infernal upgrade -- skilling BIS component"),
    # -- Kalphite Queen --
    ("Dragon chainbody",               "Kalphite Queen",     "Mid-tier melee body -- steady baseline demand"),
    ("Jar of sand",                    "Kalphite Queen",     "KQ cosmetic drop -- collector item"),
    # -- King Black Dragon --
    ("Draconic visage",                "King Black Dragon",  "Dragonfire shield component -- consistent mid-game demand"),
    ("Prince black dragon",            "King Black Dragon",  "KBD pet -- collector value"),
    # -- Dagannoth Kings --
    ("Berserker ring",                 "Dagannoth Rex",      "Melee ring -- imbue at NMZ; consistent demand"),
    ("Archers ring",                   "Dagannoth Rex",      "Range ring -- imbue at NMZ; steady mid-tier"),
    ("Seers ring",                     "Dagannoth Rex",      "Mage ring -- imbue at NMZ; mid-tier mage demand"),
    ("Warrior ring",                   "Dagannoth Rex",      "Slash ring -- imbue at NMZ; niche demand"),
    ("Dragon axe",                     "Dagannoth Prime",    "BIS woodcutting axe -- consistent skilling upgrade demand"),
    # -- Abyssal Sire --
    ("Abyssal dagger",                 "Abyssal Sire",       "Spec dagger -- whip complement; stable slayer demand"),
    ("Abyssal bludgeon",               "Abyssal Sire",       "Crush weapon -- slayer/DPS option; Sweep-Up standalone mace buff affects"),
    ("Unsired",                        "Abyssal Sire",       "Rare drop for bludgeon/whip pieces -- tracks Sire activity"),
    # -- Kraken --
    ("Trident of the seas (full)",     "Kraken",             "Mage weapon -- reliable mid-game mage DPS staple"),
    ("Kraken tentacle",                "Kraken",             "Abyssal whip upgrade -- consistent demand from slayer progression"),
    # -- Thermonuclear Smoke Devil --
    ("Occult necklace",                "Thermonuclear Smoke Devil", "Mage BIS neck -- permanent high demand from mage players"),
    ("Smoke battlestaff",              "Thermonuclear Smoke Devil", "Staff -- niche water/smoke spell demand"),
    # -- Grotesque Guardians --
    ("Black tourmaline core",          "Grotesque Guardians","Granite gloves/ring upgrade component -- niche slayer demand"),
    ("Jar of stone",                   "Grotesque Guardians","GG cosmetic -- collector item"),
    # -- Alchemical Hydra --
    ("Hydra's claw",                   "Alchemical Hydra",   "Dragon hunter lance component -- BIS Vorkath/KBD melee weapon"),
    ("Hydra leather",                  "Alchemical Hydra",   "Ferocious gloves component -- melee BIS gloves"),
    ("Hydra's heart",                  "Alchemical Hydra",   "Alchemical Hydra cosmetic piece -- collector"),
    ("Brimstone ring",                 "Alchemical Hydra",   "Hybrid combat ring -- consistent PvM demand"),
    ("Jar of chemicals",               "Alchemical Hydra",   "Hydra cosmetic -- collector item"),
    # -- Phantom Muspah --
    ("Venator shard",                  "Phantom Muspah",     "Venator bow component -- range BIS bow (4 shards needed)"),
    ("Frozen cache",                   "Phantom Muspah",     "Unlock cache -- contains ancient sceptre upgrades"),
    ("Charged ice",                    "Phantom Muspah",     "Ancient freeze spell enhancement component"),
    # -- Doom of Mokhaiotl (Doom's Delve) --
    ("Sunfire splinters",              "Doom of Mokhaiotl",  "Sunfire rune component -- used in powerful offensive spells"),
    ("Obsidian armour set",            "Doom of Mokhaiotl",  "Melee hybrid armour -- popular mid/high-tier armour option"),
    ("Smol heredit",                   "Doom of Mokhaiotl",  "Doom boss pet -- collector; tracks Doom activity"),
    # -- Moons of Peril (Varlamore) --
    ("Eclipse atlatl",                 "Eclipse Moon",       "New range weapon -- PvP nerfed in Sweep-Up; PvM use stable"),
    ("Blood moon helm",                "Blood Moon",         "Mid-tier melee helm -- Varlamore activity proxy"),
    ("Blood moon chestplate",          "Blood Moon",         "Mid-tier melee body -- tied to helm demand"),
    ("Blood moon tassets",             "Blood Moon",         "Mid-tier melee legs -- completes Blood Moon set"),
    ("Blue moon spear",                "Blue Moon",          "Mid-tier stab weapon -- Varlamore activity proxy"),
    ("Blue moon helm",                 "Blue Moon",          "Mid-tier helm -- hybrid combat use"),
    # -- Sarachnis --
    ("Sarachnis cudgel",               "Sarachnis",          "Crush weapon -- cheap melee DPS option; consistent slayer demand"),
    # -- Skotizo --
    ("Skotos",                         "Skotizo",            "Skotizo pet -- collector; dark totem grinds proxy"),
    ("Dexterous prayer scroll",        "Chambers of Xeric",  "Duplicate removed -- see CoX"),
    # -- Corporeal Beast --
    ("Elysian spirit shield",          "Corporeal Beast",    "Prestige tank shield -- fixed supply store-of-value"),
    ("Arcane spirit shield",           "Corporeal Beast",    "Mage spirit shield -- steady collector demand"),
    ("Spectral spirit shield",         "Corporeal Beast",    "Prayer/mage def shield -- niche but tracked"),
    ("Holy elixir",                    "Corporeal Beast",    "Spirit shield blessing -- consistent demand for shield builds"),
    # -- Thermy --
    ("Jar of smoke",                   "Thermonuclear Smoke Devil", "Thermy cosmetic -- collector item"),
    # ======================================================================
    # CLUE UNIQUES (500K+ threshold)
    # ======================================================================
    # 3rd Age (ultra-rare hard/elite/master)
    ("3rd age platebody",              "Treasure Trails",    "Ultra-rare hard/elite clue -- store-of-value; ~1/42K rate"),
    ("3rd age platelegs",              "Treasure Trails",    "Ultra-rare hard clue -- pairs with platebody"),
    ("3rd age full helmet",            "Treasure Trails",    "Ultra-rare hard clue -- completes 3rd age melee set"),
    ("3rd age kiteshield",             "Treasure Trails",    "Ultra-rare hard clue -- 3rd age melee shield"),
    ("3rd age longsword",              "Treasure Trails",    "Rare hard clue -- speculative; very low supply"),
    ("3rd age bow",                    "Treasure Trails",    "Ultra-rare elite/master clue -- range prestige item"),
    ("3rd age wand",                   "Treasure Trails",    "Ultra-rare elite clue -- mage prestige item"),
    ("3rd age robe top",               "Treasure Trails",    "Ultra-rare elite clue -- mage 3rd age body"),
    ("3rd age robe",                   "Treasure Trails",    "Ultra-rare elite clue -- mage 3rd age legs"),
    ("3rd age mage hat",               "Treasure Trails",    "Ultra-rare elite clue -- mage 3rd age helm"),
    ("3rd age range top",              "Treasure Trails",    "Ultra-rare elite clue -- range 3rd age body"),
    ("3rd age range legs",             "Treasure Trails",    "Ultra-rare elite clue -- range 3rd age legs"),
    ("3rd age range coif",             "Treasure Trails",    "Ultra-rare elite clue -- range 3rd age helm"),
    ("3rd age cloak",                  "Treasure Trails",    "Rare master clue -- complement to 3rd age sets"),
    ("3rd age vambraces",              "Treasure Trails",    "Rare hard/elite clue -- range gloves prestige"),
    ("3rd age amulet",                 "Treasure Trails",    "Ultra-rare master clue -- prestige neck"),
    ("3rd age druidic robe top",       "Treasure Trails",    "Ultra-rare master clue -- rarest 3rd age prayer set piece"),
    ("3rd age druidic robe bottoms",   "Treasure Trails",    "Ultra-rare master clue -- 3rd age prayer set"),
    ("3rd age druidic staff",          "Treasure Trails",    "Ultra-rare master clue -- prayer staff prestige"),
    ("3rd age druidic cloak",          "Treasure Trails",    "Ultra-rare master clue -- prayer cloak prestige"),
    ("3rd age axe",                    "Treasure Trails",    "Ultra-rare master clue -- skilling prestige item"),
    ("3rd age pickaxe",                "Treasure Trails",    "Ultra-rare master clue -- skilling prestige item"),
    # Gilded items
    ("Gilded platebody",               "Treasure Trails",    "Elite/master clue -- prestige melee body"),
    ("Gilded platelegs",               "Treasure Trails",    "Elite/master clue -- gilded melee legs"),
    ("Gilded plateskirt",              "Treasure Trails",    "Elite/master clue -- gilded melee skirt"),
    ("Gilded full helm",               "Treasure Trails",    "Elite/master clue -- gilded melee helm"),
    ("Gilded kiteshield",              "Treasure Trails",    "Elite/master clue -- gilded shield"),
    ("Gilded scimitar",                "Treasure Trails",    "Hard/elite gilded -- cosmetic floor item"),
    ("Gilded boots",                   "Treasure Trails",    "Elite clue gilded -- fashionscape demand"),
    ("Gilded coif",                    "Treasure Trails",    "Elite clue gilded -- range cosmetic"),
    ("Gilded d'hide vambs",            "Treasure Trails",    "Elite clue gilded -- range gloves cosmetic"),
    ("Gilded d'hide body",             "Treasure Trails",    "Elite clue gilded -- range body cosmetic"),
    ("Gilded d'hide chaps",            "Treasure Trails",    "Elite clue gilded -- range legs cosmetic"),
    ("Gilded spade",                   "Treasure Trails",    "Master clue -- rare clue cosmetic tool"),
    # Ranger set
    ("Ranger boots",                   "Treasure Trails",    "Medium clue BIS range boots -- high demand relative to rate"),
    ("Ranger gloves",                  "Treasure Trails",    "Hard clue -- BIS range gloves for certain setups"),
    ("Robin hood hat",                 "Treasure Trails",    "Hard clue range helm -- consistently desired cosmetic"),
    ("Ranger hat",                     "Treasure Trails",    "Elite clue range cosmetic -- part of ranger set"),
    ("Ranger top",                     "Treasure Trails",    "Elite clue -- full ranger set body piece"),
    ("Ranger tights",                  "Treasure Trails",    "Elite clue -- ranger set legs"),
    # Blessed d'hide sets
    ("Saradomin d'hide body",          "Treasure Trails",    "Blessed d'hide body -- Saradomin cosmetic; consistent hard clue demand"),
    ("Armadyl d'hide body",            "Treasure Trails",    "Blessed d'hide body -- Armadyl cosmetic variant"),
    ("Zamorak d'hide body",            "Treasure Trails",    "Blessed d'hide body -- Zamorak cosmetic"),
    ("Ancient d'hide body",            "Treasure Trails",    "Blessed d'hide body -- Ancient cosmetic"),
    ("Bandos d'hide body",             "Treasure Trails",    "Blessed d'hide body -- Bandos cosmetic"),
    ("Guthix d'hide body",             "Treasure Trails",    "Blessed d'hide body -- Guthix cosmetic"),
    ("Saradomin d'hide boots",         "Treasure Trails",    "Blessed boots -- cosmetic upgrade over black d'hide boots"),
    ("Armadyl d'hide boots",           "Treasure Trails",    "Blessed boots -- Armadyl cosmetic variant"),
    ("Zamorak d'hide boots",           "Treasure Trails",    "Blessed boots -- Zamorak cosmetic variant"),
    ("Ancient d'hide boots",           "Treasure Trails",    "Blessed boots -- Ancient cosmetic variant"),
    ("Bandos d'hide boots",            "Treasure Trails",    "Blessed boots -- Bandos cosmetic variant"),
    ("Guthix d'hide boots",            "Treasure Trails",    "Blessed boots -- Guthix cosmetic variant"),
    # Ornament kits
    ("Torture ornament kit",           "Treasure Trails",    "Elite clue ornament -- amulet of torture cosmetic"),
    ("Occult ornament kit",            "Treasure Trails",    "Elite clue ornament -- occult necklace cosmetic"),
    ("Dragon defender ornament kit",   "Treasure Trails",    "Elite clue ornament -- defender cosmetic; consistent demand"),
    ("Berserker necklace ornament kit","Treasure Trails",    "Elite clue ornament -- decorative upgrade; low supply"),
    ("Fury ornament kit",              "Treasure Trails",    "Elite clue ornament -- amulet of fury cosmetic"),
    ("Dragon platebody ornament kit",  "Treasure Trails",    "Master clue ornament -- dragon platebody cosmetic"),
    ("Dragon platelegs ornament kit",  "Treasure Trails",    "Master clue ornament -- dragon platelegs cosmetic"),
    ("Dragon full helm ornament kit",  "Treasure Trails",    "Master clue ornament -- dragon full helm cosmetic"),
    ("Dragon chainbody ornament kit",  "Treasure Trails",    "Master clue ornament -- dragon chain cosmetic"),
    ("Dragon boots ornament kit",      "Treasure Trails",    "Master clue ornament -- dragon boots cosmetic"),
    ("Dragon kiteshield ornament kit", "Treasure Trails",    "Master clue ornament -- dragon kiteshield cosmetic"),
    ("Helm of neitiznot (f)",          "Treasure Trails",    "Elite clue cosmetic -- popular mid-tier helm upgrade look"),
    # Miscellaneous high-demand
    ("Black cavalier",                 "Treasure Trails",    "Hard clue cosmetic hat -- fashionscape staple"),
    ("Pirates' hat",                   "Treasure Trails",    "Medium/hard clue -- popular cosmetic; consistent collector demand"),
    ("Musketeer tabard",               "Treasure Trails",    "Medium clue -- fashionscape demand"),
    ("Highwayman mask",                "Treasure Trails",    "Medium clue -- recognisable cosmetic; steady demand"),
    ("Rune scimitar ornament kit (Saradomin)", "Treasure Trails", "Hard clue ornament kit -- consistent fashionscape demand"),
    ("Rune scimitar ornament kit (Zamorak)",   "Treasure Trails", "Hard clue ornament kit -- consistent fashionscape demand"),
    ("Holy sandals",                   "Treasure Trails",    "Hard clue -- niche prayer/cosmetic appeal"),
    ("Briefcase",                      "Treasure Trails",    "Master clue -- rare cosmetic backpack; collector item"),
    ("Bloodhound",                     "Treasure Trails",    "Master clue pet -- tracks master clue activity"),
]
WATCHLIST_NAMES     = [w[0] for w in WATCHLIST]
WATCHLIST_CATALYSTS = {w[0]: w[2] for w in WATCHLIST}
WATCHLIST_CATEGORY  = {w[0]: w[1] for w in WATCHLIST}


# Signals Universe -- TYPE | STATUS | REASON
SIGNALS_UNIVERSE = {
    # ---- ACTIVE: Blood Moon Rises (June 30) ----
    "Necklace of anguish":          "Game Update | ACTIVE | Necklace of Rupture (new BIS range neck) releases June 30 -- direct price displacement risk",
    "Soulreaper axe":               "Game Update | ACTIVE | Summer Sweep-Up rework live -- stacks to 5, 50% acc buff, 12.5% def drain per hit",
    "Sanguinesti staff (uncharged)":"Game Update | ACTIVE | Summer Sweep-Up: 6% DPS buff, charge cost cut 3->2 blood runes -- demand spike",
    "Ghrazi rapier":                "Game Update | ACTIVE | Summer Sweep-Up: +4 strength bonus -- guaranteed extra max hit in all setups",
    "Inquisitor's mace":            "Game Update | ACTIVE | Sweep-Up: standalone str buffed but set bonus removed -- net weaker with full Inq",
    "Inquisitor's hauberk":         "Price Risk | ACTIVE | Inquisitor set bonus removed -- pieces no longer synergise; demand for full set softening",
    "Inquisitor's plateskirt":      "Price Risk | ACTIVE | Same as hauberk -- set synergy gone; price risk if mace-only meta forms",
    # ---- ACTIVE: Raids 4 prep ----
    "Twisted bow":                  "Raids Prep | ACTIVE | Raids 4 (Autumn 2026) -- Tbow confirmed as prep BiS; community accumulating now",
    "Tumeken's shadow":             "Raids Prep | ACTIVE | Raids 4 prep -- Shadow confirmed BIS mage for Fractured Archive; must-have",
    "Scythe of vitur":              "Raids Prep | ACTIVE | Raids 4 prep -- Scythe closest reference melee weapon; accumulation phase",
    # ---- WATCH: Blood Moon Rises displacement ----
    "Tormented bracelet":           "Game Update | WATCH | Blood Moon Rises (June 30) may add BIS hybrid bracelet -- monitor for displacement",
    "Zaryte crossbow":              "Meta Shift | WATCH | Necklace of Rupture buffs range setups June 30 -- crossbow demand proxy for range meta",
    "Masori body (f)":              "Meta Shift | WATCH | Range meta improving with Rupture necklace -- BIS armour demand may rise",
    # ---- WATCH: Summer Sweep-Up ongoing reactions ----
    "Ancestral robe top":           "Game Update | WATCH | Ancient scepters buffed 5->10% magic damage -- mage DPS ecosystem lift",
    "Ancestral robe bottom":        "Game Update | WATCH | Tied to ancestral top -- moves in tandem with mage DPS discussions",
    "Virtus robe top":              "Meta Shift | WATCH | DT2 mage hybrid; benefits from scepter buff and shadow ecosystem strength",
    "Virtus robe bottom":           "Meta Shift | WATCH | Tied to Virtus top demand",
    "Venator ring":                 "Game Update | WATCH | Venator bow consistency fix in Sweep-Up -- ring demand proxy for range meta",
    "Torva full helm":              "Meta Shift | WATCH | Completes Torva set; melee hype accelerating with Soulreaper buff",
    "Justiciar faceguard":          "Meta Shift | WATCH | Tank meta indicator; set bonus removal may depress full-set demand",
    # ---- WATCH: Supply / prestige plays ----
    "Elysian spirit shield":        "Supply Shock | WATCH | Fixed supply store-of-value; Blood Moon Rises hype lifting high-ticket market",
    "Enhanced crystal weapon seed": "Supply Shock | WATCH | CG supply may increase after Sweep-Up changes -- Bowfa ecosystem watch",
    # ---- WATCH: Raids 4 ecosystem ----
    "Avernic defender hilt":        "Raids Prep | WATCH | ToB participation rising as players gear for Raids 4 -- Avernic demand proxy",
    "Dexterous prayer scroll":      "Raids Prep | WATCH | CoX participation increasing with Raids 4 prep -- Rigour scroll demand proxy",
    "Bellator ring":                "Raids Prep | WATCH | DT2 melee ring -- accumulation proxy for Raids 4 melee prep",
    "Ultor ring":                   "Raids Prep | WATCH | Strength ring -- follows melee meta; Soulreaper buff and Raids 4 hype",
    "Magus ring":                   "Raids Prep | WATCH | Mage ring -- tied to Shadow demand and ancestral scepter ecosystem",
    "Zaryte vambraces":             "Meta Shift | WATCH | Endgame range gloves BIS; Nex activity proxy",
    # ---- WATCH: Boss demand ----
    "Inquisitor's mace":            "Boss Demand | WATCH | Crush BIS standalone -- buffed in Sweep-Up; Nightmare/Phosani activity proxy",
    "Dragon claws":                 "PvP Meta | WATCH | Spec weapon -- rises sharply on PvP tournament or wilderness meta announcements",
    "Volatile orb":                 "Community Hype | WATCH | CoX spec orb; spikes on streamer content and CoX meta discussion",
    "Dragon hunter lance":          "Boss Demand | WATCH | Vorkath/KBD BIS melee -- spikes on boss rework or slayer task weight changes",
    "Dragon hunter crossbow":       "Boss Demand | WATCH | Vorkath BIS range -- moves with lance; sensitive to Vorkath task changes",
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

    # Watchlist: item list and order are STATIC -- defined solely by WATCHLIST_NAMES.
    # Live price/trend data refreshes each cycle, but items never added/removed/reordered automatically.
    _wl_order = {name.lower(): i for i, name in enumerate(WATCHLIST_NAMES)}
    watch_raw = [all_by_name[n.lower()] for n in WATCHLIST_NAMES if n.lower() in all_by_name]
    watch     = enrich_with_trends(watch_raw)
    for w in watch:
        w["category"]       = WATCHLIST_CATEGORY.get(w["name"], "")
        w["signal_context"] = WATCHLIST_CATALYSTS.get(w["name"], "")
        w["catalyst"]       = WATCHLIST_CATALYSTS.get(w["name"], "")
    # Preserve manual order -- NO dynamic sort
    watch = sorted(watch, key=lambda r: _wl_order.get(r.get("name", "").lower(), 999))

    # Signals: preserve the order defined in SIGNALS_UNIVERSE (manually curated).
    # Live price/trend data refreshes but the item list and order never change dynamically.
    _sig_order = {name.lower(): i for i, name in enumerate(SIGNALS_UNIVERSE.keys())}
    signals_raw = [all_by_name[n.lower()] for n in SIGNALS_UNIVERSE if n.lower() in all_by_name]
    signals     = enrich_with_trends(signals_raw)
    for s in signals:
        s["signal_context"] = SIGNALS_UNIVERSE.get(s["name"], "")
    signals = sorted(signals, key=lambda r: _sig_order.get(r.get("name", "").lower(), 999))

    return bulk, singular, high_roi, watch, signals, rows