import discord
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
import time
import datetime

# =====================
# AYARLAR
# =====================
TOKEN = "BOT_TOKEN"
GUILD_ID = 123456789012345678
LOG_CHANNEL_ID = 123456789012345678
PING_CHANNEL_ID = 123456789012345678
YETKILI_ROLE_ID = 123456789012345678

start_time = time.time()

# =====================
# BOT
# =====================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

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
# YETKİ KONTROL
# =====================
def yetkili():
    async def predicate(interaction: discord.Interaction):
        role = interaction.guild.get_role(YETKILI_ROLE_ID)
        return role in interaction.user.roles
    return app_commands.check(predicate)

# =====================
# READY
# =====================
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="SASP Departmanı"
        )
    )

    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"{bot.user} aktif!")
    ping_loop.start()

# =====================
# LOG
# =====================
async def log(guild, text):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(text)

# =====================
# SLASH /PING
# =====================
@tree.command(name="ping", description="Bot durumu", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    uptime = int(time.time() - start_time)
    await interaction.followup.send(
        f"📡 Ping: {round(bot.latency*1000)}ms\n"
        f"⏱ Uptime: {uptime//3600}sa {(uptime%3600)//60}dk {uptime%60}sn",
        ephemeral=True
    )

# =====================
# SLASH /CLEAR
# =====================
@tree.command(name="clear", description="Mesaj sil", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)

    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(
        f"🧹 {len(deleted)} mesaj silindi",
        ephemeral=True
    )

    await log(interaction.guild, f"🧹 {interaction.user} {len(deleted)} mesaj sildi")

# =====================
# SLASH /BAN
# =====================
@tree.command(name="ban", description="Kullanıcıyı banla", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):
    await interaction.response.defer(ephemeral=True)

    await user.ban(reason=reason)
    await interaction.followup.send(f"🔨 {user} banlandı", ephemeral=True)

    await log(interaction.guild, f"🔨 {user} banlandı | {interaction.user}")

# =====================
# SLASH /KICK
# =====================
@tree.command(name="kick", description="Kullanıcıyı at", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):
    await interaction.response.defer(ephemeral=True)

    await user.kick(reason=reason)
    await interaction.followup.send(f"👢 {user} atıldı", ephemeral=True)

    await log(interaction.guild, f"👢 {user} kicklendi | {interaction.user}")

# =====================
# SLASH /TIMEOUT
# =====================
@tree.command(name="timeout", description="Timeout at", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def timeout(interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "Sebep yok"):
    await interaction.response.defer(ephemeral=True)

    until = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
    await user.timeout(until, reason=reason)

    await interaction.followup.send(
        f"⏳ {user} {minutes} dk timeoutlandı",
        ephemeral=True
    )

    await log(interaction.guild, f"⏳ {user} timeout | {minutes}dk | {interaction.user}")

# =====================
# SLASH /UNBAN
# =====================
@tree.command(name="unban", description="Ban kaldır", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def unban(interaction: discord.Interaction, user_id: int):
    await interaction.response.defer(ephemeral=True)

    user = await bot.fetch_user(user_id)
    await interaction.guild.unban(user)

    await interaction.followup.send(f"✅ {user} unbanlandı", ephemeral=True)
    await log(interaction.guild, f"✅ {user} unbanlandı | {interaction.user}")

# =====================
# PING LOOP (5 DK)
# =====================
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

    async for m in channel.history(limit=5):
        if m.author == bot.user:
            await m.edit(content=msg)
            return

    await channel.send(msg)

# =====================
bot.run(TOKEN)
