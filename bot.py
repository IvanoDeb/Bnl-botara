
import discord
from discord.ext import commands, tasks
import datetime
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

DATA_FILE = 'data.json'

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        players = data.get("players", {})
        budgets = data.get("budgets", {})
        loans = data.get("loans", {})
else:
    players = {}
    budgets = {
        "GNK Dinamo Zagreb": 10950000,
        "HNK Hajduk Split": 33200000,
        "HNK Rijeka": 2600000,
        "NK Osijek": 3000000,
        "NK Istra 1961": 1500000,
        "NK Šibenik": 1950000,
        "HŠK Zrinjski Mostar": 5000000,
        "NK Široki Brijeg": 1500000,
        "FK Borac Banja Luka": 4600000,
        "FK Željezničar": 10000000,
        "FK Velež Mostar": 8600000
    }
    loans = {}

CLUBS = list(budgets.keys())

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump({"players": players, "budgets": budgets, "loans": loans}, f)

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    check_loans.start()

@bot.command()
async def register(ctx, discord_user: discord.Member, roblox_username: str, club: str, contract: str):
    if club not in CLUBS:
        await ctx.send("Invalid club name. Use one of: " + ", ".join(CLUBS))
        return
    if str(discord_user.id) in players:
        await ctx.send(f"{discord_user.display_name} is already registered for {players[str(discord_user.id)]['club']}.")
    else:
        players[str(discord_user.id)] = {
            "discord": str(discord_user),
            "roblox": roblox_username,
            "club": club,
            "contract": contract
        }
        save_data()
        await ctx.send(f"Player {discord_user.display_name} registered to {club} with contract {contract}.")

@bot.command()
async def transfer(ctx, player: discord.Member, to_club: str, price: int):
    pid = str(player.id)
    if pid not in players:
        await ctx.send("Player is not registered.")
        return

    from_club = players[pid]["club"]

    if from_club not in budgets or to_club not in budgets:
        await ctx.send("Invalid club name.")
        return

    if budgets[to_club] < price:
        await ctx.send(f"{to_club} does not have enough budget.")
        return

    budgets[to_club] -= price
    budgets[from_club] += price
    players[pid]["club"] = to_club
    save_data()
    await ctx.send(f"{player.display_name} transferred from {from_club} to {to_club} for €{price}.")

@bot.command()
async def remove(ctx, player: discord.Member):
    pid = str(player.id)
    if pid in players:
        del players[pid]
        save_data()
        await ctx.send(f"{player.display_name} removed from registry.")
    else:
        await ctx.send("Player not found.")

@bot.command()
async def players_list(ctx):
    if not players:
        await ctx.send("No players registered.")
        return

    message = "**Registered players:**
"
    for p in players.values():
        message += f"{p['discord']} | Roblox: {p['roblox']} | Club: {p['club']} | Contract: {p['contract']}
"
    await ctx.send(message)

@bot.command()
async def budgets_list(ctx):
    message = "**Club Budgets:**
"
    for club, budget in budgets.items():
        message += f"{club}: €{budget}
"
    await ctx.send(message)

@bot.command()
async def loan(ctx, player: discord.Member, to_club: str, contract: str):
    pid = str(player.id)
    if pid not in players:
        await ctx.send("Player is not registered.")
        return

    try:
        duration_days = int(contract.replace("d", ""))
        end_date = datetime.datetime.utcnow() + datetime.timedelta(days=duration_days)
        loans[pid] = {
            "original_club": players[pid]["club"],
            "loaned_to": to_club,
            "end_date": end_date.isoformat()
        }
        players[pid]["club"] = to_club
        save_data()
        await ctx.send(f"{player.display_name} loaned to {to_club} for {duration_days} days.")
    except Exception as e:
        await ctx.send("Invalid contract format. Use format like `10d`.")

@tasks.loop(hours=24)
async def check_loans():
    now = datetime.datetime.utcnow()
    to_remove = []
    for pid, loan in loans.items():
        if now >= datetime.datetime.fromisoformat(loan["end_date"]):
            players[pid]["club"] = loan["original_club"]
            to_remove.append(pid)
    for pid in to_remove:
        del loans[pid]
    save_data()

@bot.command()
async def helpbot(ctx):
    await ctx.send("""
**Bot commands:**
/register [discord_user] [roblox_username] [club] [contract]  
/transfer [discord_user] [to_club] [price]  
/remove [discord_user]  
/players_list  
/budgets_list  
/loan [discord_user] [to_club] [contract, e.g. 10d]  
""")

bot.run("MTM3MjMzNjA3ODYzNTQwNTQxMw.Gj-nyG.snZ9HfnF0gd0ioZLUtVBvRs2Z9Pg4Gx7LTaNfU")
