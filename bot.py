import discord
import requests
import asyncio
import re
import os
from flask import Flask
import threading

# =========================
# SETTINGS
# =========================

TEST_MODE = True  # 🔔 Set to False when you want real @everyone pings

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1471171197290152099

APPLE_BUNDLE_ID = "com.animalcompany.companion"
APPLE_LOOKUP = "https://itunes.apple.com/lookup?bundleId=" + APPLE_BUNDLE_ID
DECRYPT_URL = "https://decrypt.day/app/id6741173617"

CHECK_INTERVAL = 300  # 5 minutes

# =========================
# RENDER PORT FIX
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

# =========================
# DISCORD SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

last_apple_version = None
last_decrypt_version = None

# =========================
# VERSION FUNCTIONS
# =========================

def get_appstore_version():
    try:
        response = requests.get(APPLE_LOOKUP)
        data = response.json()
        if data["resultCount"] > 0:
            return data["results"][0]["version"]
    except:
        return None
    return None

def get_decrypt_version():
    try:
        r = requests.get(DECRYPT_URL)
        text = r.text
        match = re.search(r"Version[: ]*([0-9A-Za-z\.\-]+)", text)
        if match:
            return match.group(1).strip()
    except:
        return None
    return None

# =========================
# EMBED BUILDERS
# =========================

def build_apple_embed(old, new):
    embed = discord.Embed(
        title="🍎 App Store Update Detected",
        description=f"**Animal Company Companion**",
        color=0x00B2FF
    )
    embed.add_field(name="Version Change", value=f"V{old} → V{new}", inline=False)
    embed.add_field(name="Status", value="🔄 decrypt.day release coming soon...", inline=False)
    embed.add_field(name="App Store", value="https://apps.apple.com/app/id6741173617", inline=False)
    embed.set_footer(text="Animal Update Tracker")
    return embed

def build_decrypt_embed(old, new):
    embed = discord.Embed(
        title="🔓 NOW LIVE ON DECRYPT.DAY",
        description="Download is officially available 🚀",
        color=0x00FF66
    )
    embed.add_field(name="Version Change", value=f"V{old} → V{new}", inline=False)
    embed.add_field(name="Download", value=DECRYPT_URL, inline=False)
    embed.set_footer(text="Animal Update Tracker")
    return embed

# =========================
# UPDATE LOOP
# =========================

async def check_updates():
    global last_apple_version, last_decrypt_version
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            app_v = get_appstore_version()
            if app_v:
                if last_apple_version is None:
                    last_apple_version = app_v
                elif app_v != last_apple_version:
                    embed = build_apple_embed(last_apple_version, app_v)
                    if TEST_MODE:
                        await channel.send("🧪 TEST MODE (No ping)", embed=embed)
                    else:
                        await channel.send("@everyone", embed=embed)
                    last_apple_version = app_v

            dec_v = get_decrypt_version()
            if dec_v:
                if last_decrypt_version is None:
                    last_decrypt_version = dec_v
                elif dec_v != last_decrypt_version:
                    embed = build_decrypt_embed(last_decrypt_version, dec_v)
                    if TEST_MODE:
                        await channel.send("🧪 TEST MODE (No ping)", embed=embed)
                    else:
                        await channel.send("@everyone", embed=embed)
                    last_decrypt_version = dec_v

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(CHECK_INTERVAL)

# =========================
# COMMANDS
# =========================

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content == "!test apple":
        embed = build_apple_embed("59.0", "60.0")
        await message.channel.send("🧪 Apple Preview", embed=embed)

    if message.content == "!test decrypt":
        embed = build_decrypt_embed("59.0", "60.0")
        await message.channel.send("🧪 decrypt.day Preview", embed=embed)

    if message.content == "!status":
        await message.channel.send(
            f"📊 Current Stored Versions:\n"
            f"Apple: {last_apple_version}\n"
            f"decrypt.day: {last_decrypt_version}"
        )

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_updates())

client.run(TOKEN)

