import discord
from discord.ext import commands
import asyncio
import os

# =====================
# AYARLAR
# =====================
TOKEN = os.getenv("TOKEN")  # Railway Variables'a ekle
GUILD_ID = 123456789012345678
VOICE_CHANNEL_ID = 123456789012345678

# =====================
# BOT
# =====================
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# READY
# =====================
@bot.event
async def on_ready():
    print(f"{bot.user} aktif")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="24/7 Ses"
        )
    )
    await ensure_voice()

# =====================
# 24/7 SES GARANTİ
# =====================
async def ensure_voice():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Guild bulunamadı")
        return

    channel = guild.get_channel(VOICE_CHANNEL_ID)
    if not channel:
        print("Ses kanalı bulunamadı")
        return

    while True:
        try:
            if not guild.voice_client:
                await channel.connect(self_deaf=True)
                print("Sese girildi (24/7)")
        except Exception as e:
            print("Ses hatası:", e)

        await asyncio.sleep(30)

# =====================
# ATILIRSA TEKRAR GİR
# =====================
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and after.channel is None:
        await asyncio.sleep(5)
        await ensure_voice()

# =====================
bot.run(TOKEN)
