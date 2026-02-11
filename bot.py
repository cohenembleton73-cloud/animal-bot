import discord
from discord.ext import commands
from discord import app_commands
import requests
import asyncio
import re
import os
from flask import Flask
import threading
from datetime import datetime, UTC

# =========================
# SETTINGS
# =========================

TEST_MODE = True  # Set False for real @everyone

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1471171197290152099
GUILD_ID = 1471171197290152099  # OPTIONAL: put your server ID here for instant slash sync

APPLE_BUNDLE_ID = "com.animalcompany.companion"
APPLE_LOOKUP = f"https://itunes.apple.com/lookup?bundleId={APPLE_BUNDLE_ID}"
DECRYPT_URL = "https://decrypt.day/app/id6741173617"

CHECK_INTERVAL = 300  # 5 minutes

# =========================
# RENDER WEB SERVER (KEEP ALIVE)
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
bot = commands.Bot(command_prefix="!", intents=intents)

last_apple_version = None
last_decrypt_version = None
bot_start_time = datetime.now(UTC)

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
        title="🍎 Companion IPA Update Detected",
        description="**Animal Company Companion**",
        color=0x1DA1F2,
        timestamp=datetime.now(UTC)
    )
    embed.add_field(
        name="📦 Version Upgrade",
        value=f"```V{old} ➜ V{new}```",
        inline=False
    )
    embed.add_field(
        name="🔗 App Store",
        value="https://apps.apple.com/app/id6741173617",
        inline=False
    )
    embed.set_footer(text="Animal Companion Update Tracker")
    return embed

def build_decrypt_embed(old, new):
    embed = discord.Embed(
        title="🔓 IPA Now Live",
        description="The decrypted IPA is officially available 🚀",
        color=0x00FF88,
        timestamp=datetime.now(UTC)
    )
    embed.add_field(
        name="📦 Version Upgrade",
        value=f"```V{old} ➜ V{new}```",
        inline=False
    )
    embed.add_field(
        name="🚀 Download",
        value=DECRYPT_URL,
        inline=False
    )
    embed.set_footer(text="Animal Companion Update Tracker")
    return embed

# =========================
# SLASH COMMANDS
# =========================

@bot.tree.command(name="test", description="Simulate an update embed")
@app_commands.describe(type="Choose which update to simulate")
@app_commands.choices(type=[
    app_commands.Choice(name="Apple", value="apple"),
    app_commands.Choice(name="Decrypt", value="decrypt")
])
async def test(interaction: discord.Interaction, type: app_commands.Choice[str]):

    if type.value == "apple":
        embed = build_apple_embed("59.0", "60.0")
        await interaction.response.send_message(embed=embed)

    elif type.value == "decrypt":
        embed = build_decrypt_embed("59.0", "60.0")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="status", description="Check current tracked versions")
async def status(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📊 Tracker Status",
        color=0x5865F2,
        timestamp=datetime.now(UTC)
    )
    embed.add_field(name="Apple Version", value=last_apple_version or "Unknown", inline=False)
    embed.add_field(name="Decrypt Version", value=last_decrypt_version or "Unknown", inline=False)

    uptime = datetime.now(UTC) - bot_start_time
    embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="forcecheck", description="Manually check for updates")
async def forcecheck(interaction: discord.Interaction):

    await interaction.response.defer()

    await run_update_check(force=True)

    await interaction.followup.send("✅ Manual check completed.")

# =========================
# UPDATE LOOP
# =========================

async def run_update_check(force=False):
    global last_apple_version, last_decrypt_version

    channel = bot.get_channel(CHANNEL_ID)

    app_v = get_appstore_version()
    dec_v = get_decrypt_version()

    # Apple
    if app_v:
        if last_apple_version is None:
            last_apple_version = app_v
        elif app_v != last_apple_version or force:
            embed = build_apple_embed(last_apple_version, app_v)
            if TEST_MODE:
                await channel.send(embed=embed)
            else:
                await channel.send("@everyone", embed=embed)
            last_apple_version = app_v

    # Decrypt
    if dec_v:
        if last_decrypt_version is None:
            last_decrypt_version = dec_v
        elif dec_v != last_decrypt_version or force:
            embed = build_decrypt_embed(last_decrypt_version, dec_v)
            if TEST_MODE:
                await channel.send(embed=embed)
            else:
                await channel.send("@everyone", embed=embed)
            last_decrypt_version = dec_v


async def check_updates():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            await run_update_check()
        except Exception as e:
            print("Update loop error:", e)

        await asyncio.sleep(CHECK_INTERVAL)

# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print("Sync error:", e)

    bot.loop.create_task(check_updates())

# =========================
# START
# =========================

bot.run(TOKEN)





