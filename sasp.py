import discord
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
import time
import os

# =====================
# AYARLAR
# =====================
TOKEN = os.getenv("TOKEN")  # Railway ENV
GUILD_ID = 123456789012345678
VOICE_CHANNEL_ID = 123456789012345678
LOG_CHANNEL_ID = 123456789012345678
YETKILI_ROLE_ID = 123456789012345678

start_time = time.time()

# =====================
# BOT
# =====================
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =====================
# UPTIME SERVER
# =====================
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

# =====================
# READY
# =====================
@bot.event
async def on_ready():
    print(f"{bot.user} aktif")
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="SASP Department"
        )
    )

    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)

    await join_voice_247()
    ping_loop.start()

# =====================
# 24/7 SES
# =====================
async def join_voice_247():
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(VOICE_CHANNEL_ID)

    if not guild.voice_client:
        await channel.connect(self_deaf=True)  
        # self_deaf = bot kulaklığı kapalı (dinlemez)

# =====================
# YETKİ KONTROL
# =====================
def yetkili():
    async def predicate(interaction: discord.Interaction):
        role = interaction.guild.get_role(YETKILI_ROLE_ID)
        return role in interaction.user.roles
    return app_commands.check(predicate)

# =====================
# SLASH: PING
# =====================
@tree.command(name="ping", description="Bot durumu", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    uptime = int(time.time() - start_time)
    await interaction.response.send_message(
        f"📡 Ping: {round(bot.latency*1000)}ms\n"
        f"⏱ Uptime: {uptime//3600}sa {(uptime%3600)//60}dk {uptime%60}sn"
    )

# =====================
# SLASH: BAN
# =====================
@tree.command(name="ban", description="Kullanıcıyı banlar", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):
    await user.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {user} banlandı")

# =====================
# SLASH: KICK
# =====================
@tree.command(name="kick", description="Kullanıcıyı atar", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):
    await user.kick(reason=reason)
    await interaction.response.send_message(f"👢 {user} atıldı")

# =====================
# SLASH: TIMEOUT
# =====================
@tree.command(name="timeout", description="Susturma verir", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    dakika: int,
    reason: str = "Sebep yok"
):
    until = discord.utils.utcnow() + discord.timedelta(minutes=dakika)
    await user.timeout(until, reason=reason)
    await interaction.response.send_message(
        f"⏳ {user} {dakika} dk susturuldu"
    )

# =====================
# SLASH: CLEAR
# =====================
@tree.command(name="clear", description="Mesaj siler", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(
        f"🧹 {amount} mesaj silindi",
        ephemeral=True
    )

# =====================
# 5 DK PING LOOP
# =====================
@tasks.loop(minutes=5)
async def ping_loop():
    channel = bot.get_channel(LOG_CHANNEL_ID)
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

# =====================
bot.run(TOKEN)
