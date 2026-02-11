import discord
from discord.ext import commands, tasks
import requests
import re
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

# =========================
# SETTINGS
# =========================

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1471171197290152099
CHECK_INTERVAL = 300  # 5 minutes

APPLE_LOOKUP = "https://itunes.apple.com/lookup?id=6741173617"
DECRYPT_URL = "https://decrypt.day/app/id6741173617"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# KEEP ALIVE SERVER (Render)
# =========================

def run_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# =========================
# DISCORD SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True  # REQUIRED for ! commands

bot = commands.Bot(command_prefix="!", intents=intents)

last_apple_version = None
last_decrypt_version = None
initialised = False

# =========================
# VERSION FETCHERS
# =========================

def get_appstore_version():
    try:
        r = requests.get(APPLE_LOOKUP, headers=HEADERS, timeout=10)
        data = r.json()
        if data.get("resultCount", 0) > 0:
            return data["results"][0]["version"]
    except Exception as e:
        print("Apple fetch error:", e)
    return None


def get_decrypt_version():
    try:
        r = requests.get(DECRYPT_URL, headers=HEADERS, timeout=10)
        match = re.search(r"\b\d+\.\d+\.\d+\.\d+\b", r.text)
        if match:
            return match.group(0)
    except Exception as e:
        print("Decrypt fetch error:", e)
    return None

# =========================
# UPDATE LOOP
# =========================

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_updates():
    global last_apple_version, last_decrypt_version, initialised

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    apple_v = get_appstore_version()
    decrypt_v = get_decrypt_version()

    # First run: just cache versions
    if not initialised:
        last_apple_version = apple_v
        last_decrypt_version = decrypt_v
        initialised = True
        print("Initial versions cached.")
        return

    # Apple Update
    if apple_v and apple_v != last_apple_version:
        embed = discord.Embed(
            title="🍎 App Store Updated",
            description=f"New Version: **{apple_v}**",
            color=0x007AFF,
            timestamp=datetime.utcnow()
        )
        embed.add_field(
            name="Download",
            value="https://apps.apple.com/app/id6741173617",
            inline=False
        )
        embed.set_footer(text="Animal Companion Tracker • App Store")

        await channel.send("@everyone", embed=embed)
        last_apple_version = apple_v

    # Decrypt Update
    if decrypt_v and decrypt_v != last_decrypt_version:
        embed = discord.Embed(
            title="🔓 IPA Now Available",
            description=f"New Version: **{decrypt_v}**",
            color=0x00C853,
            timestamp=datetime.utcnow()
        )
        embed.add_field(
            name="Download",
            value=DECRYPT_URL,
            inline=False
        )
        embed.set_footer(text="Animal Companion Tracker • decrypt.day")

        await channel.send("@everyone", embed=embed)
        last_decrypt_version = decrypt_v

# =========================
# STATUS COMMAND
# =========================

@bot.command()
async def status(ctx):
    apple_v = get_appstore_version()
    decrypt_v = get_decrypt_version()

    embed = discord.Embed(
        title="📊 Current Versions",
        color=0x5865F2,
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name="🍎 App Store",
        value=apple_v or "Unavailable",
        inline=False
    )

    embed.add_field(
        name="🔓 decrypt.day",
        value=decrypt_v or "Unavailable",
        inline=False
    )

    await ctx.send(embed=embed)

# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not check_updates.is_running():
        check_updates.start()

# =========================
# START BOT
# =========================

bot.run(TOKEN)









