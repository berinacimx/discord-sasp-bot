import os
import time
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread

# =========================
# ENV
# =========================
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
YETKILI_ROLE_ID = int(os.getenv("YETKILI_ROLE_ID", 0))
PING_CHANNEL_ID = int(os.getenv("PING_CHANNEL_ID", 0))

start_time = time.time()

# =========================
# BOT
# =========================
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =========================
# DATABASE (SICIL)
# =========================
db = sqlite3.connect("sicil.db")
cur = db.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS sicil (
    user_id INTEGER,
    yetkili TEXT,
    sebep TEXT,
    tarih TEXT
)
""")
db.commit()

# =========================
# UPTIME SERVER
# =========================
app = Flask("uptime")

@app.route("/")
def home():
    uptime = int(time.time() - start_time)
    return {
        "status": "ok",
        "uptime": f"{uptime//3600}sa {(uptime%3600)//60}dk {uptime%60}sn"
    }

def run_web():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()

# =========================
# YETKI KONTROL
# =========================
def yetkili():
    async def predicate(interaction: discord.Interaction):
        role = interaction.guild.get_role(YETKILI_ROLE_ID)
        return role in interaction.user.roles
    return app_commands.check(predicate)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)

    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Game("SASP Dashboard")
    )

    ping_loop.start()
    print("✅ Bot hazır | Slash komutlar yüklendi")

# =========================
# DASHBOARD
# =========================
@tree.command(name="ping", description="Bot durumu", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    uptime = int(time.time() - start_time)
    await interaction.response.send_message(
        f"📡 Ping: {round(bot.latency*1000)}ms\n"
        f"⏱ Uptime: {uptime//3600}sa {(uptime%3600)//60}dk {uptime%60}sn"
    )

@tasks.loop(minutes=5)
async def ping_loop():
    if PING_CHANNEL_ID == 0:
        return

    channel = bot.get_channel(PING_CHANNEL_ID)
    if not channel:
        return

    uptime = int(time.time() - start_time)
    msg = (
        f"📡 Ping: {round(bot.latency*1000)}ms\n"
        f"⏱ Uptime: {uptime//3600}sa {(uptime%3600)//60}dk {uptime%60}sn"
    )

    async for m in channel.history(limit=5):
        if m.author == bot.user:
            await m.edit(content=msg)
            return

    await channel.send(msg)

# =========================
# MODERASYON
# =========================
@tree.command(name="ban", description="Ban at", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def ban(interaction: discord.Interaction, user: discord.Member, sebep: str = "Sebep yok"):
    await user.ban(reason=sebep)
    await interaction.response.send_message(f"🔨 {user} banlandı")

@tree.command(name="kick", description="Kick at", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def kick(interaction: discord.Interaction, user: discord.Member, sebep: str = "Sebep yok"):
    await user.kick(reason=sebep)
    await interaction.response.send_message(f"👢 {user} atıldı")

@tree.command(name="timeout", description="Timeout at", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def timeout(interaction: discord.Interaction, user: discord.Member, dakika: int):
    await user.timeout(discord.utils.utcnow() + discord.timedelta(minutes=dakika))
    await interaction.response.send_message(f"⏳ {user} timeout aldı")

# =========================
# SICIL
# =========================
@tree.command(name="sicil-ekle", description="Sicil ekle", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def sicil_ekle(interaction: discord.Interaction, user: discord.Member, sebep: str):
    cur.execute(
        "INSERT INTO sicil VALUES (?,?,?,datetime('now'))",
        (user.id, interaction.user.name, sebep)
    )
    db.commit()
    await interaction.response.send_message("✅ Sicil eklendi")

@tree.command(name="sicil-bak", description="Sicil bak", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def sicil_bak(interaction: discord.Interaction, user: discord.Member):
    cur.execute("SELECT yetkili, sebep, tarih FROM sicil WHERE user_id=?", (user.id,))
    rows = cur.fetchall()

    if not rows:
        return await interaction.response.send_message("📂 Sicil temiz")

    text = ""
    for r in rows:
        text += f"👮 {r[0]} | {r[1]} | {r[2]}\n"

    await interaction.response.send_message(text)

# =========================
# START
# =========================
bot.run(TOKEN)
