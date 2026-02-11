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
PING_ROLE_ID = None  # Put role ID here if you want role ping

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
update_task_started = False  # 🔥 prevents double loop

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
# PREMIUM EMBEDS
# =========================

def build_apple_embed(old, new):
    embed = discord.Embed(
        title="🍎 Companion Update Released",
        description="A new version is now live on the App Store.",
        color=0x1DA1F2,
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name="📦 Version",
        value=f"**{old} → {new}**",
        inline=False
    )

    embed.add_field(
        name="🔗 Download",
        value="[View on App Store](https://apps.apple.com/app/id6741173617)",
        inline=False
    )

    embed.set_footer(text="Animal Companion Update Tracker")
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/732/732208.png")

    return embed


def build_decrypt_embed(old, new):
    embed = discord.Embed(
        title="🔓 IPA Now Available",
        description="The decrypted IPA is now ready.",
        color=0x00FF88,
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name="📦 Version",
        value=f"**{old} → {new}**",
        inline=False
    )

    embed.add_field(
        name="⬇ Download",
        value=f"[Download IPA]({DECRYPT_URL})",
        inline=False
    )

    embed.set_footer(text="Animal Companion Update Tracker")
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/833/833314.png")

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
    await ctx.send(
        f"📊 Current Versions:\n"
        f"Apple: {last_apple_version}\n"
        f"decrypt.day: {last_decrypt_version}"
    )

# =========================
# UPDATE LOOP
# =========================

async def run_update_check():
    global last_apple_version, last_decrypt_version

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        return

    app_v = get_appstore_version()
    dec_v = get_decrypt_version()

    # Apple
    if app_v:
        if last_apple_version is None:
            last_apple_version = app_v
        elif app_v != last_apple_version:
            embed = build_apple_embed(last_apple_version, app_v)
            await send_update(channel, embed)
            last_apple_version = app_v

    # Decrypt
    if dec_v:
        if last_decrypt_version is None:
            last_decrypt_version = dec_v
        elif dec_v != last_decrypt_version:
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






