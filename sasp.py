import os
import time
import asyncio
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
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID"))
PING_CHANNEL_ID = int(os.getenv("PING_CHANNEL_ID", 0))
YETKILI_ROLE_ID = int(os.getenv("YETKILI_ROLE_ID", 0))

start_time = time.time()

# =========================
# BOT
# =========================
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

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
# YETKI CHECK
# =========================
def yetkili():
    async def predicate(interaction: discord.Interaction):
        if YETKILI_ROLE_ID == 0:
            return True
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
        activity=discord.Game("San Andreas State Police")
    )

    await ensure_voice()

    if PING_CHANNEL_ID != 0:
        ping_loop.start()

    print("✅ Bot hazır | Slashlar yüklendi | Ses aktif")

# =========================
# 24/7 SES
# =========================
async def ensure_voice():
    await bot.wait_until_ready()

    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(VOICE_CHANNEL_ID)

    if not channel:
        print("❌ Ses kanalı bulunamadı")
        return

    if guild.voice_client:
        return

    try:
        await channel.connect()
        print("🔊 Bot sese bağlandı")
    except Exception as e:
        print(f"Ses hatası: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    guild = bot.get_guild(GUILD_ID)
    vc = guild.voice_client

    if not vc or not vc.channel:
        await ensure_voice()

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
    channel = bot.get_channel(PING_CHANNEL_ID)
    if not channel:
        return

    uptime = int(time.time() - start_time)
    msg = (
        f"📡 Ping: {round(bot.latency*1000)}ms\n"
        f"⏱ Uptime: {uptime//3600}sa {(uptime%3600)//60}dk {uptime%60}sn"
    )

    async for m in channel.history(limit=3):
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
    await user.timeout(
        discord.utils.utcnow() + discord.timedelta(minutes=dakika)
    )
    await interaction.response.send_message(f"⏳ {user} timeout aldı")

# =========================
# START
# =========================
bot.run(TOKEN)
