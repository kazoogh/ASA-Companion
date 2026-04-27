ASA Companion Bot

A powerful Discord bot for ARK: Survival Ascended (ASA) players and tribes.
Track official servers, manage generator timers, calculate crafting costs, lookup players, and use Dododex-style taming tools directly inside Discord.

Built with Python + discord.py

🚀 Features
⚡ Generator Timer Tracking

Keep track of your tribe generators and element fuel.

Commands:

/addgen → Add a single generator
/addgens → Add multiple generators
/removegen → Remove generator
/cleargens → Clear all generators
/fillgen → Refill one generator
/fillgens → Refill multiple generators
/gentimers → View all active generator timers

Example:

/addgen fuel:2 group:ice number:1
🛠️ Crafting Calculator

Calculate resources needed for structures, recipes, kibble, brews, etc.

Commands:

/crafting
/recipe

Example:

/crafting name:"metal foundation" amount:20
🦖 Dododex Style Taming Calculator

View knockout shots + food required for taming creatures.

Command:

/dododex name:rex lvl:150

Shows:

Tranq arrows needed
Tranq darts needed
Food required
Approximate tame time
📊 Official Server Lookup

Pull server information directly from official ARK server list.

Commands:

/lookup
/dashboard_place

Example:

/lookup server_id:1234
👤 Steam Player Lookup

Track previously seen players and their server history.

Command:

/lookupid steam64:76561198000000000

Displays:

Steam profile link
Most visited servers
Recent servers
Main server
📺 Live Dashboard System

Create live-updating server dashboards in Discord channels.

Command:

/dashboard_place server_id:1234

Updates every 30 seconds

Shows:

Server population
Players tracked
Last updated timestamp
📦 Installation
1. Clone Repository
git clone https://github.com/yourusername/asa-companion-bot.git
cd asa-companion-bot
2. Install Dependencies
pip install -U discord.py aiohttp
3. Configure Bot

Open the Python file and replace:

TOKEN = "YOUR_DISCORD_BOT_TOKEN"
GUILD_TOKEN = "YOUR_GUILD_ID"
STEAM_API_KEY = "YOUR_STEAM_API_KEY"
4. Run Bot
python bot.py
📁 Data Files

The bot automatically stores persistent data in JSON files:

players.json
generators.json
items.json
dinosaurs.json
🛠 Built With
Python 3.10+
discord.py
aiohttp
Steam Web API
ARK Official Server API
📌 Future Features
EOS Player Tracking
Tribe Logs
Raid Alerts
Discord Dashboard UI
Market Prices
Breeding Timers
Crossplay Detection
PvP Enemy Watchlists
