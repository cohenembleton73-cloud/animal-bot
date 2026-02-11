import discord
from discord.ext import commands
import requests
import asyncio
import re
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1471171197290152099
PING_ROLE_ID = None  # 🔥 Put role ID here if you want role ping (or leave None)

TEST_MODE = True
CHECK_INTERVAL = 300

APPLE_BUNDLE_ID = "com.animalcompany.companion"
APPLE_LOOKUP = f"https://itunes.apple.com/lookup?bundleId={APPLE_BUNDLE_ID}"
DECRYPT_URL = "https://decrypt.day/app/id6741173617"

# =========================
# KEEP ALIVE SERVER
# =========================

def run_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# =========================
# DISCORD SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

last_apple_version = None
last_decrypt_version = None
last_checked = None
bot_start_time = datetime.utcnow()

# =========================
# VERSION FETCHERS
# =========================

def get_appstore_version():
    try:
        r = requests.get(APPLE_LOOKUP, timeout=10)
        data = r.json()
        if data["resultCount"] > 0:
            return data["results"][0]["version"]
    except:
        return None
    return None

def get_decrypt_version():
    try:
        r = requests.get(DECRYPT_URL, timeout=10)
        text = r.text
        match = re.search(r"Version[: ]*([0-9A-Za-z\.\-]+)", text)
        if match:
            return match.group(1).strip()
    except:
        return None
    return None

# =========================
# EMBEDS
# =========================

def build_apple_embed(old, new):
    embed = discord.Embed(
        title="🍎 App Store Update Detected",
        description="Animal Company Companion",
        color=0x1DA1F2,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Version Upgrade", value=f"```V{old} ➜ V{new}```", inline=False)
    embed.add_field(name="App Store", value="https://apps.apple.com/app/id6741173617", inline=False)
    return embed

def build_decrypt_embed(old, new):
    embed = discord.Embed(
        title="🔓 IPA Now Live",
        description="Decrypted IPA available",
        color=0x00FF88,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Version Upgrade", value=f"```V{old} ➜ V{new}```", inline=False)
    embed.add_field(name="Download", value=DECRYPT_URL, inline=False)
    return embed

# =========================
# COMMANDS
# =========================

@bot.command()
async def test(ctx, type: str):
    if type.lower() == "apple":
        await ctx.send(embed=build_apple_embed("59.0", "60.0"))
    elif type.lower() == "decrypt":
        await ctx.send(embed=build_decrypt_embed("59.0", "60.0"))
    else:
        await ctx.send("Use: !test apple OR !test decrypt")

@bot.command()
async def status(ctx):
    embed = discord.Embed(
        title="📊 Tracker Status",
        color=0x5865F2,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Apple Version", value=last_apple_version or "Unknown", inline=False)
    embed.add_field(name="Decrypt Version", value=last_decrypt_version or "Unknown", inline=False)

    uptime = datetime.utcnow() - bot_start_time
    embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=False)

    if last_checked:
        embed.add_field(name="Last Checked", value=last_checked.strftime("%H:%M:%S UTC"), inline=False)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def forcecheck(ctx):
    await ctx.send("🔎 Checking now...")
    await run_update_check(force=True)
    await ctx.send("✅ Manual check complete.")

@bot.command()
async def uptime(ctx):
    uptime = datetime.utcnow() - bot_start_time
    await ctx.send(f"⏱ Uptime: {str(uptime).split('.')[0]}")

# =========================
# UPDATE LOOP
# =========================

async def run_update_check(force=False):
    global last_apple_version, last_decrypt_version, last_checked

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found.")
        return

    last_checked = datetime.utcnow()

    app_v = get_appstore_version()
    dec_v = get_decrypt_version()

    if app_v:
        if last_apple_version is None:
            last_apple_version = app_v
        elif app_v != last_apple_version or force:
            embed = build_apple_embed(last_apple_version, app_v)
            await send_update(channel, embed)
            last_apple_version = app_v

    if dec_v:
        if last_decrypt_version is None:
            last_decrypt_version = dec_v
        elif dec_v != last_decrypt_version or force:
            embed = build_decrypt_embed(last_decrypt_version, dec_v)
            await send_update(channel, embed)
            last_decrypt_version = dec_v

async def send_update(channel, embed):
    if TEST_MODE:
        await channel.send(embed=embed)
    else:
        if PING_ROLE_ID:
            await channel.send(f"<@&{PING_ROLE_ID}>", embed=embed)
        else:
            await channel.send("@everyone", embed=embed)

async def check_updates():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            await run_update_check()
        except Exception as e:
            print("Update error:", e)
        await asyncio.sleep(CHECK_INTERVAL)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(check_updates())

bot.run(TOKEN)




