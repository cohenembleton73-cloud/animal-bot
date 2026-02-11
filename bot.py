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

CHECK_INTERVAL = 300  # 5 minutes

APPLE_BUNDLE_ID = "com.animalcompany.companion"
APPLE_LOOKUP = f"https://itunes.apple.com/lookup?bundleId={APPLE_BUNDLE_ID}"
DECRYPT_URL = "https://decrypt.day/app/id6741173617"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

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
# DISCORD SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

last_apple_version = None
last_decrypt_version = None
initialised = False

# =========================
# VERSION FETCHERS
# =========================

APPLE_LOOKUP = "https://itunes.apple.com/lookup?id=6741173617"


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

        # Match the Version label specifically
        match = re.search(r"Version\s*</[^>]+>\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", r.text)

        if match:
            return match.group(1)

        print("Decrypt version not found near label.")
    except Exception as e:
        print("Decrypt fetch error:", e)

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
# UPDATE LOOP (SAFE)
# =========================

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_updates():
    global last_apple_version, last_decrypt_version, initialised

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    apple_v = get_appstore_version()
    decrypt_v = get_decrypt_version()

    # First run: cache only
    if not initialised:
        last_apple_version = apple_v
        last_decrypt_version = decrypt_v
        initialised = True
        print("Initial version cache set.")
        return

    # Apple update
    if apple_v and apple_v != last_apple_version:
        embed = apple_embed(last_apple_version, apple_v)
        msg = await channel.send(embed=embed)
        await msg.add_reaction("🚀")
        await msg.add_reaction("🔥")
        last_apple_version = apple_v

    # Decrypt update
    if decrypt_v and decrypt_v != last_decrypt_version:
        embed = decrypt_embed(last_decrypt_version, decrypt_v)
        msg = await channel.send(embed=embed)
        await msg.add_reaction("🚀")
        await msg.add_reaction("🔥")
        last_decrypt_version = decrypt_v

# =========================
# COMMANDS
# =========================

from discord.ext.commands import cooldown, BucketType

@bot.command()
@cooldown(3, 5, BucketType.channel)  # max 3 uses per 5 seconds per channel
async def status(ctx):

    apple_v = get_appstore_version()
    decrypt_v = get_decrypt_version()

    embed = discord.Embed(
        title="📊 Live Version Status",
        color=0x5865F2,
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name="🍎 App Store",
        value=f"`{apple_v or 'Unavailable'}`",
        inline=False
    )

    embed.add_field(
        name="🔓 decrypt.day",
        value=f"`{decrypt_v or 'Unavailable'}`",
        inline=False
    )

    embed.set_footer(text="Real-time version check")

    await ctx.send(embed=embed)


# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"BOT STARTED INSTANCE: {bot.user}")
    if not check_updates.is_running():
        check_updates.start()

bot.run(TOKEN)









