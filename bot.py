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
PING_ROLE_ID = None  # Put role ID if you want role ping

TEST_MODE = True
CHECK_INTERVAL = 300

APPLE_BUNDLE_ID = "com.animalcompany.companion"
APPLE_LOOKUP = f"https://itunes.apple.com/lookup?bundleId={APPLE_BUNDLE_ID}"
DECRYPT_URL = "https://decrypt.day/app/id6741173617"

# =========================
# KEEP ALIVE (FOR RENDER WEB SERVICE)
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
update_task_started = False

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
# CLEAN PREMIUM EMBEDS
# =========================

def build_apple_embed(old, new):
    embed = discord.Embed(
        title="🍎 Companion Update Released",
        description="A new version is now live on the **App Store**.",
        color=0x007AFF,
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name="📦 Version",
        value=f"`{old}` ➜ **`{new}`**",
        inline=False
    )

    embed.add_field(
        name="🔗 Download",
        value="[View on App Store](https://apps.apple.com/app/id6741173617)",
        inline=False
    )

    embed.set_footer(text="Animal Companion Tracker • App Store")

    return embed


def build_decrypt_embed(old, new):
    embed = discord.Embed(
        title="🔓 IPA Now Available",
        description="The decrypted IPA is now available.",
        color=0x00C853,
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name="📦 Version",
        value=f"`{old}` ➜ **`{new}`**",
        inline=False
    )

    embed.add_field(
        name="⬇ Download",
        value=f"[Download IPA]({DECRYPT_URL})",
        inline=False
    )

    embed.set_footer(text="Animal Companion Tracker • decrypt.day")

    return embed

# =========================
# COMMANDS
# =========================

@bot.command()
async def test(ctx, type: str):
    if type.lower() == "apple":
        msg = await ctx.send(embed=build_apple_embed("59.0", "60.0"))
    elif type.lower() == "decrypt":
        msg = await ctx.send(embed=build_decrypt_embed("59.0", "60.0"))
    else:
        return await ctx.send("Use: !test apple OR !test decrypt")

    # Auto reactions
    await msg.add_reaction("🚀")
    await msg.add_reaction("🔥")

@bot.command()
async def status(ctx):
    apple_live = get_appstore_version()
    decrypt_live = get_decrypt_version()

    embed = discord.Embed(
        title="📊 Live Version Status",
        color=0x5865F2,
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name="🍎 App Store",
        value=f"`{apple_live or 'Unknown'}`",
        inline=False
    )

    embed.add_field(
        name="🔓 decrypt.day",
        value=f"`{decrypt_live or 'Unknown'}`",
        inline=False
    )

    embed.set_footer(text="Real-time version check")

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def forcecheck(ctx):
    await ctx.send("🔎 Checking now...")
    await run_update_check(force=True)
    await ctx.send("✅ Manual check complete.")

# =========================
# UPDATE LOOP
# =========================

async def send_update(channel, embed):
    if TEST_MODE:
        msg = await channel.send(embed=embed)
    else:
        if PING_ROLE_ID:
            msg = await channel.send(f"<@&{PING_ROLE_ID}>", embed=embed)
        else:
            msg = await channel.send("@everyone", embed=embed)

    # Auto reactions on announcements
    await msg.add_reaction("🚀")
    await msg.add_reaction("🔥")


async def run_update_check(force=False):
    global last_apple_version, last_decrypt_version

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        return

    app_v = get_appstore_version()
    dec_v = get_decrypt_version()

    if app_v:
        if last_apple_version is None:
            last_apple_version = app_v
        elif app_v != last_apple_version or force:
            await send_update(channel, build_apple_embed(last_apple_version, app_v))
            last_apple_version = app_v

    if dec_v:
        if last_decrypt_version is None:
            last_decrypt_version = dec_v
        elif dec_v != last_decrypt_version or force:
            await send_update(channel, build_decrypt_embed(last_decrypt_version, dec_v))
            last_decrypt_version = dec_v


async def check_updates():
    await bot.wait_until_ready()
    while True:
        try:
            await run_update_check()
        except Exception as e:
            print("Update error:", e)

        await asyncio.sleep(CHECK_INTERVAL)

@bot.event
async def on_ready():
    global update_task_started

    print(f"Logged in as {bot.user}")

    if not update_task_started:
        bot.loop.create_task(check_updates())
        update_task_started = True

bot.run(TOKEN)



