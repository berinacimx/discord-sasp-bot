import os
import time
import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask, render_template_string
from threading import Thread

# =====================
# AYARLAR (ENV)
# =====================
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
YETKILI_ROLE_ID = int(os.getenv("YETKILI_ROLE_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
PORT = int(os.getenv("PORT", 8080))

start_time = time.time()
DATA_FILE = "sicil.json"

# =====================
# VERİ
# =====================
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# BOT
# =====================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =====================
# YETKİ KONTROL
# =====================
def yetkili():
    async def predicate(interaction: discord.Interaction):
        if YETKILI_ROLE_ID == 0:
            return True
        role = interaction.guild.get_role(YETKILI_ROLE_ID)
        return role in interaction.user.roles
    return app_commands.check(predicate)

async def logla(guild, mesaj):
    if LOG_CHANNEL_ID == 0:
        return
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(mesaj)

# =====================
# READY
# =====================
@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.watching, name="SASP Departmanı")
    )
    print(f"🚔 SASP Bot Aktif: {bot.user}")
    ping_loop.start()

# =====================
# MODERASYON
# =====================
@tree.command(name="ban", description="Kullanıcıyı banla")
@yetkili()
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):
    await user.ban(reason=reason)
    data = load_data()
    data.setdefault(str(user.id), []).append({
        "type": "BAN",
        "reason": reason,
        "yetkili": interaction.user.id,
        "time": int(time.time())
    })
    save_data(data)
    await interaction.response.send_message(f"🔨 {user} banlandı")
    await logla(interaction.guild, f"🔨 **BAN** | {user} | {reason}")

@tree.command(name="kick", description="Kullanıcıyı at")
@yetkili()
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):
    await user.kick(reason=reason)
    await interaction.response.send_message(f"👢 {user} atıldı")
    await logla(interaction.guild, f"👢 **KICK** | {user} | {reason}")

@tree.command(name="timeout", description="Timeout ver")
@yetkili()
async def timeout(interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "Sebep yok"):
    until = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
    await user.timeout(until, reason=reason)
    await interaction.response.send_message(f"⏱ {user} timeout aldı ({minutes} dk)")
    await logla(interaction.guild, f"⏱ **TIMEOUT** | {user} | {minutes} dk | {reason}")

# =====================
# SİCİL
# =====================
@tree.command(name="sicil", description="Kullanıcı sicili")
@yetkili()
async def sicil(interaction: discord.Interaction, user: discord.Member):
    data = load_data()
    kayıtlar = data.get(str(user.id), [])
    if not kayıtlar:
        return await interaction.response.send_message("📄 Sicil temiz ✅", ephemeral=True)

    msg = ""
    for i, k in enumerate(kayıtlar, 1):
        msg += f"{i}. {k['type']} | {k['reason']}\n"

    await interaction.response.send_message(f"📄 **{user} Sicili**\n{msg}", ephemeral=True)

# =====================
# TEMİZLİK
# =====================
@tree.command(name="clear", description="Mesaj sil")
@yetkili()
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 {amount} mesaj silindi", ephemeral=True)

# =====================
# ANTİ-SPAM (BASİT)
# =====================
spam_cache = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = time.time()
    spam_cache.setdefault(message.author.id, [])
    spam_cache[message.author.id].append(now)
    spam_cache[message.author.id] = [t for t in spam_cache[message.author.id] if now - t < 5]

    if len(spam_cache[message.author.id]) > 5:
        try:
            await message.delete()
            await message.author.timeout(discord.utils.utcnow() + discord.timedelta(minutes=1))
        except:
            pass

    await bot.process_commands(message)

# =====================
# PING & UPTIME
# =====================
@tree.command(name="ping", description="Bot durumu")
async def ping(interaction: discord.Interaction):
    uptime = int(time.time() - start_time)
    await interaction.response.send_message(
        f"📡 Ping: {round(bot.latency*1000)}ms\n"
        f"⏱ Uptime: {uptime//3600}sa {(uptime%3600)//60}dk"
    )

@tasks.loop(minutes=5)
async def ping_loop():
    pass

# =====================
# DASHBOARD
# =====================
app = Flask("sasp")

HTML = """
<html>
<head>
<title>SASP Dashboard</title>
<style>
body{background:#0f172a;color:white;font-family:Arial;text-align:center}
.card{background:#1e293b;padding:20px;margin:20px;border-radius:10px}
</style>
</head>
<body>
<h1>🚓 SASP Dashboard</h1>
<div class="card">Bot Durumu: 🟢 Online</div>
<div class="card">Uptime: {{uptime}}</div>
</body>
</html>
"""

@app.route("/")
def index():
    uptime = int(time.time() - start_time)
    return render_template_string(HTML, uptime=f"{uptime//3600}sa {(uptime%3600)//60}dk")

def run_web():
    app.run(host="0.0.0.0", port=PORT)

Thread(target=run_web).start()

# =====================
bot.run(TOKEN)
