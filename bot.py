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

TEST_MODE = True  # False = real @everyone
CHECK_INTERVAL = 300  # 5 minutes

APPLE_BUNDLE_ID = "com.animalcompany.companion"
APPLE_LOOKUP = f"https://itunes.apple.com/lookup?bundleId={APPLE_BUNDLE_ID}"
DECRYPT_URL = "https://decrypt.day/app/id6741173617"

# =========================
# MINIMAL KEEP-ALIVE SERVER (FOR RENDER WEB SERVICE)
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
intents.message_content = True  # Needed for ! commands

bot = commands.Bot(command_prefix="!", intents=intents)

last_apple_version = None
last_decrypt_version = None

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
    embed.add_field(
        name="Version Upgrade",
        value=f"```V{old} ➜ V{new}```",
        inline=False
    )
    embed.add_field(
        name="App Store",
        value="https://apps.apple.com/app/id6741173617",
        inline=False
    )
    return embed

def build_decrypt_embed(old, new):
    embed = discord.Embed(
        title="🔓 IPA Now Live",
        description="Decrypted IPA available",
        color=0x00FF88,
        timestamp=datetime.utcnow()
    )
    embed.add_field(
        name="Version Upgrade",
        value=f"```V{old} ➜ V{new}```",
        inline=False
    )
    embed.add_field(
        name="Download",
        value=DECRYPT_URL,
        inline=False
    )
    return embed

# =========================
# PREFIX COMMANDS
# =========================

@bot.command()
async def test(ctx, type: str):
    if type.lower() == "apple":
        embed = build_apple_embed("59.0", "60.0")
        await ctx.send(embed=embed)

    elif type.lower() == "decrypt":
        embed = build_decrypt_embed("59.0", "60.0")
        await ctx.send(embed=embed)

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

async def check_updates():
    global last_apple_version, last_decrypt_version

    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

    while not bot.is_closed():
        try:
            app_v = get_appstore_version()
            dec_v = get_decrypt_version()

            if app_v:
                if last_apple_version is None:
                    last_apple_version = app_v
                elif app_v != last_apple_version:
                    embed = build_apple_embed(last_apple_version, app_v)
                    if TEST_MODE:
                        await channel.send(embed=embed)
                    else:
                        await channel.send("@everyone", embed=embed)
                    last_apple_version = app_v

            if dec_v:
                if last_decrypt_version is None:
                    last_decrypt_version = dec_v
                elif dec_v != last_decrypt_version:
                    embed = build_decrypt_embed(last_decrypt_version, dec_v)
                    if TEST_MODE:
                        await channel.send(embed=embed)
                    else:
                        await channel.send("@everyone", embed=embed)
                    last_decrypt_version = dec_v

        except Exception as e:
            print("Update error:", e)

        await asyncio.sleep(CHECK_INTERVAL)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(check_updates())

bot.run(TOKEN)







