import requests

BASE = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {"User-Agent": "OsrsFlipDashboard/Owen"}
TAX_RATE = 0.02
TAX_CAP = 5_000_000

# Watchlist -- comprehensive 5M+ bossing/raids drops and endgame gear
WATCHLIST = [
# ======================================================================
# RAID UNIQUES
# ======================================================================

# -- Chambers of Xeric --
("Twisted bow", "Chambers of Xeric", "Ranged BiS -- rarest CoX unique; permanently scarce supply"),
("Kodai wand", "Chambers of Xeric", "Mage BiS autocast -- steady demand from mage PvMers"),
("Elder maul", "Chambers of Xeric", "Crush BiS -- ToA drives additional demand"),
("Ancestral robe top", "Chambers of Xeric", "Mage BiS armour -- reactive to mage update announcements"),
("Ancestral robe bottom", "Chambers of Xeric", "Mage BiS armour -- tied to top demand"),
("Ancestral hat", "Chambers of Xeric", "Mage BiS helm -- completes ancestral set"),
("Dragon claws", "Chambers of Xeric", "Spec weapon -- high PvP + PvM demand; volatile"),
("Dexterous prayer scroll", "Chambers of Xeric", "Rigour unlock -- CoX participation proxy"),
("Arcane prayer scroll", "Chambers of Xeric", "Augury unlock -- tied to Rigour demand"),
("Harmonised orb", "Chambers of Xeric", "Mage BiS for NM/PvM -- CoX changes shift supply"),
("Volatile orb", "Chambers of Xeric", "High-value spec weapon orb -- spec meta proxy"),
("Eldritch orb", "Chambers of Xeric", "Prayer restore spec orb -- niche but stable demand"),
("Olmlet", "Chambers of Xeric", "CoX pet -- collector value; tracks CoX activity"),

# -- Theatre of Blood --
("Scythe of vitur", "Theatre of Blood", "Melee BiS for slayer/raids -- essential endgame weapon"),
("Ghrazi rapier", "Theatre of Blood", "Stab BiS -- Summer Sweep-Up +4 str buff live now"),
("Sanguinesti staff (uncharged)", "Theatre of Blood", "Mage BiS -- Summer Sweep-Up 6% DPS buff + cheaper charges"),
("Avernic defender hilt", "Theatre of Blood", "Defender upgrade -- tied to ToB/raids participation"),
("Justiciar faceguard", "Theatre of Blood", "Tank helm -- set bonus removed in Sweep-Up; demand softening"),
("Justiciar chestguard", "Theatre of Blood", "Tank body -- set bonus removal reduces full-set value"),
("Justiciar legguards", "Theatre of Blood", "Tank legs -- same set bonus removal impact"),
("Scythe of vitur ornament kit", "Theatre of Blood", "HM cosmetic kit -- ToB Hard Mode prestige"),
("Sanguinesti staff ornament kit", "Theatre of Blood", "HM cosmetic kit -- ToB Hard Mode prestige"),
("Sanguine scythe of vitur", "Theatre of Blood", "HM cosmetic -- rare ToB Hard Mode prestige item"),
("Lil' Zik", "Theatre of Blood", "ToB pet -- collector value; tracks ToB activity"),

# -- Tombs of Amascut --
("Tumeken's shadow", "Tombs of Amascut", "Mage BiS -- Raids 4 prep meta; confirmed must-have"),
("Osmumten's fang", "Tombs of Amascut", "Stab BiS -- consistently high ToA activity proxy"),
("Elidinis' ward (f)", "Tombs of Amascut", "Mage offhand BiS -- completes ToA mage setup"),
("Masori body (f)", "Tombs of Amascut", "Range BiS armour -- benefits from Necklace of Rupture range meta"),
("Masori chaps (f)", "Tombs of Amascut", "Range BiS legs -- paired with body demand"),
("Masori mask (f)", "Tombs of Amascut", "Range BiS helm -- completes Masori set"),
("Masori body", "Tombs of Amascut", "Range armour -- upgrades to (f) with thread"),
("Masori chaps", "Tombs of Amascut", "Range legs -- upgrades to (f) with thread"),
("Masori mask", "Tombs of Amascut", "Range helm -- upgrades to (f) with thread"),
("Elidinis' ward", "Tombs of Amascut", "Mage offhand -- upgrades to (f) with arcane sigil"),
("Osmumten's fang (or)", "Tombs of Amascut", "ToA ornamental fang -- prestige variant"),
("Thread of elidinis", "Tombs of Amascut", "Masori upgrade component -- demand tied to Masori (f) crafting"),
("Tumeken's guardian", "Tombs of Amascut", "ToA pet -- collector value; tracks ToA activity"),

# -- The Nightmare / Phosani's Nightmare --
("Inquisitor's mace", "The Nightmare", "Crush BiS -- Summer Sweep-Up standalone buff; set bonus removed"),
("Inquisitor's hauberk", "The Nightmare", "Set bonus removed -- weaker with mace post-Sweep-Up; price risk"),
("Inquisitor's plateskirt", "The Nightmare", "Same as hauberk -- set synergy gone post-Sweep-Up"),
("Nightmare staff", "The Nightmare", "Mage staff -- base for Harmonised/Volatile/Eldritch orbs"),
("Eldritch nightmare staff", "The Nightmare", "Prayer restore spec -- assembled from staff + Eldritch orb"),
("Volatile nightmare staff", "The Nightmare", "Mage spec weapon -- assembled from staff + Volatile orb"),
("Harmonised nightmare staff", "The Nightmare", "Mage BiS assembled staff -- staff + Harmonised orb"),
("Little nightmare", "The Nightmare", "Nightmare pet -- collector value"),

# -- Corrupted Gauntlet --
("Enhanced crystal weapon seed", "Corrupted Gauntlet", "Bowfa component -- universal early endgame range weapon"),
("Crystal armour seed", "Corrupted Gauntlet", "CG armour seed -- Raids 4 prep drives CG participation"),
("Youngllef", "Corrupted Gauntlet", "Gauntlet pet -- collector; tracks CG activity"),

# -- Araxxor --
("Araxyte fang", "Araxxor", "Noxious halberd component -- BiS halberd for multi-target PvM"),
("Noxious halberd", "Araxxor", "Assembled BiS halberd -- crush+slash hybrid; high endgame demand"),

# -- Hueycoatl (Varlamore) --
("Dragon hunter wand", "Hueycoatl", "BiS mage weapon vs dragons/wyverns -- major Varlamore unique"),

# -- Amoxliatl (Varlamore) --
("Pendant of ates", "Amoxliatl", "Unique neck piece from Amoxliatl -- frozen lake boss Varlamore Pt 2"),

# ======================================================================
# BOSS UNIQUES
# ======================================================================

# -- Nex --
("Torva platebody", "Nex", "Melee BiS body -- Soulreaper axe buff increases melee activity"),
("Torva platelegs", "Nex", "Melee BiS legs -- melee hype proxy"),
("Torva full helm", "Nex", "Completes Torva set -- melee demand proxy"),
("Zaryte crossbow", "Nex", "Range BiS alt -- benefits from Necklace of Rupture range meta"),
("Zaryte vambraces", "Nex", "Endgame range gloves BiS -- Nex activity proxy"),
("Nihil horn", "Nex", "Zaryte crossbow component -- demand tied to ZCB"),
("Ancient hilt", "Nex", "Ancient godsword hilt -- niche PvP/flex item"),

# -- Desert Treasure II --
("Soulreaper axe", "Vardorvis", "Melee BiS -- Summer Sweep-Up major rework; biggest melee buff in years"),
("Virtus robe top", "Duke Sucellus", "DT2 mage hybrid -- scepter DPS buffs boost mage ecosystem"),
("Virtus robe bottom", "Duke Sucellus", "DT2 mage hybrid -- tied to Virtus top demand"),
("Bellator ring", "The Whisperer", "Melee ring -- Soulreaper buff raises melee demand proxy"),
("Venator ring", "The Leviathan", "Range ring -- bow consistency fix in Sweep-Up aids range meta"),
("Magus ring", "Duke Sucellus", "Mage ring -- tied to Shadow + ancestral scepter buff ecosystem"),
("Ultor ring", "Vardorvis", "Strength ring -- melee proxy; Soulreaper hype driver"),
("Awakener's orb", "Vardorvis", "Awakened boss unlock -- needed for all 4 DT2 awakened variants"),
("Blood quartz", "Vardorvis", "Ring upgrade component -- used with Ultor ring"),
("Smoke quartz", "Duke Sucellus", "Ring upgrade component -- used with Magus ring"),
("Ice quartz", "The Leviathan", "Ring upgrade component -- used with Venator ring"),
("Shadow quartz", "The Whisperer", "Ring upgrade component -- used with Bellator ring"),

# -- God Wars Dungeon --
("Bandos chestplate", "General Graardor", "Melee BiS body at mid-tier -- returning-player demand proxy"),
("Bandos tassets", "General Graardor", "Melee BiS legs -- pairs with chestplate demand"),
("Bandos boots", "General Graardor", "Melee BiS boots -- steady demand from melee builds"),
("Bandos godsword", "General Graardor", "Spec weapon -- 10% defence drain; PvP + PvM demand"),
("Armadyl chestplate", "Kree'arra", "Range mid-tier body -- solid baseline demand"),
("Armadyl chainskirt", "Kree'arra", "Range mid-tier legs -- pairs with chestplate"),
("Armadyl helmet", "Kree'arra", "Range mid-tier helm -- completes Armadyl set"),
("Armadyl godsword", "Kree'arra", "Spec weapon -- 25% spec; PvP staple"),
("Saradomin godsword", "Commander Zilyana", "SGS spec -- prayer restore; PvP utility + BiS for some styles"),
("Saradomin sword", "Commander Zilyana", "Mid-tier melee weapon -- stable mid-game demand"),
("Zamorak godsword", "K'ril Tsutsaroth", "ZGS spec -- massive str boost; PvP niche"),
("Steam battlestaff", "K'ril Tsutsaroth", "Mage staff -- steady mid-tier mage demand"),
("Staff of the dead", "K'ril Tsutsaroth", "Mage staff -- damage reduction spec; enduring demand"),
("Zamorakian spear", "K'ril Tsutsaroth", "Stab weapon -- Corp Beast secondary weapon; niche stable demand"),

# -- Zulrah --
("Tanzanite fang", "Zulrah", "Toxic blowpipe component -- universal early-mid BiS range weapon"),
("Magic fang", "Zulrah", "Toxic staff upgrade -- budget mage weapon"),
("Serpentine visage", "Zulrah", "Serpentine helm component -- slayer/venom utility"),
("Tanzanite mutagen", "Zulrah", "Blowpipe cosmetic swap -- rare prestige item"),
("Magma mutagen", "Zulrah", "Helm cosmetic swap -- rare prestige item"),
("Jar of swamp", "Zulrah", "Zulrah cosmetic -- collector item"),
("Snakeling", "Zulrah", "Zulrah pet -- collector value"),

# -- Vorkath --
("Dragonbone necklace", "Vorkath", "Prayer necklace -- niche prayer-heavy build demand"),
("Skeletal visage", "Vorkath", "Dragonfire ward component -- anti-dragon shield upgrade"),
("Vorkath's head", "Vorkath", "Assembles Assembler -- needed for Ava's assembler; high demand"),
("Jar of decay", "Vorkath", "Vorkath cosmetic -- collector item"),
("Vorki", "Vorkath", "Vorkath pet -- collector value"),

# -- Cerberus --
("Primordial crystal", "Cerberus", "Primordial boots component -- BiS melee boots; 1/512 drop"),
("Eternal crystal", "Cerberus", "Eternal boots component -- BiS mage boots; 1/512 drop"),
("Pegasian crystal", "Cerberus", "Pegasian boots component -- BiS range boots; 1/512 drop"),
("Smouldering stone", "Cerberus", "Dragon axe/pickaxe infernal upgrade -- skilling BiS component"),
("Hellpuppy", "Cerberus", "Cerberus pet -- collector value"),

# -- Kalphite Queen --
("Dragon chainbody", "Kalphite Queen", "Mid-tier melee body -- steady baseline demand"),
("Kalphite princess", "Kalphite Queen", "KQ pet -- collector value"),
("Jar of sand", "Kalphite Queen", "KQ cosmetic -- collector item"),

# -- King Black Dragon --
("Draconic visage", "King Black Dragon", "Dragonfire shield component -- consistent mid-game demand"),
("Prince black dragon", "King Black Dragon", "KBD pet -- collector value"),
("Jar of dirt", "King Black Dragon", "KBD cosmetic -- collector item"),

# -- Dagannoth Kings --
("Berserker ring", "Dagannoth Rex", "Melee ring -- imbue at NMZ; consistent demand"),
("Archers ring", "Dagannoth Rex", "Range ring -- imbue at NMZ; steady mid-tier"),
("Seers ring", "Dagannoth Rex", "Mage ring -- imbue at NMZ; mid-tier mage demand"),
("Warrior ring", "Dagannoth Rex", "Slash ring -- imbue at NMZ; niche demand"),
("Berserker ring (i)", "Dagannoth Rex", "Imbued melee ring -- NMZ imbued version"),
("Archers ring (i)", "Dagannoth Rex", "Imbued range ring -- NMZ imbued version"),
("Dragon axe", "Dagannoth Prime", "BiS woodcutting axe -- consistent skilling upgrade demand"),
("Mud battlestaff", "Dagannoth Prime", "Water+earth combined staff -- mid-tier mage utility"),
("Seercull", "Dagannoth Supreme", "Ranged weapon -- niche but tracked"),

# -- Abyssal Sire --
("Abyssal dagger", "Abyssal Sire", "Spec dagger -- whip complement; stable slayer demand"),
("Abyssal bludgeon", "Abyssal Sire", "Crush weapon -- slayer/DPS option"),
("Abyssal orphan", "Abyssal Sire", "Sire pet -- collector value"),

# -- Kraken --
("Trident of the seas (full)", "Kraken", "Mage weapon -- reliable mid-game mage DPS staple"),
("Kraken tentacle", "Kraken", "Abyssal whip upgrade -- consistent demand from slayer progression"),
("Pet kraken", "Kraken", "Kraken pet -- collector value"),

# -- Thermonuclear Smoke Devil --
("Occult necklace", "Thermonuclear Smoke Devil", "Mage BiS neck -- permanent high demand from mage players"),
("Smoke battlestaff", "Thermonuclear Smoke Devil", "Staff -- niche water/smoke spell demand"),
("Pet smoke devil", "Thermonuclear Smoke Devil", "Thermy pet -- collector value"),

# -- Grotesque Guardians --
("Black tourmaline core", "Grotesque Guardians", "Granite gloves/ring upgrade component -- niche slayer demand"),
("Granite gloves", "Grotesque Guardians", "Melee gloves -- consistent slayer reward demand"),
("Granite ring", "Grotesque Guardians", "Defence ring -- niche tanking use"),
("Granite hammer", "Grotesque Guardians", "Crush weapon -- consistent mid-level demand"),
("Jar of stone", "Grotesque Guardians", "GG cosmetic -- collector item"),
("Noon", "Grotesque Guardians", "Grotesque Guardians pet -- collector value"),

# -- Alchemical Hydra --
("Hydra's claw", "Alchemical Hydra", "Dragon hunter lance component -- BiS Vorkath/KBD melee weapon"),
("Hydra leather", "Alchemical Hydra", "Ferocious gloves component -- melee BiS gloves"),
("Brimstone ring", "Alchemical Hydra", "Hybrid combat ring -- consistent PvM demand"),
("Hydra's eye", "Alchemical Hydra", "Brimstone ring component -- tracked for ring crafting"),
("Hydra's fang", "Alchemical Hydra", "Brimstone ring component -- tracked for ring crafting"),
("Hydra's heart", "Alchemical Hydra", "Brimstone ring component -- tracked for ring crafting"),
("Jar of chemicals", "Alchemical Hydra", "Hydra cosmetic -- collector item"),
("Ikkle hydra", "Alchemical Hydra", "Hydra pet -- collector value"),

# -- Basilisk Knight --
("Basilisk jaw", "Basilisk Knight", "Neitiznot faceguard component -- mid-tier melee helm upgrade"),
("Neitiznot faceguard", "Basilisk Knight", "Mid-tier melee BiS helm -- consistent demand from slayer/mid-game"),

# -- Phantom Muspah --
("Venator shard", "Phantom Muspah", "Venator bow component -- range BiS bow (4 shards needed)"),
("Frozen cache", "Phantom Muspah", "Unlock cache -- contains ancient sceptre upgrades"),
("Charged ice", "Phantom Muspah", "Ancient freeze spell enhancement component"),
("Muphin", "Phantom Muspah", "Phantom Muspah pet -- collector value"),

# -- Royal Titans --
("Sunfire fanatic helm", "Royal Titans", "Royal Titans melee helm -- new 2025 content; tracks Titans activity"),
("Sunfire fanatic cuirass", "Royal Titans", "Royal Titans melee body -- strong mid/high tier armour"),
("Sunfire fanatic chausses", "Royal Titans", "Royal Titans melee legs -- completes Sunfire set"),
("Sunfire fanatic gauntlets", "Royal Titans", "Royal Titans melee gloves -- set completion piece"),
("Sunfire fanatic boots", "Royal Titans", "Royal Titans melee boots -- set completion piece"),
("Eldric's staff", "Royal Titans", "Royal Titans mage staff -- new 2025 unique; tracks Titans activity"),
("Branda's axe", "Royal Titans", "Royal Titans melee axe -- new 2025 unique"),
("Royal necklace", "Royal Titans", "Royal Titans necklace -- prayer/combat hybrid utility"),
("Smol heredit", "Royal Titans", "Royal Titans pet -- collector value"),

# -- Doom of Mokhaiotl (Doom's Delve) --
("Eclipse atlatl", "Doom of Mokhaiotl", "Ranged weapon from Doom -- Varlamore Pt 3 endgame content"),
("Sunset saber", "Doom of Mokhaiotl", "Melee weapon from Doom -- new Varlamore endgame content"),
("Sunfire splinter", "Doom of Mokhaiotl", "Upgrade component for Sunfire spells -- tracks Doom activity"),

# -- Moons of Peril --
("Blood moon helm", "Blood Moon", "Mid-tier melee helm -- Varlamore activity proxy"),
("Blood moon chestplate", "Blood Moon", "Mid-tier melee body -- tied to helm demand"),
("Blood moon tassets", "Blood Moon", "Mid-tier melee legs -- completes Blood Moon set"),
("Blue moon spear", "Blue Moon", "Mid-tier stab weapon -- Varlamore activity proxy"),
("Blue moon helm", "Blue Moon", "Mid-tier helm -- hybrid combat use"),
("Blue moon chestplate", "Blue Moon", "Mid-tier body -- hybrid combat use"),
("Blue moon tassets", "Blue Moon", "Mid-tier legs -- completes Blue Moon set"),
("Eclipse moon helm", "Eclipse Moon", "Mid-tier helm -- Eclipse Moon activity proxy"),
("Eclipse moon chestplate", "Eclipse Moon", "Mid-tier body -- Varlamore completionist demand"),
("Eclipse moon tassets", "Eclipse Moon", "Mid-tier legs -- completes Eclipse Moon set"),

# -- Corporeal Beast --
("Elysian spirit shield", "Corporeal Beast", "Prestige tank shield -- fixed supply store-of-value"),
("Arcane spirit shield", "Corporeal Beast", "Mage spirit shield -- steady collector demand"),
("Spectral spirit shield", "Corporeal Beast", "Prayer/mage def shield -- niche but tracked"),
("Elysian sigil", "Corporeal Beast", "Elysian spirit shield component -- tracks Corp Beast activity"),
("Arcane sigil", "Corporeal Beast", "Arcane spirit shield component -- tracks Corp Beast activity"),
("Spectral sigil", "Corporeal Beast", "Spectral spirit shield component -- tracks Corp Beast activity"),
("Holy elixir", "Corporeal Beast", "Spirit shield blessing component -- consistent demand for shield builds"),
("Spirit shield", "Corporeal Beast", "Base shield -- component for all spirit shields"),

# -- Sarachnis --
("Sarachnis cudgel", "Sarachnis", "Crush weapon -- cheap melee DPS; consistent slayer demand"),
("Sraracha", "Sarachnis", "Sarachnis pet -- collector value"),

# -- Skotizo --
("Skotos", "Skotizo", "Skotizo pet -- dark totem grinds proxy"),
("Totem of the fang (top)", "Skotizo", "Dark totem component -- consistent demand from Catacombs grind"),

# -- Abyssal demons (Slayer) --
("Abyssal whip", "Abyssal Demon", "Mid-tier melee BiS -- most popular first slayer weapon"),

# -- Wilderness Bosses --
("Odium ward", "Chaos Elemental", "Range offhand -- consistent PvP demand"),
("Malediction ward", "Chaos Elemental", "Mage offhand -- PvP + PvM niche"),
("Dragon 2h sword", "Chaos Elemental", "Dragon 2h -- PvP/PvM crush; steady wilderness boss drop"),
("Thammaron's sceptre", "Calvar'ion", "Wilderness mage sceptre -- Calvar'ion activity proxy"),
("Viggora's chainmace", "Calvar'ion", "Wilderness crush weapon -- Calvar'ion activity proxy"),
("Craw's bow", "Calvar'ion", "Wilderness range weapon -- high value in revenant caves context"),
("Ursine chainmace", "Calvar'ion", "Upgraded Viggora mace -- tracks Calvar'ion upgrade activity"),
("Webweaver bow", "Calvar'ion", "Upgraded Craw's bow -- range BiS in wilderness"),
("Accursed sceptre", "Calvar'ion", "Upgraded Thammaron sceptre -- mage BiS in wilderness"),
("Venomous fangs", "Scorpia", "Scorpia unique -- niche demand"),
("Odium shard 1", "Scorpia", "Odium ward component -- consistent demand from PvP builds"),
("Malediction shard 1", "Scorpia", "Malediction ward component -- consistent demand"),
("Dragon pickaxe", "Chaos Elemental", "BiS pickaxe -- consistent skilling/PvM demand from wilderness boss"),

# -- Araxxor --
("Araxyte fang", "Araxxor", "Noxious halberd component -- ~22M; tracks Araxxor activity"),
("Noxious halberd", "Araxxor", "Assembled halberd BiS -- ~48M; Araxxor signature drop"),
("Araxyte pheromone", "Araxxor", "Forces enrage mechanic -- consumable; tracks Araxxor grind"),
("Araxyte pet", "Araxxor", "Araxxor pet -- collector value"),

# -- Hueycoatl --
("Dragon hunter wand", "Hueycoatl", "BiS mage vs dragons/wyverns -- ~25M+; new Varlamore endgame boss"),
("Hueycoatl hide", "Hueycoatl", "Crafting component from Hueycoatl -- tracks boss activity"),

# -- Amoxliatl --
("Pendant of ates", "Amoxliatl", "Unique neck piece from Frozen Lake boss -- ~500K+"),

# -- Twinflame staff (Royal Titans) --
("Twinflame staff", "Royal Titans", "Assembled BiS mage staff from Royal Titans -- two halves combine"),

# -- Lightbearer (ToA missing from watchlist) --
("Lightbearer", "Tombs of Amascut", "Ring from ToA -- spec restore; consistent demand"),

# -- Dragon hunter lance (Hydra assembled) --
("Dragon hunter lance", "Alchemical Hydra", "BiS melee for Vorkath/KBD -- assembled from Hydra claw + DHL; ~40M"),

# -- Dragon hunter buckler (Fortis Colosseum) --
("Dragon hunter buckler", "Fortis Colosseum", "Fortis Colosseum unique offhand -- dragon/wyvern bonus"),
("Echo crystal", "Fortis Colosseum", "Fortis Colosseum upgrade component -- tracks Colosseum activity"),
("Sunfire fanatic helm", "Fortis Colosseum", "Colosseum melee helm -- part of sunfire fanatic set"),
("Sunfire fanatic cuirass", "Fortis Colosseum", "Colosseum melee body -- BiS melee chest for some content"),
("Sunfire fanatic chausses", "Fortis Colosseum", "Colosseum melee legs -- completes sunfire set"),

# -- Venator bow (Phantom Muspah assembled) --
("Venator bow", "Phantom Muspah", "Assembled from 4x Venator shard -- range BiS bow ~350M"),

# -- Neitiznot faceguard (Basilisk Knight assembled) --
("Neitiznot faceguard", "Basilisk Knight", "Assembled melee helm -- mid-tier BiS; ~6M; requires basilisk jaw"),

# -- Toxic blowpipe (Zulrah assembled) --
("Toxic blowpipe (empty)", "Zulrah", "Assembled from Tanzanite fang -- universal range weapon; ~1.5M"),

# -- Armadyl crossbow (GWD Zilyana) --
("Armadyl crossbow", "Commander Zilyana", "Ranged weapon from Zilyana -- uses armadyl bolts; consistent demand"),

# -- GWD hilts --
("Zamorak hilt", "K'ril Tsutsaroth", "ZGS component -- tracks K'ril activity"),
("Saradomin hilt", "Commander Zilyana", "SGS component -- tracks Zilyana activity"),
("Armadyl hilt", "Kree'arra", "AGS component -- tracks Kree'arra activity"),
("Bandos hilt", "General Graardor", "BGS component -- tracks Graardor activity"),

# -- Abyssal Demon slayer drop --
("Abyssal head", "Abyssal Demon", "Mounted head -- collector/skiller demand"),

# -- Corporeal Beast sigils (already have shields, add standalone sigils) --
("Holy elixir", "Corporeal Beast", "Spirit shield blessing -- consistent demand for shield builds"),

# -- Doom of Mokhaiotl full drops --
("Confliction gauntlets", "Doom of Mokhaiotl", "Melee gloves from Doom delve -- endgame Varlamore content"),
("Avernic treads", "Doom of Mokhaiotl", "Melee boots from Doom delve -- Varlamore endgame"),
("Eye of ayak (uncharged)", "Doom of Mokhaiotl", "Powered staff component from Doom -- BiS mage weapon element"),
("Earthbound tecpatl", "Doom of Mokhaiotl", "Melee weapon from Doom delve -- tracks Varlamore boss activity"),

# -- Barrows --
("Karil's crossbow", "Barrows", "Barrows range weapon -- consistent Barrows grind value"),
("Ahrim's robetop", "Barrows", "Barrows mage body -- consistent mid-game mage demand"),
("Ahrim's robeskirt", "Barrows", "Barrows mage legs -- pairs with robetop"),
("Torag's platebody", "Barrows", "Barrows melee body -- mid-tier tank demand"),
("Dharok's greataxe", "Barrows", "NMZ/PvM spec weapon -- most popular Barrows weapon for combat builds"),
("Guthan's warspear", "Barrows", "Self-heal set -- AFK slayer staple"),
("Verac's flail", "Barrows", "Prayer-ignoring weapon -- PvP + slayer niche"),
("Ahrim's staff", "Barrows", "Barrows mage weapon -- complete Ahrim set piece"),
("Dharok's helm", "Barrows", "Barrows NMZ helm -- Dharok set completion"),
("Karil's leathertop", "Barrows", "Barrows range body -- set completion piece"),
("Karil's leatherskirt", "Barrows", "Barrows range legs -- set completion piece"),

# -- Giant Mole --
("Mole skin", "Giant Mole", "Baby mole pet component + crafting -- consistent minor demand"),

# -- Wintertodt --
("Phoenix", "Wintertodt", "Wintertodt skilling pet -- collector value"),
("Burnt page", "Wintertodt", "Tome of fire charge -- consistently demanded by fire-spell mages"),

# -- Tempoross --
("Spirit angler's top", "Tempoross", "Angler outfit piece -- fishing pet grind proxy"),
("Tackle box", "Tempoross", "Fishing upgrade storage -- skilling item"),

# -- Zalcano --
("Crystal tool seed", "Zalcano", "Crystal tool upgrade seed -- skilling BiS axe/pickaxe/harpoon component"),
("Smolcano", "Zalcano", "Zalcano pet -- collector value"),

# -- Gauntlet (Regular) --
("Crystal weapon seed", "The Gauntlet", "Crystal weapon/armour seed -- mid-tier upgrade component"),
("Crystal armour seed", "Corrupted Gauntlet", "CG armour seed -- Raids 4 prep drives CG participation"),

# -- Nightmare Zone --
("Imbued heart", "Nightmare Zone", "Magic boost item -- consistent mage demand; 1M+ NMZ points"),

# -- Slayer (General) --
("Trident of the swamp (uncharged)", "Cave Kraken", "Mage BiS trident -- consistent high demand from mage slayers"),

# ======================================================================
# CLUE UNIQUES (500K+ threshold)
# ======================================================================

# 3rd Age (hard/elite/master)
("3rd age platebody", "Treasure Trails", "Ultra-rare hard/elite clue -- store-of-value; ~1/42K rate"),
("3rd age platelegs", "Treasure Trails", "Ultra-rare hard clue -- pairs with platebody"),
("3rd age full helmet", "Treasure Trails", "Ultra-rare hard clue -- completes 3rd age melee set"),
("3rd age kiteshield", "Treasure Trails", "Ultra-rare hard clue -- 3rd age melee shield"),
("3rd age longsword", "Treasure Trails", "Rare hard clue -- speculative; very low supply"),
("3rd age bow", "Treasure Trails", "Ultra-rare elite/master clue -- range prestige item"),
("3rd age wand", "Treasure Trails", "Ultra-rare elite clue -- mage prestige item"),
("3rd age robe top", "Treasure Trails", "Ultra-rare elite clue -- mage 3rd age body"),
("3rd age robe", "Treasure Trails", "Ultra-rare elite clue -- mage 3rd age legs"),
("3rd age mage hat", "Treasure Trails", "Ultra-rare elite clue -- mage 3rd age helm"),
("3rd age range top", "Treasure Trails", "Ultra-rare elite clue -- range 3rd age body"),
("3rd age range legs", "Treasure Trails", "Ultra-rare elite clue -- range 3rd age legs"),
("3rd age range coif", "Treasure Trails", "Ultra-rare elite clue -- range 3rd age helm"),
("3rd age cloak", "Treasure Trails", "Rare master clue -- complement to 3rd age sets"),
("3rd age vambraces", "Treasure Trails", "Rare hard/elite clue -- range gloves prestige"),
("3rd age amulet", "Treasure Trails", "Ultra-rare master clue -- prestige neck"),
("3rd age druidic robe top", "Treasure Trails", "Ultra-rare master clue -- rarest 3rd age prayer set piece"),
("3rd age druidic robe bottoms", "Treasure Trails", "Ultra-rare master clue -- 3rd age prayer set"),
("3rd age druidic staff", "Treasure Trails", "Ultra-rare master clue -- prayer staff prestige"),
("3rd age druidic cloak", "Treasure Trails", "Ultra-rare master clue -- prayer cloak prestige"),
("3rd age axe", "Treasure Trails", "Ultra-rare master clue -- skilling prestige item"),
("3rd age pickaxe", "Treasure Trails", "Ultra-rare master clue -- skilling prestige item"),

# Gilded items (hard/elite/master)
("Gilded platebody", "Treasure Trails", "Elite/master clue -- prestige melee body"),
("Gilded platelegs", "Treasure Trails", "Elite/master clue -- gilded melee legs"),
("Gilded plateskirt", "Treasure Trails", "Elite/master clue -- gilded melee skirt"),
("Gilded full helm", "Treasure Trails", "Elite/master clue -- gilded melee helm"),
("Gilded kiteshield", "Treasure Trails", "Elite/master clue -- gilded shield"),
("Gilded scimitar", "Treasure Trails", "Hard/elite gilded -- cosmetic melee weapon"),
("Gilded boots", "Treasure Trails", "Elite clue gilded -- fashionscape demand"),
("Gilded coif", "Treasure Trails", "Elite clue gilded -- range cosmetic"),
("Gilded d'hide vambs", "Treasure Trails", "Elite clue gilded -- range gloves cosmetic"),
("Gilded d'hide body", "Treasure Trails", "Elite clue gilded -- range body cosmetic"),
("Gilded d'hide chaps", "Treasure Trails", "Elite clue gilded -- range legs cosmetic"),
("Gilded spade", "Treasure Trails", "Master clue -- rare clue cosmetic tool"),

# Ranger set (medium/hard/elite)
("Ranger boots", "Treasure Trails", "Medium clue BiS range boots -- high demand relative to rate"),
("Ranger gloves", "Treasure Trails", "Hard clue -- BiS range gloves for certain setups"),
("Robin hood hat", "Treasure Trails", "Hard clue range helm -- consistently desired cosmetic"),
("Ranger hat", "Treasure Trails", "Elite clue range cosmetic -- part of ranger set"),
("Ranger top", "Treasure Trails", "Elite clue -- full ranger set body piece"),
("Ranger tights", "Treasure Trails", "Elite clue -- ranger set legs"),

# Blessed d'hide sets (all gods, hard clue)
("Saradomin d'hide body", "Treasure Trails", "Blessed d'hide body -- Saradomin cosmetic; consistent hard clue demand"),
("Armadyl d'hide body", "Treasure Trails", "Blessed d'hide body -- Armadyl cosmetic variant"),
("Zamorak d'hide body", "Treasure Trails", "Blessed d'hide body -- Zamorak cosmetic"),
("Ancient d'hide body", "Treasure Trails", "Blessed d'hide body -- Ancient cosmetic"),
("Bandos d'hide body", "Treasure Trails", "Blessed d'hide body -- Bandos cosmetic"),
("Guthix d'hide body", "Treasure Trails", "Blessed d'hide body -- Guthix cosmetic"),
("Saradomin d'hide boots", "Treasure Trails", "Blessed boots -- Saradomin cosmetic"),
("Armadyl d'hide boots", "Treasure Trails", "Blessed boots -- Armadyl cosmetic variant"),
("Zamorak d'hide boots", "Treasure Trails", "Blessed boots -- Zamorak cosmetic variant"),
("Ancient d'hide boots", "Treasure Trails", "Blessed boots -- Ancient cosmetic variant"),
("Bandos d'hide boots", "Treasure Trails", "Blessed boots -- Bandos cosmetic variant"),
("Guthix d'hide boots", "Treasure Trails", "Blessed boots -- Guthix cosmetic variant"),

# Ornament kits (elite/master)
("Torture ornament kit", "Treasure Trails", "Elite clue ornament -- amulet of torture cosmetic"),
("Occult ornament kit", "Treasure Trails", "Elite clue ornament -- occult necklace cosmetic"),
("Dragon defender ornament kit", "Treasure Trails", "Elite clue ornament -- defender cosmetic; consistent demand"),
("Berserker necklace ornament kit", "Treasure Trails", "Elite clue ornament -- decorative upgrade; low supply"),
("Fury ornament kit", "Treasure Trails", "Elite clue ornament -- amulet of fury cosmetic"),
("Dragon platebody ornament kit", "Treasure Trails", "Master clue ornament -- dragon platebody cosmetic"),
("Dragon platelegs ornament kit", "Treasure Trails", "Master clue ornament -- dragon platelegs cosmetic"),
("Dragon full helm ornament kit", "Treasure Trails", "Master clue ornament -- dragon full helm cosmetic"),
("Dragon chainbody ornament kit", "Treasure Trails", "Master clue ornament -- dragon chain cosmetic"),
("Dragon boots ornament kit", "Treasure Trails", "Master clue ornament -- dragon boots cosmetic"),
("Dragon kiteshield ornament kit", "Treasure Trails", "Master clue ornament -- dragon kiteshield cosmetic"),
("Helm of neitiznot (f)", "Treasure Trails", "Elite clue cosmetic -- popular mid-tier helm upgrade look"),

# Notable fashionscape / cosmetic clue items
("Black cavalier", "Treasure Trails", "Hard clue cosmetic hat -- fashionscape staple"),
("Pirates' hat", "Treasure Trails", "Medium/hard clue -- popular cosmetic; consistent collector demand"),
("Musketeer tabard", "Treasure Trails", "Medium clue -- fashionscape demand"),
("Highwayman mask", "Treasure Trails", "Medium clue -- recognisable cosmetic; steady demand"),
("Holy sandals", "Treasure Trails", "Hard clue -- niche prayer/cosmetic appeal"),
("Briefcase", "Treasure Trails", "Master clue -- rare cosmetic backpack; collector item"),
("Rune scimitar ornament kit (Saradomin)", "Treasure Trails", "Hard clue ornament kit -- consistent fashionscape demand"),
("Rune scimitar ornament kit (Zamorak)", "Treasure Trails", "Hard clue ornament kit -- consistent fashionscape demand"),
("Bloodhound", "Treasure Trails", "Master clue pet -- tracks master clue activity"),
]

WATCHLIST_NAMES = [w[0] for w in WATCHLIST]
WATCHLIST_CATALYSTS = {w[0]: w[2] for w in WATCHLIST}
WATCHLIST_CATEGORY = {w[0]: w[1] for w in WATCHLIST}

# Signals Universe -- TYPE | STATUS | REASON
SIGNALS_UNIVERSE = {
# ---- ACTIVE: Blood Moon Rises (June 30) ----
"Necklace of anguish": "Game Update | ACTIVE | Necklace of Rupture (new BIS range neck) releases June 30 -- direct price displacement risk",
"Soulreaper axe": "Game Update | ACTIVE | Summer Sweep-Up rework live -- stacks to 5, 50% acc buff, 12.5% def drain per hit",
"Sanguinesti staff (uncharged)": "Game Update | ACTIVE | Summer Sweep-Up: 6% DPS buff, charge cost cut 3->2 blood runes -- demand spike",
"Ghrazi rapier": "Game Update | ACTIVE | Summer Sweep-Up: +4 strength bonus -- guaranteed extra max hit in all setups",
"Inquisitor's mace": "Game Update | ACTIVE | Sweep-Up: standalone str buffed but set bonus removed -- net weaker with full Inq",
"Inquisitor's hauberk": "Price Risk | ACTIVE | Inquisitor set bonus removed -- pieces no longer synergise; demand for full set softening",
"Inquisitor's plateskirt": "Price Risk | ACTIVE | Same as hauberk -- set synergy gone; price risk if mace-only meta forms",
# ---- ACTIVE: Raids 4 prep ----
"Twisted bow": "Raids Prep | ACTIVE | Raids 4 (Autumn 2026) -- Tbow confirmed as prep BiS; community accumulating now",
"Tumeken's shadow": "Raids Prep | ACTIVE | Raids 4 prep -- Shadow confirmed BIS mage for Fractured Archive; must-have",
"Scythe of vitur": "Raids Prep | ACTIVE | Raids 4 prep -- Scythe closest reference melee weapon; accumulation phase",
# ---- WATCH: Blood Moon Rises displacement ----
"Tormented bracelet": "Game Update | WATCH | Blood Moon Rises (June 30) may add BIS hybrid bracelet -- monitor for displacement",
"Zaryte crossbow": "Meta Shift | WATCH | Necklace of Rupture buffs range setups June 30 -- crossbow demand proxy for range meta",
"Masori body (f)": "Meta Shift | WATCH | Range meta improving with Rupture necklace -- BIS armour demand may rise",
# ---- WATCH: Summer Sweep-Up ongoing reactions ----
"Ancestral robe top": "Game Update | WATCH | Ancient scepters buffed 5->10% magic damage -- mage DPS ecosystem lift",
"Ancestral robe bottom": "Game Update | WATCH | Tied to ancestral top -- moves in tandem with mage DPS discussions",
"Virtus robe top": "Meta Shift | WATCH | DT2 mage hybrid; benefits from scepter buff and shadow ecosystem strength",
"Virtus robe bottom": "Meta Shift | WATCH | Tied to Virtus top demand",
"Venator ring": "Game Update | WATCH | Venator bow consistency fix in Sweep-Up -- ring demand proxy for range meta",
"Torva full helm": "Meta Shift | WATCH | Completes Torva set; melee hype accelerating with Soulreaper buff",
"Justiciar faceguard": "Meta Shift | WATCH | Tank meta indicator; set bonus removal may depress full-set demand",
# ---- WATCH: Supply / prestige plays ----
"Elysian spirit shield": "Supply Shock | WATCH | Fixed supply store-of-value; Blood Moon Rises hype lifting high-ticket market",
"Enhanced crystal weapon seed": "Supply Shock | WATCH | CG supply may increase after Sweep-Up changes -- Bowfa ecosystem watch",
# ---- WATCH: Raids 4 ecosystem ----
"Avernic defender hilt": "Raids Prep | WATCH | ToB participation rising as players gear for Raids 4 -- Avernic demand proxy",
"Dexterous prayer scroll": "Raids Prep | WATCH | CoX participation increasing with Raids 4 prep -- Rigour scroll demand proxy",
"Bellator ring": "Raids Prep | WATCH | DT2 melee ring -- accumulation proxy for Raids 4 melee prep",
"Ultor ring": "Raids Prep | WATCH | Strength ring -- follows melee meta; Soulreaper buff and Raids 4 hype",
"Magus ring": "Raids Prep | WATCH | Mage ring -- tied to Shadow demand and ancestral scepter ecosystem",
"Zaryte vambraces": "Meta Shift | WATCH | Endgame range gloves BIS; Nex activity proxy",
# ---- WATCH: Boss demand ----
"Dragon claws": "PvP Meta | WATCH | Spec weapon -- rises sharply on PvP tournament or wilderness meta announcements",
"Volatile orb": "Community Hype | WATCH | CoX spec orb; spikes on streamer content and CoX meta discussion",
"Dragon hunter lance": "Boss Demand | WATCH | Vorkath/KBD BIS melee -- spikes on boss rework or slayer task weight changes",
"Dragon hunter crossbow": "Boss Demand | WATCH | Vorkath BIS range -- moves with lance; sensitive to Vorkath task changes",
# ---- WATCH: Varlamore content ----
"Noxious halberd": "New Content | WATCH | Araxxor BIS halberd -- Varlamore endgame; tracks Araxxor farming activity",
"Araxyte fang": "New Content | WATCH | Noxious halberd component -- demand tied to halberd crafting",
"Dragon hunter wand": "New Content | WATCH | Hueycoatl BIS mage wand -- major unique from Varlamore dragon boss",
"Eclipse atlatl": "New Content | WATCH | Doom of Mokhaiotl ranged weapon -- Varlamore Pt 3 endgame content",
"Sunfire fanatic cuirass": "New Content | WATCH | Royal Titans BIS melee body -- tracks Titans farming activity",
}

SHIFTS_HIGH_TICKET_SEEDS = [
"Twisted bow", "Scythe of vitur", "Tumeken's shadow", "Soulreaper axe",
"Osmumten's fang", "Harmonised orb", "Volatile orb", "Eldritch orb",
"Enhanced crystal weapon seed", "Ghrazi rapier", "Sanguinesti staff (uncharged)",
"Avernic defender hilt", "Torva platebody", "Torva platelegs",
"Masori body (f)", "Masori chaps (f)", "Ancestral robe top", "Ancestral robe bottom",
"Virtus robe top", "Virtus robe bottom", "Zaryte crossbow", "Dragon hunter lance",
"Dragon hunter crossbow", "Necklace of anguish", "Torva full helm",
"Justiciar faceguard", "Elysian spirit shield", "3rd age platebody",
"Inquisitor's mace", "Zaryte vambraces", "Kodai wand", "Elder maul",
"Dragon claws", "Dexterous prayer scroll", "Arcane prayer scroll",
"Ancestral hat", "Justiciar chestguard", "Justiciar legguards",
"Elidinis' ward (f)", "Masori mask (f)",
"Inquisitor's hauberk", "Inquisitor's plateskirt", "Nightmare staff",
"Bellator ring", "Venator ring", "Magus ring", "Ultor ring",
"Armadyl chestplate", "Armadyl chainskirt", "Armadyl helmet",
"Bandos chestplate", "Bandos tassets",
"Tormented bracelet", "Arcane spirit shield",
"Noxious halberd", "Dragon hunter wand", "Eclipse atlatl",
"Sunfire fanatic cuirass",
]

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
    if ratio is None: return 0.3, "No data"
    if 0.8 <= ratio <= 1.5: return 1.0, "Ideal"
    if 1.5 < ratio <= 3.0: return 0.7, "High demand"
    if ratio > 3.0: return 0.4, "Hard to buy"
    if 0.4 <= ratio < 0.8: return 0.8, "Slight flood"
    return 0.5, "Flooded"


# -- Row builder ----------------------------------------------------------------
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


# -- Trend enrichment ----------------------------------------------------------
def enrich_with_trends(rows):
    enriched = []
    for r in rows:
        item_id = r.get("id")
        cur = r.get("sell_price") or 0
        ts_data = []
        if item_id:
            try:
                ts_data = fetch_timeseries(item_id, "24h")
            except Exception:
                ts_data = []

        def price_at(n_days_ago):
            if not ts_data or len(ts_data) < n_days_ago:
                return None
            entry = ts_data[-(n_days_ago)]
            return entry.get("avgHighPrice") or entry.get("avgLowPrice")

        p1  = price_at(1)
        p7  = price_at(7)
        p14 = price_at(14)
        p30 = price_at(30)

        def pct(old, new):
            if old and new and old > 0:
                return round((new - old) / old * 100, 2)
            return None

        chg_1d  = pct(p1,  cur)
        chg_7d  = pct(p7,  cur)
        chg_14d = pct(p14, cur)
        chg_30d = pct(p30, cur)

        # Short-term from 5m timeseries
        ts_5m = []
        if item_id:
            try:
                ts_5m = fetch_timeseries(item_id, "5m")
            except Exception:
                ts_5m = []

        def price_at_5m(n_periods):
            if not ts_5m or len(ts_5m) < n_periods:
                return None
            entry = ts_5m[-n_periods]
            return entry.get("avgHighPrice") or entry.get("avgLowPrice")

        p20m = price_at_5m(4)
        p40m = price_at_5m(8)
        p1h  = price_at_5m(12)
        p6h  = price_at_5m(72)
        p12h = price_at_5m(144)

        chg_20m = pct(p20m, cur)
        chg_40m = pct(p40m, cur)
        chg_1h  = pct(p1h,  cur)
        chg_6h  = pct(p6h,  cur)
        chg_12h = pct(p12h, cur)

        # Trend classification
        up30 = chg_30d is not None and chg_30d > 2
        up7  = chg_7d  is not None and chg_7d  > 1
        up1  = chg_1d  is not None and chg_1d  > 0.5
        dn30 = chg_30d is not None and chg_30d < -2
        dn7  = chg_7d  is not None and chg_7d  < -1
        dn1  = chg_1d  is not None and chg_1d  < -0.5

        if up30 and up7 and up1:
            trend = "Extended"
        elif up30 and up7:
            trend = "Building"
        elif up30 and dn7:
            trend = "Pullback"
        elif dn30 and dn7:
            trend = "Weakening"
        else:
            trend = "Flat"

        flags = []
        if chg_1d is not None and abs(chg_1d) >= 10:
            flags.append("Price shock")
        elif chg_1d is not None and abs(chg_1d) >= 5:
            flags.append("Big move")
        if r.get("profit_unit", 0) >= 500_000:
            flags.append("Fat margin")
        if r.get("sell_price", 0) >= 10_000_000:
            flags.append("High GP")

        enriched.append({
            **r,
            "chg_1d":  chg_1d,
            "chg_7d":  chg_7d,
            "chg_14d": chg_14d,
            "chg_30d": chg_30d,
            "chg_20m": chg_20m,
            "chg_40m": chg_40m,
            "chg_1h":  chg_1h,
            "chg_6h":  chg_6h,
            "chg_12h": chg_12h,
            "trend":   trend,
            "flags":   ", ".join(flags) if flags else "Quiet",
            "prev_price_1d":  p1,
            "prev_price_7d":  p7,
            "prev_price_14d": p14,
            "prev_price_30d": p30,
            "prev_price_1h":  p1h,
        })
    return enriched


# -- Viability filter for bulk -------------------------------------------------
def is_viable_bulk(r):
    name = r.get("name", "").lower()
    if any(x in name for x in ["(1)", "(2)", "(3)", "noted", "certificate"]):
        return False
    return True


# -- Shifts data ---------------------------------------------------------------
def build_shifts_data(all_rows, mapping):
    """
    Scan the entire GE catalogue (all_rows from build_rows).
    High-ticket: sell price >= 3M AND ge_limit <= 100 (scarce rares).
    Bulk:        ge_limit >= 500 AND total_hr >= 200 (liquid commodities).
    No seed lists -- every tradeable item in the live snapshot is eligible.
    """
    ht_rows   = enrich_with_trends([
        r for r in all_rows
        if (r.get("sell_price") or 0) >= 3_000_000
        and (r.get("ge_limit") or 0) <= 100
    ])
    bulk_rows = enrich_with_trends([
        r for r in all_rows
        if (r.get("ge_limit") or 0) >= 500
        and (r.get("total_hr") or 0) >= 200
    ])
    return ht_rows, bulk_rows


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

    # Watchlist: item list and order are STATIC
    _wl_order = {name.lower(): i for i, name in enumerate(WATCHLIST_NAMES)}
    watch_raw = [all_by_name[n.lower()] for n in WATCHLIST_NAMES if n.lower() in all_by_name]
    watch = enrich_with_trends(watch_raw)
    for w in watch:
        w["category"] = WATCHLIST_CATEGORY.get(w["name"], "")
        w["signal_context"] = WATCHLIST_CATALYSTS.get(w["name"], "")
        w["catalyst"] = WATCHLIST_CATALYSTS.get(w["name"], "")
    watch = sorted(watch, key=lambda r: _wl_order.get(r.get("name", "").lower(), 999))

    # Signals: preserve the order defined in SIGNALS_UNIVERSE
    _sig_order = {name.lower(): i for i, name in enumerate(SIGNALS_UNIVERSE.keys())}
    signals_raw = [all_by_name[n.lower()] for n in SIGNALS_UNIVERSE if n.lower() in all_by_name]
    signals = enrich_with_trends(signals_raw)
    for s in signals:
        s["signal_context"] = SIGNALS_UNIVERSE.get(s["name"], "")
    signals = sorted(signals, key=lambda r: _sig_order.get(r.get("name", "").lower(), 999))

    return bulk, singular, high_roi, watch, signals, rows