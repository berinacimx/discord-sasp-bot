import os
import threading
from flask import Flask
import discord
from discord import app_commands

# ---------- ENV ----------
TOKEN = os.environ["TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])

# ---------- FLASK ----------
app = Flask("uptime")

@app.route("/")
def home():
    return "SASP Bot Online"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ---------- DISCORD ----------
intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Bot aktif: {bot.user}")

# ---------- ÖRNEK SLASH ----------
@tree.command(
    name="ping",
    description="Bot gecikmesini gösterir",
    guild=discord.Object(id=GUILD_ID)
)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

# ---------- START ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
