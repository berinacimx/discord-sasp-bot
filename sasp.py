import os
import time
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread

# ======================
# ORTAM DEĞİŞKENLERİ
# ======================
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
YETKILI_ROLE_ID = int(os.getenv("YETKILI_ROLE_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

start_time = time.time()

# ======================
# BOT AYARLARI
# ======================
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ======================
# UPTIME (FLASK)
# ======================
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

Thread(target=run_web, daemon=True).start()

# ======================
# SİCİL (RAM)
# ======================
sicil = {}

def add_sicil(user_id, action):
    sicil.setdefault(user_id, []).append(action)

# ======================
# YETKİ KONTROL
# ======================
def yetkili():
    async def predicate(interaction: discord.Interaction):
        role = interaction.guild.get_role(YETKILI_ROLE_ID)
        return role in interaction.user.roles
    return app_commands.check(predicate)

# ======================
# READY
# ======================
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="SASP Departmanı"
        )
    )

    guild = discord.Object(id=GUILD_ID)

    # 🔥 KOMUTLARI TEMİZLE (ÇAKIŞMA YOK)
    tree.clear_commands(guild=guild)
    await tree.sync(guild=guild)

    print(f"✅ {bot.user} aktif | Slash komutlar temiz + yüklendi")

# ======================
# SLASH KOMUTLAR
# ======================

@tree.command(name="ping", description="Bot durumu", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    uptime = int(time.time() - start_time)
    await interaction.response.send_message(
        f"🏓 Ping: {round(bot.latency*1000)}ms\n"
        f"⏱ Uptime: {uptime//3600}sa {(uptime%3600)//60}dk {uptime%60}sn"
    )

@tree.command(name="sicil", description="Kullanıcı sicili", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def sicil_goster(interaction: discord.Interaction, user: discord.Member):
    kayıtlar = sicil.get(user.id, [])
    if not kayıtlar:
        return await interaction.response.send_message("📂 Sicil temiz")

    text = "\n".join(kayıtlar)
    await interaction.response.send_message(f"📋 {user.mention} sicili:\n{text}")

@tree.command(name="ban", description="Kullanıcı banla", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):
    await user.ban(reason=reason)
    add_sicil(user.id, f"Ban | {reason}")
    await interaction.response.send_message(f"🔨 {user} banlandı")

@tree.command(name="kick", description="Kullanıcı at", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):
    await user.kick(reason=reason)
    add_sicil(user.id, f"Kick | {reason}")
    await interaction.response.send_message(f"👢 {user} atıldı")

@tree.command(name="timeout", description="Timeout ver", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    dakika: int,
    reason: str = "Sebep yok"
):
    await user.timeout(discord.utils.utcnow() + discord.timedelta(minutes=dakika), reason=reason)
    add_sicil(user.id, f"Timeout {dakika}dk | {reason}")
    await interaction.response.send_message(f"⏳ {user} timeout aldı")

@tree.command(name="clear", description="Mesaj sil", guild=discord.Object(id=GUILD_ID))
@yetkili()
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 {amount} mesaj silindi", ephemeral=True)

# ======================
# BOTU BAŞLAT
# ======================
bot.run(TOKEN)
