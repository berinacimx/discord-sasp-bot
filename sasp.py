import os
import time
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread

# =======================
# ENV
# =======================
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
YETKILI_ROLE_ID = int(os.getenv("YETKILI_ROLE_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

start_time = time.time()

# =======================
# BOT
# =======================
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =======================
# UPTIME
# =======================
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

# =======================
# YETKİ
# =======================
def yetkili():
    async def predicate(interaction: discord.Interaction):
        role = interaction.guild.get_role(YETKILI_ROLE_ID)
        return role in interaction.user.roles
    return app_commands.check(predicate)

# =======================
# READY
# =======================
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="SASP Department"
        )
    )

    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"{len(synced)} slash komut yüklendi")
    except Exception as e:
        print("SYNC HATASI:", e)

    print("Bot aktif!")

# =======================
# SLASH KOMUTLAR
# =======================

@tree.command(name="ping", description="Bot durumu", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    uptime = int(time.time() - start_time)
    await interaction.response.send_message(
        f"📡 Ping: {round(bot.latency*1000)}ms\n"
        f"⏱ Uptime: {uptime//3600}sa {(uptime%3600)//60}dk {uptime%60}sn",
        ephemeral=True
    )

@tree.command(name="clear", description="Mesaj sil", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 {amount} mesaj silindi")

@tree.command(name="kick", description="Kick at", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):
    await interaction.response.defer()
    await user.kick(reason=reason)
    await interaction.followup.send(f"👢 {user.mention} atıldı")

@tree.command(name="ban", description="Ban at", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):
    await interaction.response.defer()
    await user.ban(reason=reason)
    await interaction.followup.send(f"🔨 {user.mention} banlandı")

@tree.command(name="sicil", description="Kullanıcı sicil", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def sicil(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(
        f"📄 {user.mention} sicil kaydı temiz.",
        ephemeral=True
    )

# =======================
# RUN
# =======================
if not TOKEN:
    raise RuntimeError("TOKEN ENV YOK!")

bot.run(TOKEN)
