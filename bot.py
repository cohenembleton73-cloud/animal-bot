import discord
from discord.ext import commands, tasks
import requests
import re
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1471171197290152099
PING_ROLE_ID = None  # Add role ID if needed

TEST_MODE = True
CHECK_INTERVAL = 300  # 5 minutes

APPLE_BUNDLE_ID = "com.animalcompany.companion"
APPLE_LOOKUP = f"https://itunes.apple.com/lookup?bundleId={APPLE_BUNDLE_ID}"
DECRYPT_URL = "https://decrypt.day/app/id6741173617"

# =========================
# RENDER KEEP ALIVE
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
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

last_apple_version = None
last_decrypt_version = None
initialised = False

# =========================
# FETCHERS
# =========================

def get_appstore_version():
    try:
        r = requests.get(APPLE_LOOKUP, timeout=10)
        data = r.json()
        if data["resultCount"] > 0:
            return data["results"][0]["version"]
    except:
        return None

def get_decrypt_version():
    try:
        r = requests.get(DECRYPT_URL, timeout=10)
        match = re.search(r"Version[: ]*([0-9A-Za-z\.\-]+)", r.text)
        if match:
            return match.group(1).strip()
    except:
        return None

# =========================
# EMBEDS
# =========================

def apple_embed(old, new):
    embed = discord.Embed(
        title="🍎 Companion Update Released",
        description="New version live on the App Store.",
        color=0x007AFF,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Version", value=f"`{old}` ➜ **`{new}`**", inline=False)
    embed.add_field(
        name="Download",
        value="[View on App Store](https://apps.apple.com/app/id6741173617)",
        inline=False
    )
    embed.set_footer(text="Animal Companion Tracker • App Store")
    return embed

def decrypt_embed(old, new):
    embed = discord.Embed(
        title="🔓 IPA Now Available",
        description="Decrypted IPA is now available.",
        color=0x00C853,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Version", value=f"`{old}` ➜ **`{new}`**", inline=False)
    embed.add_field(
        name="Download",
        value=f"[Download IPA]({DECRYPT_URL})",
        inline=False
    )
    embed.set_footer(text="Animal Companion Tracker • decrypt.day")
    return embed

# =========================
# UPDATE LOOP (SAFE VERSION)
# =========================

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_updates():
    global last_apple_version, last_decrypt_version, initialised

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    apple_v = get_appstore_version()
    decrypt_v = get_decrypt_version()

    # First run → just store versions, don't send
    if not initialised:
        last_apple_version = apple_v
        last_decrypt_version = decrypt_v
        initialised = True
        print("Initial version cache set.")
        return

    # Apple Update
    if apple_v and apple_v != last_apple_version:
        embed = apple_embed(last_apple_version, apple_v)
        msg = await channel.send(embed=embed)
        await msg.add_reaction("🚀")
        await msg.add_reaction("🔥")
        last_apple_version = apple_v

    # Decrypt Update
    if decrypt_v and decrypt_v != last_decrypt_version:
        embed = decrypt_embed(last_decrypt_version, decrypt_v)
        msg = await channel.send(embed=embed)
        await msg.add_reaction("🚀")
        await msg.add_reaction("🔥")
        last_decrypt_version = decrypt_v

# =========================
# COMMANDS
# =========================

@bot.command()
async def status(ctx):
    apple_v = get_appstore_version()
    decrypt_v = get_decrypt_version()

    embed = discord.Embed(
        title="📊 Live Version Status",
        color=0x5865F2,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="🍎 App Store", value=f"`{apple_v or 'Unknown'}`", inline=False)
    embed.add_field(name="🔓 decrypt.day", value=f"`{decrypt_v or 'Unknown'}`", inline=False)
    embed.set_footer(text="Real-time version check")

    await ctx.send(embed=embed)

@bot.command()
async def forcecheck(ctx):
    await ctx.send("Checking manually...")
    await check_updates()
    await ctx.send("Manual check complete.")

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not check_updates.is_running():
        check_updates.start()

bot.run(TOKEN)




