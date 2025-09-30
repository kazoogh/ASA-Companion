import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import time
import aiohttp
import os
import json
import datetime
import math

# -----------------------------
# CONFIG
# -----------------------------

TOKEN = "DISCORD_DEVELOPER_TOKEN"
SERVERLIST_URL = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
GUILD_TOKEN = "GUILD_ID"
STEAM_API_KEY = "API_KEY"
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# DASHBOARD STATE
# -----------------------------

dashboards = {}  
# { channel_id: [ { "message_id": int, "server_id": int, "server_name": str } ] }

# Track who is currently online per server
active_sessions = {}  
# { server_id: { steam64: { "joined": datetime, "name": str } } }

# -----------------------------
# DINO DATABASE
# -----------------------------

DINOSAUR_FILE = "dinosaurs.json"

def load_dinos():
    if os.path.exists(DINOSAUR_FILE):
        with open(DINOSAUR_FILE, "r") as f:
            return json.load(f)
    return {}

def save_dinos():
    with open(DINOSAUR_FILE, "w") as f:
        json.dump(dinosaurs, f, indent=2)

dinosaurs = load_dinos()
# {
#   "rex": {
#     "base_torpor": 1550,
#     "torpor_per_level": 93,
#     "food_drain": 0.1,
#     "taming_affinity_per_level": 85,
#     "base_affinity": 1200,
#     "foods": {
#       "extraordinary_kibble": {"food_value": 80, "affinity": 400},
#       "raw_mutton": {"food_value": 50, "affinity": 150}
#     },
#     "weapons": {
#       "tranq_arrow": 90,
#       "tranq_dart": 221,
#       "shocking_tranq_dart": 396
#     }
#   }
# }


# -----------------------------
# GENERATOR DATABASE
# -----------------------------

GEN_FILE = "generators.json"

def load_gens():
    if os.path.exists(GEN_FILE):
        with open(GEN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_gens():
    with open(GEN_FILE, "w") as f:
        json.dump(generators, f, indent=2)

generators = load_gens()
# { group: { number: { "fuel": int, "end_time": int } } }

# -----------------------------
# PLAYER DATABASE
# -----------------------------

PLAYER_DB = "players.json"
EXPIRY_DAYS = 14

def load_db():
    if os.path.exists(PLAYER_DB):
        with open(PLAYER_DB, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(PLAYER_DB, "w") as f:
        json.dump(db, f, indent=2)

player_db = load_db()

def prune_old_entries(player_id):
    """Remove servers not seen in the last 14 days."""
    if player_id not in player_db:
        return
    now = datetime.datetime.utcnow()
    servers = player_db[player_id]["servers"]
    expired = []
    for server, meta in servers.items():
        last_seen = datetime.datetime.fromisoformat(meta["last_seen"])
        if (now - last_seen).days > EXPIRY_DAYS:
            expired.append(server)
    for s in expired:
        del servers[s]

def record_visit(steam64, name, server_name, joined_time, left_time=None):
    now = datetime.datetime.utcnow().isoformat()
    duration = None
    if left_time:
        duration = (left_time - joined_time).total_seconds() // 60  # minutes

    if steam64 not in player_db:
        player_db[steam64] = {
            "name": name,
            "platform": "Steam",
            "eos_id": None,
            "steam_id": steam64,
            "tag": "Random",
            "comments": None,
            "servers": {}
        }

    prune_old_entries(steam64)

    servers = player_db[steam64]["servers"]
    if server_name not in servers:
        servers[server_name] = {"visits": 0, "last_seen": now, "total_minutes": 0}
    servers[server_name]["visits"] += 1
    servers[server_name]["last_seen"] = now
    if duration:
        servers[server_name]["total_minutes"] += duration

    save_db(player_db)

def get_top_servers(player_id, limit=5):
    prune_old_entries(player_id)
    servers = player_db[player_id]["servers"]
    sorted_by_visits = sorted(servers.items(), key=lambda x: x[1]["visits"], reverse=True)
    return sorted_by_visits[:limit]

def get_recent_servers(player_id, limit=5):
    prune_old_entries(player_id)
    servers = player_db[player_id]["servers"]
    sorted_by_time = sorted(servers.items(), key=lambda x: x[1]["last_seen"], reverse=True)
    return sorted_by_time[:limit]

ITEMS = {
    # -----------------------------
    # KIBBLES
    # -----------------------------

    "basic_kibble": {
        "name": "Basic Kibble",
        "ingredients": {
            "Extra Small Egg": 1,
            "Amarberry": 5,
            "Mejoberry": 5,
            "Tintoberry": 10,
            "Cooked Meat": 1,
            "Fiber": 25,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/c/c7/Basic_Kibble.png/64px-Basic_Kibble.png"
    },
    "simple_kibble": {
        "name": "Simple Kibble",
        "ingredients": {
            "Small Egg": 1,
            "Cooked Fish Meat": 1,
            "Mejoberry": 5,
            "Rockarrot": 2,
            "Fiber": 1,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/f/f8/Simple_Kibble.png/64px-Simple_Kibble.png"
    },
    "regular_kibble": {
        "name": "Regular Kibble",
        "ingredients": {
            "Medium Egg": 1,
            "Cooked Meat Jerky": 1,
            "Longrass": 2,
            "Savoroot": 2,
            "Fiber": 5,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/6/68/Regular_Kibble.png/64px-Regular_Kibble.png"
    },
    "superior_kibble": {
        "name": "Superior Kibble",
        "ingredients": {
            "Large Egg": 1,
            "Prime Meat Jerky": 1,
            "Citronal": 2,
            "Sap": 2,
            "Cooked Meat": 1,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/6/6e/Superior_Kibble.png/64px-Superior_Kibble.png"
    },
    "exceptional_kibble": {
        "name": "Exceptional Kibble",
        "ingredients": {
            "Extra Large Egg": 1,
            "Focal Chili": 1,
            "Mejoberry": 10,
            "Rare Flower": 1,
            "Rare Mushroom": 1,
            "Prime Meat Jerky": 1,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/0/0d/Exceptional_Kibble.png/64px-Exceptional_Kibble.png"
    },
    "extraordinary_kibble": {
        "name": "Extraordinary Kibble",
        "ingredients": {
            "Special Egg (Yutyrannus, etc.)": 1,
            "Giant Bee Honey": 1,
            "Mejoberry": 10,
            "Lazarus Chowder": 1,
            "Fiber": 1,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/0/0c/Extraordinary_Kibble.png/64px-Extraordinary_Kibble.png"
    },

    # -----------------------------
    # SOUPS / BREWS / STEWS
    # -----------------------------

    "medbrew": {
        "name": "Medical Brew",
        "ingredients": {
            "Tintoberry": 20,
            "Narcotic": 2,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/8/88/Medical_Brew.png/64px-Medical_Brew.png"
    },
    "energybrew": {
        "name": "Energy Brew",
        "ingredients": {
            "Azulberry": 20,
            "Stimulant": 2,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/0/0e/Energy_Brew.png/64px-Energy_Brew.png"
    },
    "calien soup": {
        "name": "Calien Soup",
        "ingredients": {
            "Citronal": 5,
            "Tintoberry": 20,
            "Azulberry": 20,
            "Mejoberry": 10,
            "Stimulant": 2,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/a/a4/Calien_Soup.png/64px-Calien_Soup.png"
    },
    "focal chili": {
        "name": "Focal Chili",
        "ingredients": {
            "Cooked Meat": 9,
            "Citronal": 5,
            "Tintoberry": 20,
            "Azulberry": 20,
            "Mejoberry": 20,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/8/8b/Focal_Chili.png/64px-Focal_Chili.png"
    },
    "lazarus chowder": {
        "name": "Lazarus Chowder",
        "ingredients": {
            "Cooked Meat": 9,
            "Savoroot": 5,
            "Longrass": 5,
            "Mejoberry": 10,
            "Narcotic": 2,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/0/01/Lazarus_Chowder.png/64px-Lazarus_Chowder.png"
    },
    "enduro stew": {
        "name": "Enduro Stew",
        "ingredients": {
            "Cooked Meat": 9,
            "Rockarrot": 5,
            "Savoroot": 5,
            "Mejoberry": 10,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/7/7f/Enduro_Stew.png/64px-Enduro_Stew.png"
    },
    "fria curry": {
        "name": "Fria Curry",
        "ingredients": {
            "Rockarrot": 5,
            "Longrass": 5,
            "Mejoberry": 20,
            "Narcotic": 2,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/4/4f/Fria_Curry.png/64px-Fria_Curry.png"
    },
    "shadow steak": {
        "name": "Shadow Steak Saute",
        "ingredients": {
            "Prime Meat Jerky": 1,
            "Rockarrot": 2,
            "Savoroot": 2,
            "Longrass": 2,
            "Mejoberry": 20,
            "Narcotic": 8,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/6/6e/Shadow_Steak_Saute.png/64px-Shadow_Steak_Saute.png"
    },
    "battle tartare": {
        "name": "Battle Tartare",
        "ingredients": {
            "Cooked Prime Meat": 3,
            "Savoroot": 2,
            "Longrass": 2,
            "Rare Flower": 1,
            "Rare Mushroom": 1,
            "Mejoberry": 20,
            "Stimulant": 8,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/1/16/Battle_Tartare.png/64px-Battle_Tartare.png"
    },
    "mindwipe": {
        "name": "Mindwipe Tonic",
        "ingredients": {
            "Cooked Prime Meat": 24,
            "Mejoberry": 200,
            "Narcotic": 72,
            "Stimulant": 72,
            "Rare Mushroom": 20,
            "Rare Flower": 20,
            "Water": 1
        },
        "image": "https://ark.wiki.gg/images/thumb/f/fa/Mindwipe_Tonic.png/64px-Mindwipe_Tonic.png"
    },

    # -----------------------------
    # FOUNDATIONS
    # -----------------------------

    "thatch foundation": {
        "name": "Thatch Foundation",
        "ingredients": {
            "Thatch": 20,
            "Wood": 6,
            "Fiber": 15
        },
        "image": "https://ark.wiki.gg/images/thumb/e/ed/Thatch_Foundation.png/64px-Thatch_Foundation.png"
    },
    "wooden foundation": {
        "name": "Wooden Foundation",
        "ingredients": {
            "Wood": 80,
            "Thatch": 20,
            "Fiber": 15
        },
        "image": "https://ark.wiki.gg/images/thumb/d/d5/Wooden_Foundation.png/64px-Wooden_Foundation.png"
    },
    "stone foundation": {
        "name": "Stone Foundation",
        "ingredients": {
            "Stone": 80,
            "Wood": 40,
            "Thatch": 30
        },
        "image": "https://ark.wiki.gg/images/thumb/7/73/Stone_Foundation.png/64px-Stone_Foundation.png"
    },
    "metal foundation": {
        "name": "Metal Foundation",
        "ingredients": {
            "Metal Ingot": 50,
            "Cementing Paste": 15
        },
        "image": "https://ark.wiki.gg/images/thumb/2/23/Metal_Foundation.png/64px-Metal_Foundation.png"
    },
    "tek foundation": {
        "name": "Tek Foundation",
        "ingredients": {
            "Element": 1,
            "Metal Ingot": 100,
            "Crystal": 20,
            "Polymer": 45
        },
        "image": "https://ark.wiki.gg/images/thumb/8/80/Tek_Foundation.png/64px-Tek_Foundation.png"
    },

    # -----------------------------
    # WALLS
    # -----------------------------

    "thatch wall": {
        "name": "Thatch Wall",
        "ingredients": {
            "Thatch": 10,
            "Wood": 2,
            "Fiber": 7
        },
        "image": "https://ark.wiki.gg/images/thumb/5/55/Thatch_Wall.png/64px-Thatch_Wall.png"
    },
    "wooden wall": {
        "name": "Wooden Wall",
        "ingredients": {
            "Wood": 40,
            "Thatch": 10,
            "Fiber": 7
        },
        "image": "https://ark.wiki.gg/images/thumb/4/4f/Wooden_Wall.png/64px-Wooden_Wall.png"
    },
    "stone wall": {
        "name": "Stone Wall",
        "ingredients": {
            "Stone": 40,
            "Wood": 20,
            "Thatch": 15
        },
        "image": "https://ark.wiki.gg/images/thumb/1/1e/Stone_Wall.png/64px-Stone_Wall.png"
    },
    "metal wall": {
        "name": "Metal Wall",
        "ingredients": {
            "Metal Ingot": 25,
            "Cementing Paste": 7
        },
        "image": "https://ark.wiki.gg/images/thumb/0/0d/Metal_Wall.png/64px-Metal_Wall.png"
    },
    "tek wall": {
        "name": "Tek Wall",
        "ingredients": {
            "Element": 1,
            "Metal Ingot": 35,
            "Crystal": 15,
            "Polymer": 20
        },
        "image": "https://ark.wiki.gg/images/thumb/1/1d/Tek_Wall.png/64px-Tek_Wall.png"
    },

    # -----------------------------
    # DOORS
    # -----------------------------

    "thatch door": {
        "name": "Thatch Door",
        "ingredients": {
            "Thatch": 10,
            "Wood": 2,
            "Fiber": 7
        },
        "image": "https://ark.wiki.gg/images/thumb/1/12/Thatch_Door.png/64px-Thatch_Door.png"
    },
    "wooden door": {
        "name": "Wooden Door",
        "ingredients": {
            "Wood": 40,
            "Thatch": 10,
            "Fiber": 7
        },
        "image": "https://ark.wiki.gg/images/thumb/3/35/Wooden_Door.png/64px-Wooden_Door.png"
    },
    "stone door": {
        "name": "Stone Door",
        "ingredients": {
            "Stone": 40,
            "Wood": 20,
            "Thatch": 15
        },
        "image": "https://ark.wiki.gg/images/thumb/8/88/Stone_Door.png/64px-Stone_Door.png"
    },
    "metal door": {
        "name": "Metal Door",
        "ingredients": {
            "Metal Ingot": 25,
            "Cementing Paste": 7
        },
        "image": "https://ark.wiki.gg/images/thumb/e/e4/Metal_Door.png/64px-Metal_Door.png"
    },
    "tek door": {
        "name": "Tek Door",
        "ingredients": {
            "Element": 1,
            "Metal Ingot": 35,
            "Crystal": 15,
            "Polymer": 20
        },
        "image": "https://ark.wiki.gg/images/thumb/d/d5/Tek_Door.png/64px-Tek_Door.png"
    },

    # -----------------------------
    # CEILINGS
    # -----------------------------

    "thatch ceiling": {
        "name": "Thatch Ceiling",
        "ingredients": {
            "Thatch": 10,
            "Wood": 2,
            "Fiber": 7
        },
        "image": "https://ark.wiki.gg/images/thumb/a/a3/Thatch_Ceiling.png/64px-Thatch_Ceiling.png"
    },
    "wooden ceiling": {
        "name": "Wooden Ceiling",
        "ingredients": {
            "Wood": 40,
            "Thatch": 10,
            "Fiber": 7
        },
        "image": "https://ark.wiki.gg/images/thumb/3/39/Wooden_Ceiling.png/64px-Wooden_Ceiling.png"
    },
    "stone ceiling": {
        "name": "Stone Ceiling",
        "ingredients": {
            "Stone": 40,
            "Wood": 20,
            "Thatch": 15
        },
        "image": "https://ark.wiki.gg/images/thumb/4/4f/Stone_Ceiling.png/64px-Stone_Ceiling.png"
    },
    "metal ceiling": {
        "name": "Metal Ceiling",
        "ingredients": {
            "Metal Ingot": 35,
            "Cementing Paste": 10
        },
        "image": "https://ark.wiki.gg/images/thumb/3/37/Metal_Ceiling.png/64px-Metal_Ceiling.png"
    },
    "tek ceiling": {
        "name": "Tek Ceiling",
        "ingredients": {
            "Element": 1,
            "Metal Ingot": 50,
            "Crystal": 20,
            "Polymer": 25
        },
        "image": "https://ark.wiki.gg/images/thumb/b/b0/Tek_Ceiling.png/64px-Tek_Ceiling.png"
    },

    # -----------------------------
    # OTHERS
    # -----------------------------

    "tek gateway": {
        "name": "Tek Gateway",
        "ingredients": {
            "Element": 2,
            "Metal Ingot": 170,
            "Crystal": 30,
            "Polymer": 50
        },
        "image": "https://ark.wiki.gg/images/thumb/5/54/Tek_Gateway.png/64px-Tek_Gateway.png"
    },
    "metal gateway": {
        "name": "Metal Gateway",
        "ingredients": {
            "Metal Ingot": 170,
            "Cementing Paste": 50
        },
        "image": "https://ark.wiki.gg/images/thumb/2/2a/Metal_Gateway.png/64px-Metal_Gateway.png"
    },
    "dedi": {
        "name": "Tek Dedicated Storage",
        "ingredients": {
            "Element": 3,
            "Metal Ingot": 125,
            "Crystal": 75,
            "Polymer": 55,
            "Black Pearls": 4
        },
        "image": "https://ark.wiki.gg/images/thumb/7/7c/Tek_Dedicated_Storage.png/64px-Tek_Dedicated_Storage.png"
    },
    "tek generator": {
        "name": "Tek Generator",
        "ingredients": {
            "Element": 30,
            "Metal Ingot": 2400,
            "Crystal": 250,
            "Polymer": 500,
            "Black Pearls": 120
        },
        "image": "https://ark.wiki.gg/images/thumb/1/1a/Tek_Generator.png/64px-Tek_Generator.png"
    },
    "tek transmitter": {
        "name": "Tek Transmitter",
        "ingredients": {
            "Element": 40,
            "Metal Ingot": 2500,
            "Crystal": 250,
            "Polymer": 320,
            "Black Pearls": 80
        },
        "image": "https://ark.wiki.gg/images/thumb/4/41/Tek_Transmitter.png/64px-Tek_Transmitter.png"
    },
    "tek turret": {
        "name": "Tek Turret",
        "ingredients": {
            "Element": 3,
            "Metal Ingot": 100,
            "Electronics": 100,
            "Polymer": 50,
            "Cementing Paste": 50
        },
        "image": "https://ark.wiki.gg/images/thumb/d/d6/Tek_Turret.png/64px-Tek_Turret.png"
    },
    "heavy turret": {
        "name": "Heavy Turret",
        "ingredients": {
            "Metal Ingot": 540,
            "Electronics": 270,
            "Polymer": 70,
            "Cementing Paste": 200
        },
        "image": "https://ark.wiki.gg/images/thumb/e/e6/Heavy_Turret.png/64px-Heavy_Turret.png"
    }
}

# -----------------------------
# STEAM API HELPERS
# -----------------------------

async def get_steam_summary(steam_id: str):
    """Fetch name, avatar, and profile link from Steam API."""
    url = (
        f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        f"?key={STEAM_API_KEY}&steamids={steam_id}"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    players = data.get("response", {}).get("players", [])
    if not players:
        return None

    p = players[0]
    return {
        "name": p.get("personaname", "Unknown"),
        "avatar": p.get("avatarfull", ""),
        "profile": p.get("profileurl", "")
    }

# -----------------------------
# TAME CALCULATOR HELPERS
# -----------------------------

def calc_torpor(dino, lvl: int) -> int:
    return dino["base_torpor"] + (lvl - 1) * dino["torpor_per_level"]

def calc_affinity_needed(dino, lvl: int) -> int:
    return dino["base_affinity"] + (lvl - 1) * dino["taming_affinity_per_level"]

def calc_foods(dino, affinity_needed: int) -> list[str]:
    results = []
    for food, meta in dino["foods"].items():
        items_needed = math.ceil(affinity_needed / meta["affinity"])
        time_seconds = (items_needed * meta["food_value"]) / dino["food_drain"]
        mins = int(time_seconds // 60)
        results.append(f"- {food.replace('_',' ').title()}: {items_needed} ({mins} min)")
    return results

def calc_weapons(dino, torpor_needed: int) -> list[str]:
    results = []
    for weapon, torpor in dino["weapons"].items():
        shots = math.ceil(torpor_needed / torpor)
        results.append(f"- {weapon.replace('_',' ').title()}: {shots}")
    return results


# -----------------------------
# QUERY SERVERLIST.JSON
# -----------------------------

async def query_server(server_id: int):
    """Fetch server info from official ASA serverlist.json."""
    async with aiohttp.ClientSession() as session:
        async with session.get(SERVERLIST_URL) as resp:
            data = await resp.json()

    server = None
    for entry in data:
        if entry.get("Name", "").endswith(str(server_id)):
            server = entry
            break

    if not server:
        return {
            "name": f"Server {server_id} (not found)",
            "tracked_count": 0,
            "total": 0,
            "players": []
        }

    # Placeholder players (replace with EOS later if possible)
    players = []  

    return {
        "name": server["Name"],
        "tracked_count": len(players),
        "total": server["NumPlayers"],
        "players": players
    }

# -----------------------------
# FORMAT HELPERS
# -----------------------------

def format_dashboard_content(server_data, server_id):
    header = (f"{server_data['name']}\n"
              f"Players found: {server_data['tracked_count']}\n"
              f"Total Online: {server_data['total']}/70\n\n")

    table_header = (
        "Tag | Name            | Steam64          | Time Online | Main\n"
        "──────────────────────────────────────────────────────────────\n"
    )

    if server_id not in active_sessions or not active_sessions[server_id]:
        table_rows = ["⚪ | No player data available"]
    else:
        table_rows = []
        for steam64, meta in active_sessions[server_id].items():
            joined = meta["joined"]
            elapsed = datetime.datetime.utcnow() - joined
            mins = int(elapsed.total_seconds() // 60)
            table_rows.append(
                f"⚪ | {meta['name']:<16} | {steam64:<16} | {mins}m | {server_data['name']}"
            )

    return f"```{header}{table_header}" + "\n".join(table_rows) + "```"

# -----------------------------
# COMMANDS
# -----------------------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")
    dashboard_updater.start()

@bot.tree.command(name="lookup", description="Lookup an Ark server by ID")
@app_commands.describe(server_id="The 4-digit Ark server ID")
async def lookup(interaction: discord.Interaction, server_id: int):
    await interaction.response.defer()
    server_data = await query_server(server_id)
    embed = discord.Embed(
        title=server_data["name"],
        description=f"Players found: {server_data['tracked_count']}\n"
                    f"Total Online: {server_data['total']}/70",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="lookupid", description="Lookup a player by Steam64 ID")
@app_commands.describe(steam64="The player's Steam64 ID")
async def lookupid(interaction: discord.Interaction, steam64: str):
    await interaction.response.defer()

    if steam64 not in player_db:
        await interaction.followup.send(f"❌ No data found for `{steam64}`")
        return

    data = player_db[steam64]
    servers = data["servers"]

    main_server = max(servers.items(), key=lambda x: x[1]["visits"], default=None)
    top = sorted(servers.items(), key=lambda x: x[1]["visits"], reverse=True)[:5]
    recent = sorted(servers.items(), key=lambda x: x[1]["last_seen"], reverse=True)[:5]

    embed = discord.Embed(title=f"Lookup: {steam64}", color=discord.Color.blue())
    embed.add_field(name="Name", value=data["name"], inline=True)
    embed.add_field(name="Platform", value="Steam", inline=True)
    embed.add_field(name="Profile Link", value=f"https://steamcommunity.com/profiles/{steam64}", inline=False)

    if main_server:
        embed.add_field(name="Main Server", value=f"{main_server[0]} — {main_server[1]['visits']} visits", inline=False)

    if top:
        embed.add_field(
            name="Top Servers",
            value="\n".join([f"{srv} — {meta['visits']} visits" for srv, meta in top]),
            inline=False
        )

    if recent:
        embed.add_field(
            name="Recent Servers",
            value="\n".join([
                f"{srv} — {(datetime.datetime.utcnow() - datetime.datetime.fromisoformat(meta['last_seen'])).days} days ago"
                for srv, meta in recent
            ]),
            inline=False
        )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="dashboard_place", description="Place a live-updating dashboard in this channel")
@app_commands.describe(server_id="The 4-digit Ark server ID")
async def dashboard_place(interaction: discord.Interaction, server_id: int):
    await interaction.response.defer()
    server_data = await query_server(server_id)
    msg = await interaction.channel.send(format_dashboard_content(server_data, server_id))

    if interaction.channel.id not in dashboards:
        dashboards[interaction.channel.id] = []

    dashboards[interaction.channel.id].append({
        "message_id": msg.id,
        "server_id": server_id,
        "server_name": server_data["name"]
    })

    await interaction.followup.send(f"✅ Dashboard placed for server `{server_id}`", ephemeral=True)

@bot.tree.command(name="addgen", description="Add a generator timer")
@app_commands.describe(fuel="Number of element in the generator",
                       group="Group name (ex: ice, cave, base1)",
                       number="Generator number within the group")
async def addgen(interaction: discord.Interaction, fuel: int, group: str, number: int):
    await interaction.response.defer(ephemeral=True)

    if group not in generators:
        generators[group] = {}

    if str(number) in generators[group]:  # store as string for JSON keys
        await interaction.followup.send(f"❌ Generator `{group}-{number}` already exists.")
        return

    total_hours = fuel * 18
    end_timestamp = int(time.time() + total_hours * 3600)

    generators[group][str(number)] = {
        "fuel": fuel,
        "end_time": end_timestamp
    }

    save_gens()

    await interaction.followup.send(
        f"✅ Added generator `{group}-{number}` with {fuel} element(s). "
        f"Expires <t:{end_timestamp}:R>"
    )

@bot.tree.command(name="addgens", description="Add multiple generators at once")
@app_commands.describe(fuel="Number of element per generator",
                       group="Group name",
                       amount="How many generators to add")
async def addgens(interaction: discord.Interaction, fuel: int, group: str, amount: int):
    await interaction.response.defer(ephemeral=True)

    if group not in generators:
        generators[group] = {}

    total_hours = fuel * 18
    end_timestamp = int(time.time() + total_hours * 3600)

    created = []
    for n in range(1, amount + 1):
        if str(n) not in generators[group]:
            generators[group][str(n)] = {
                "fuel": fuel,
                "end_time": end_timestamp
            }
            created.append(f"{group}-{n}")

    save_gens()

    if not created:
        await interaction.followup.send("⚪ No new generators added (they already exist).")
    else:
        await interaction.followup.send(
            f"✅ Added {len(created)} generators with {fuel} element(s) each: {', '.join(created)}"
        )

@bot.tree.command(name="removegen", description="Remove a generator timer")
@app_commands.describe(group="Group name", number="Generator number")
async def removegen(interaction: discord.Interaction, group: str, number: int):
    await interaction.response.defer(ephemeral=True)

    if group not in generators or str(number) not in generators[group]:
        await interaction.followup.send(f"❌ Generator `{group}-{number}` not found.")
        return

    del generators[group][str(number)]
    if not generators[group]:
        del generators[group]

    save_gens()

    await interaction.followup.send(f"✅ Removed generator `{group}-{number}`")

@bot.tree.command(name="cleargens", description="Clear all generator timers")
async def cleargens(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    global generators
    generators = {}  # reset everything
    save_gens()      # persist the empty state

    await interaction.followup.send("✅ All generators have been cleared.", ephemeral=True)

@bot.tree.command(name="fillgen", description="Add fuel to an existing generator")
@app_commands.describe(fuel="Number of element added",
                       group="Group name",
                       number="Generator number")
async def fillgen(interaction: discord.Interaction, fuel: int, group: str, number: int):
    await interaction.response.defer(ephemeral=True)

    if group not in generators or str(number) not in generators[group]:
        await interaction.followup.send(f"❌ Generator `{group}-{number}` not found.")
        return

    added_hours = fuel * 18
    generators[group][str(number)]["end_time"] += added_hours * 3600
    generators[group][str(number)]["fuel"] += fuel

    save_gens()

    await interaction.followup.send(
        f"✅ Added {fuel} element(s) to `{group}-{number}`. "
        f"New expiry <t:{generators[group][str(number)]['end_time']}:R>"
    )

@bot.tree.command(name="fillgens", description="Add fuel to a range of generators")
@app_commands.describe(fuel="Number of element added per generator",
                       group="Group name",
                       numbers="Range of generator numbers (e.g. 1-15)")
async def fillgens(interaction: discord.Interaction, fuel: int, group: str, numbers: str):
    await interaction.response.defer(ephemeral=True)

    if "-" not in numbers:
        await interaction.followup.send("❌ Please use a range format like `1-15`.")
        return

    start, end = map(int, numbers.split("-"))
    updated = []

    for n in range(start, end + 1):
        if group in generators and str(n) in generators[group]:
            added_hours = fuel * 18
            generators[group][str(n)]["end_time"] += added_hours * 3600
            generators[group][str(n)]["fuel"] += fuel
            updated.append(f"{group}-{n}")

    save_gens()

    if not updated:
        await interaction.followup.send("⚪ No generators updated (check range).")
    else:
        await interaction.followup.send(
            f"✅ Added {fuel} element(s) to: {', '.join(updated)}"
        )

@bot.tree.command(name="gentimers", description="Show all generator timers")
async def gentimers(interaction: discord.Interaction):
    await interaction.response.defer()

    if not generators:
        await interaction.followup.send("⚪ No generators being tracked.")
        return

    embed = discord.Embed(
        title="⚡ Generator Timers",
        color=discord.Color.orange()
    )

    for group in sorted(generators.keys()):
        gens = generators[group]
        sorted_gens = sorted(gens.items(), key=lambda x: int(x[0]))

        lines = []
        for number, meta in sorted_gens:
            id_text   = f"{group}-{number}"
            id_field  = f"`{id_text}`".ljust(16)
            time_field = f"<t:{meta['end_time']}:R>".ljust(18)
            fuel_field = f"(fuel: {meta['fuel']} element)"

            lines.append(f"{id_field} ⏳ {time_field} {fuel_field}")

        embed.add_field(
            name=group,
            value="\n".join(lines),
            inline=False
        )

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="recipe", description="Show recipe details")
@app_commands.describe(id="Item Name (e.g. focal chili, blue coloring, tek gateway)")
async def recipe(interaction: discord.Interaction, id: str):
    sid = id.lower()
    if sid not in ITEMS:
        await interaction.response.send_message(f"❌ Unknown recipe `{id}`", ephemeral=True)
        return

    s = ITEMS[sid]

    lines = [f"- {res}: {qty}" for res, qty in s["ingredients"].items()]
    embed = discord.Embed(
        title=f"📜 Recipe: {s['name']}",
        description="\n".join(lines),
        color=discord.Color.orange()
    )
    if "image" in s:
        embed.set_thumbnail(url=s["image"])

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="crafting", description="Calculate resources for structures and recipes")
@app_commands.describe(name="Item ID (e.g. metal foundation, superior kibble, medbrew)", amount="How many to craft")
async def crafting(interaction: discord.Interaction, name: str, amount: int):
    sid = name.lower()
    if sid not in ITEMS:
        await interaction.response.send_message(f"❌ Unknown item `{name}`", ephemeral=True)
        return

    s = ITEMS[sid]
    resources = {res: qty * amount for res, qty in s["ingredients"].items()}

    lines = [f"- {res}: {qty}" for res, qty in resources.items()]
    embed = discord.Embed(
        title=f"🔨 Crafting {amount}x {s['name']}",
        description="\n".join(lines),
        color=discord.Color.gold()
    )
    if "image" in s:
        embed.set_thumbnail(url=s["image"])

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dododex", description="Taming info for a creature")
@app_commands.describe(name="Creature name", lvl="Target level")
async def dododex(interaction: discord.Interaction, name: str, lvl: int):
    key = name.lower().replace(" ", "")
    if key not in dinosaurs:
        await interaction.response.send_message(f"❌ No data for `{name}` yet.", ephemeral=True)
        return

    dino = dinosaurs[key]

    torpor_needed = calc_torpor(dino, lvl)
    affinity_needed = calc_affinity_needed(dino, lvl)

    tranq_results = calc_weapons(dino, torpor_needed)
    food_results = calc_foods(dino, affinity_needed)

    embed = discord.Embed(
        title=f"Taming: {name.title()} (Lv {lvl})",
        color=discord.Color.green()
    )
    embed.add_field(name="Knockout", value="\n".join(tranq_results), inline=False)
    embed.add_field(name="Food", value="\n".join(food_results), inline=False)
    embed.set_footer(text="Approximate values — from ARK Wiki")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 ASA Companion — Help Menu",
        description="Here are the available commands:",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="⚡ Generators",
        value=(
            "`/addgen fuel: group: number:` → Add a generator timer\n"
            "`/addgens fuel: group: amount:` → Add multiple generators\n"
            "`/removegen group: number:` → Remove a generator timer\n"
            "`/cleargens group: number:` → Clear all generator timers\n"
            "`/fillgen fuel: group: number:` → Add fuel to one generator\n"
            "`/fillgens fuel: group: numbers:` → Add fuel to a range of generators\n"
            "`/gentimers` → Show all generator timers"
        ),
        inline=False
    )

    embed.add_field(
        name="🛠️ Crafting & Recipes",
        value=(
            "`/crafting name: amount:` → Calculate resources for recipes\n"
            "`/recipe name:` → Show recipe details"
        ),
        inline=False
    )

    embed.add_field(
        name="🦖 Creatures",
        value=(
            "`/dododex name: lvl:` → Dododex-style taming info"
        ),
        inline=False
    )

    embed.add_field(
        name="📊 Server Info",
        value=(
            "`/lookup server_id:` → Lookup an Ark server by ID\n"
            "`/lookupid steam64:` → Lookup a player by Steam64 ID\n"
            "`/dashboard_place server_id:` → Place a live-updating dashboard"
        ),
        inline=False
    )

    embed.set_footer(text="ASA Companion Bot — made by @kqzoo")

    await interaction.response.send_message(embed=embed, ephemeral=True)


# -----------------------------
# TASK: Update dashboards
# -----------------------------

@tasks.loop(seconds=30)
async def dashboard_updater():
    for channel_id, dash_list in dashboards.items():
        channel = bot.get_channel(channel_id)
        if not channel:
            continue
        for info in dash_list:
            try:
                msg = await channel.fetch_message(info["message_id"])
                server_data = await query_server(info["server_id"])

                # TODO: replace fake player logic with actual EOS player tracking
                # For now, we'll just keep active_sessions empty

                timestamp = f"Last updated <t:{int(time.time())}:R>"
                content = format_dashboard_content(server_data, info["server_id"])
                await msg.edit(content=f"{timestamp}\n{content}")
            except Exception as e:
                print(f"❌ Dashboard update error in {channel_id}: {e}")

# -----------------------------
# RUN
# -----------------------------


bot.run(TOKEN)
