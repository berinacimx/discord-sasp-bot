import discord
from discord.ext import commands
from discord import app_commands
import os, time, json
from flask import Flask, request, abort
from threading import Thread

# =====================
# AYARLAR
# =====================
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1234567890

SASP_ROLE_ID = 1234567890
AMIR_ROLE_ID = 1234567890

LOG_CHANNEL_ID = 1234567890

DASHBOARD_SECRET = "sasp-secret-key"

start_time = time.time()

# =====================
# BOT
# =====================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =====================
# SICIL
# =====================
SICIL_FILE = "sicil.json"
sicil = {}

def load_sicil():
    global sicil
    try:
        with open(SICIL_FILE, "r", encoding="utf-8") as f:
            sicil = json.load(f)
    except:
        sicil = {}

def save_sicil():
    with open(SICIL_FILE, "w", encoding="utf-8") as f:
        json.dump(sicil, f, ensure_ascii=False, indent=2)

# =====================
# DASHBOARD SERVER
# =====================
app = Flask("sasp")

@app.route("/")
def health():
    uptime = int(time.time() - start_time)
    return {"status":"ok","uptime":uptime}

@app.route("/dashboard")
def dashboard():
    if request.args.get("key") != DASHBOARD_SECRET:
        abort(403)

    guild = bot.get_guild(GUILD_ID)
    members = guild.members if guild else []

    total_users = len(members)
    online_users = len([m for m in members if m.status != discord.Status.offline])
    sasp_users = len([m for m in members if any(r.id in [SASP_ROLE_ID, AMIR_ROLE_ID] for r in m.roles)])

    sicil_count = sum(len(v) for v in sicil.values())

    uptime = int(time.time() - start_time)

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>SASP Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{
    background:#0b1622;
    color:white;
    font-family:Arial;
}}
.card {{
    background:#111c2d;
    padding:15px;
    border-radius:10px;
    margin:10px;
}}
.grid {{
    display:grid;
    grid-template-columns: repeat(3, 1fr);
}}
</style>
</head>

<body>
<h1>🚔 SASP CONTROL PANEL</h1>

<div class="grid">
<div class="card">👥 Toplam Üye: {total_users}</div>
<div class="card">🟢 Online: {online_users}</div>
<div class="card">👮 SASP Yetkili: {sasp_users}</div>
<div class="card">📁 Sicil Kayıt: {sicil_count}</div>
<div class="card">⏱ Uptime: {uptime//3600}sa {(uptime%3600)//60}dk</div>
<div class="card">🤖 Bot: Online</div>
</div>

<canvas id="chart1"></canvas>
<canvas id="chart2"></canvas>

<script>
const ctx1 = document.getElementById('chart1');
new Chart(ctx1, {{
    type: 'bar',
    data: {{
        labels: ['Toplam Üye','Online','SASP Yetkili','Sicil'],
        datasets: [{{
            label: 'SASP İstatistik',
            data: [{total_users},{online_users},{sasp_users},{sicil_count}],
            backgroundColor: ['#1abc9c','#2ecc71','#3498db','#e67e22']
        }}]
    }}
}});

const ctx2 = document.getElementById('chart2');
new Chart(ctx2, {{
    type: 'doughnut',
    data: {{
        labels: ['Online','Offline'],
        datasets: [{{
            data: [{online_users},{total_users-online_users}],
            backgroundColor:['#2ecc71','#e74c3c']
        }}]
    }}
}});
</script>

</body>
</html>
"""
    return html

Thread(target=lambda: app.run(host="0.0.0.0", port=8080)).start()

# =====================
# YETKİ
# =====================
def sasp_only():
    async def predicate(interaction: discord.Interaction):
        ids = [r.id for r in interaction.user.roles]
        return SASP_ROLE_ID in ids or AMIR_ROLE_ID in ids
    return app_commands.check(predicate)

# =====================
# READY
# =====================
@bot.event
async def on_ready():
    load_sicil()
    await bot.change_presence(status=discord.Status.idle,
                              activity=discord.Activity(type=discord.ActivityType.watching,
                                                        name="SASP Operations"))
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("🚔 SASP Bot Aktif + Dashboard Online")

# =====================
# LOG
# =====================
async def log(msg):
    ch = bot.get_channel(LOG_CHANNEL_ID)
    if ch: await ch.send(msg)

# =====================
# SICIL
# =====================
@tree.command(name="sicil_ekle", description="Sicile kayıt ekle", guild=discord.Object(id=GUILD_ID))
@sasp_only()
async def sicil_ekle(interaction: discord.Interaction, uye: discord.Member, notu: str):
    sicil.setdefault(str(uye.id), []).append({
        "not": notu,
        "ekleyen": interaction.user.id,
        "tarih": int(time.time())
    })
    save_sicil()
    await interaction.response.send_message("📁 Sicil eklendi")
    await log(f"📁 Sicil: {uye} | {notu}")

@tree.command(name="sicil_gor", description="Sicil görüntüle", guild=discord.Object(id=GUILD_ID))
@sasp_only()
async def sicil_gor(interaction: discord.Interaction, uye: discord.Member):
    kayitlar = sicil.get(str(uye.id), [])
    if not kayitlar:
        return await interaction.response.send_message("Sicil temiz.")
    text = "\n".join([f"- {k['not']}" for k in kayitlar])
    await interaction.response.send_message(f"📁 **{uye} Sicil**\n{text}")

# =====================
bot.run(TOKEN)
