import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import asyncio

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "records.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    try:
        if GUILD_ID != 0:
            await tree.sync(guild=discord.Object(id=GUILD_ID))
        else:
            await tree.sync()
        print(f"✅ Bot aktif: {bot.user}")
    except Exception as e:
        print("❌ Slash sync hatası:", e)

# -------------------- YETKİ KONTROL --------------------
def admin_only(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

# -------------------- SLASH KOMUTLAR --------------------

@tree.command(name="ping", description="Bot gecikmesini gösterir")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! `{round(bot.latency * 1000)}ms`", ephemeral=True
    )

@tree.command(name="ban", description="Kullanıcıyı banlar")
@app_commands.check(admin_only)
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep belirtilmedi"):
    await interaction.response.defer(ephemeral=True)
    await user.ban(reason=reason)

    data = load_data()
    uid = str(user.id)
    data.setdefault(uid, []).append(f"BAN: {reason}")
    save_data(data)

    await interaction.followup.send(f"🚫 {user} banlandı.")

@tree.command(name="kick", description="Kullanıcıyı atar")
@app_commands.check(admin_only)
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep belirtilmedi"):
    await interaction.response.defer(ephemeral=True)
    await user.kick(reason=reason)
    await interaction.followup.send(f"👢 {user} atıldı.")

@tree.command(name="timeout", description="Kullanıcıya timeout atar")
@app_commands.check(admin_only)
async def timeout(
    interaction: discord.Interaction,
    user: discord.Member,
    minutes: int,
    reason: str = "Sebep belirtilmedi"
):
    await interaction.response.defer(ephemeral=True)
    duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
    await user.edit(timed_out_until=duration, reason=reason)
    await interaction.followup.send(f"⏳ {user} {minutes} dk timeout aldı.")

@tree.command(name="sicil", description="Kullanıcının sicilini gösterir")
async def sicil(interaction: discord.Interaction, user: discord.Member):
    data = load_data()
    records = data.get(str(user.id), [])

    if not records:
        msg = "🟢 Sicil temiz."
    else:
        msg = "\n".join(records)

    await interaction.response.send_message(
        f"📄 **{user} Sicil**\n```{msg}```",
        ephemeral=True
    )

# -------------------- ERROR HANDLER --------------------
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ Bu komutu kullanma yetkin yok.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"⚠️ Hata: {error}", ephemeral=True
        )

bot.run(TOKEN)
