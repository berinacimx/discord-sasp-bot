import discord
from discord import app_commands
import os, json, asyncio
from flask import Flask
from threading import Thread
from datetime import timedelta

# ---------- ENV ----------
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID"))
YETKILI_ROLE_ID = int(os.getenv("YETKILI_ROLE_ID"))

# ---------- DISCORD ----------
intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# ---------- SICIL ----------
SICIL_FILE = "sicil.json"
if not os.path.exists(SICIL_FILE):
    with open(SICIL_FILE, "w") as f:
        json.dump({}, f)

def load_sicil():
    with open(SICIL_FILE, "r") as f:
        return json.load(f)

def save_sicil(data):
    with open(SICIL_FILE, "w") as f:
        json.dump(data, f, indent=2)

def yetkili_mi(member):
    return any(role.id == YETKILI_ROLE_ID for role in member.roles)

# ---------- FLASK ----------
app = Flask("uptime")

@app.route("/")
def home():
    return "Bot Aktif"

def run_web():
    app.run(host="0.0.0.0", port=8080)

# ---------- SLASH KOMUTLAR ----------

@tree.command(name="ping", description="Bot durumu", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong", ephemeral=True)

# ---- SICIL ----
@tree.command(name="sicil_ekle", description="Sicile kayıt ekle", guild=discord.Object(id=GUILD_ID))
async def sicil_ekle(interaction: discord.Interaction, uye: discord.Member, sebep: str):
    if not yetkili_mi(interaction.user):
        return await interaction.response.send_message("❌ Yetkin yok", ephemeral=True)

    data = load_sicil()
    uid = str(uye.id)

    data.setdefault(uid, []).append({
        "yetkili": interaction.user.name,
        "sebep": sebep
    })

    save_sicil(data)
    await interaction.response.send_message(f"📋 {uye.mention} siciline eklendi", ephemeral=True)

@tree.command(name="sicil_gor", description="Sicil görüntüle", guild=discord.Object(id=GUILD_ID))
async def sicil_gor(interaction: discord.Interaction, uye: discord.Member):
    data = load_sicil()
    kayıtlar = data.get(str(uye.id), [])

    if not kayıtlar:
        return await interaction.response.send_message("📄 Sicil temiz", ephemeral=True)

    text = "\n".join([f"• {k['sebep']} (Yetkili: {k['yetkili']})" for k in kayıtlar])
    await interaction.response.send_message(f"📋 **Sicil:**\n{text}", ephemeral=True)

# ---- MODERATION ----
@tree.command(name="ban", description="Üye banla", guild=discord.Object(id=GUILD_ID))
async def ban(interaction: discord.Interaction, uye: discord.Member, sebep: str):
    if not yetkili_mi(interaction.user):
        return await interaction.response.send_message("❌ Yetkin yok", ephemeral=True)

    await uye.ban(reason=sebep)
    await interaction.response.send_message(f"🔨 {uye} banlandı", ephemeral=True)

@tree.command(name="kick", description="Üye at", guild=discord.Object(id=GUILD_ID))
async def kick(interaction: discord.Interaction, uye: discord.Member, sebep: str):
    if not yetkili_mi(interaction.user):
        return await interaction.response.send_message("❌ Yetkin yok", ephemeral=True)

    await uye.kick(reason=sebep)
    await interaction.response.send_message(f"👢 {uye} atıldı", ephemeral=True)

@tree.command(name="timeout", description="Timeout ver", guild=discord.Object(id=GUILD_ID))
async def timeout(interaction: discord.Interaction, uye: discord.Member, dakika: int):
    if not yetkili_mi(interaction.user):
        return await interaction.response.send_message("❌ Yetkin yok", ephemeral=True)

    await uye.timeout(timedelta(minutes=dakika))
    await interaction.response.send_message(f"⏳ {uye} timeout aldı", ephemeral=True)

@tree.command(name="untimeout", description="Timeout kaldır", guild=discord.Object(id=GUILD_ID))
async def untimeout(interaction: discord.Interaction, uye: discord.Member):
    if not yetkili_mi(interaction.user):
        return await interaction.response.send_message("❌ Yetkin yok", ephemeral=True)

    await uye.timeout(None)
    await interaction.response.send_message("✅ Timeout kaldırıldı", ephemeral=True)

# ---------- READY ----------
@bot.event
async def on_ready():
    print(f"✅ {bot.user} aktif")

    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(VOICE_CHANNEL_ID)

    if channel:
        try:
            await channel.connect(reconnect=True)
            print("🔊 24/7 ses aktif")
        except:
            pass

    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("✅ Slash komutlar yüklendi")

# ---------- START ----------
Thread(target=run_web).start()
bot.run(TOKEN)
