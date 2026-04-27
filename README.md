<div align="center">

# 🦖 ASA Companion Bot

### The Ultimate Discord Utility Bot for ARK: Survival Ascended

Track servers • Manage generators • Craft smarter • Tame faster • Monitor players

<img src="https://img.shields.io/badge/python-3.10+-blue?style=for-the-badge&logo=python">
<img src="https://img.shields.io/badge/discord.py-latest-5865F2?style=for-the-badge&logo=discord">
<img src="https://img.shields.io/badge/status-active-success?style=for-the-badge">

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### ⚡ Generator Timers
Track all tribe generators with automatic expiration times.

**Commands**
- `/addgen`
- `/addgens`
- `/fillgen`
- `/fillgens`
- `/removegen`
- `/gentimers`

</td>
<td width="50%">

### 📊 Server Dashboard
Live-updating ARK server dashboards inside Discord.

**Commands**
- `/lookup`
- `/dashboard_place`

Updates every **30 seconds**

</td>
</tr>

<tr>
<td width="50%">

### 🛠️ Crafting Calculator
Calculate exact resources for any item.

**Commands**
- `/crafting`
- `/recipe`

</td>
<td width="50%">

### 🦖 Dododex Taming
Knockout + food requirements instantly.

**Command**
- `/dododex`

</td>
</tr>

<tr>
<td width="50%">

### 👤 Steam Player Lookup
Track players, main servers, and visit history.

**Command**
- `/lookupid`

</td>
<td width="50%">

### 💾 Persistent Storage
Automatically saves data using JSON databases.

- players.json  
- generators.json  
- items.json  
- dinosaurs.json

</td>
</tr>
</table>

---

## 📸 Preview

<div align="center">

<img width="700" src="https://raw.githubusercontent.com/github/explore/main/topics/discord/discord.png">

</div>

---

## 🚀 Quick Setup

### 1️⃣ Install Dependencies

```bash
pip install -U discord.py aiohttp
