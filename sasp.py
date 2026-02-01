import os
import discord
from discord import app_commands
from flask import Flask
from threading import Thread

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID"))

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# -------- FLASK (Railway uptime) --------
app = Flask("uptime")

@app.route("/")
def home():
    return "Bot Aktif"

def run_web():
    app.run(host="0.0.0.0", port=8080)

# -------- SLASH KOMUTLAR --------
@tree.command(name="ping", description="Bot gecikmesi", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!", ephemeral=True)

@tree.command(name="clear", description="Mesaj sil", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(adet="Silinecek mesaj sayısı")
async def clear(interaction: discord.Interaction, adet: int):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ Yetkin yok", ephemeral=True)

    await interaction.channel.purge(limit=adet)
    await interaction.response.send_message(f"🧹 {adet} mesaj silindi", ephemeral=True)

# -------- SES 24/7 --------
@bot.event
async def on_ready():
    print(f"✅ {bot.user} aktif")

    guild = bot.get_guild(GUILD_ID)
    voice = guild.get_channel(VOICE_CHANNEL_ID)

    if voice:
        try:
            await voice.connect(reconnect=True)
            print("🔊 Ses kanalına bağlanıldı (24/7)")
        except:
            print("⚠️ Zaten seste")

    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("✅ Slash komutlar yüklendi")

# -------- BAŞLAT --------
Thread(target=run_web).start()
bot.run(TOKEN)
