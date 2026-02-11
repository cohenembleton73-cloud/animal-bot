import discord
import requests
import asyncio
import re
import os
from flask import Flask
import threading

# =========================
# START FLASK FIRST (IMPORTANT)
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Start web server BEFORE Discord
threading.Thread(target=run_web, daemon=True).start()

# =========================
# DISCORD CONFIG
# =========================

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1471171197290152099

APPLE_BUNDLE_ID = "com.animalcompany.companion"
APPLE_LOOKUP = "https://itunes.apple.com/lookup?bundleId=" + APPLE_BUNDLE_ID
DECRYPT_URL = "https://decrypt.day/app/id6741173617"

CHECK_INTERVAL = 300  # 5 minutes

intents = discord.Intents.default()
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
# UPDATE LOOP
# =========================

async def check_updates():
    global last_apple_version, last_decrypt_version
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            # Apple check
            app_v = get_appstore_version()
            if app_v:
                if last_apple_version is None:
                    last_apple_version = app_v
                elif app_v != last_apple_version:
                    await channel.send(
                        f"@everyone 🍎 **Animal Company Companion updated on the App Store!**\n\n"
                        f"Version: V{app_v}\n"
                        f"🔄 decrypt.day release coming soon...\n"
                        f"https://apps.apple.com/app/id6741173617"
                    )
                    last_apple_version = app_v

            # decrypt.day check
            dec_v = get_decrypt_version()
            if dec_v:
                if last_decrypt_version is None:
                    last_decrypt_version = dec_v
                elif dec_v != last_decrypt_version:
                    await channel.send(
                        f"@everyone 🔓 **Animal Company Companion is NOW LIVE on decrypt.day!**\n\n"
                        f"🔥 Version: V{dec_v}\n"
                        f"📥 Download here:\n{DECRYPT_URL}\n\n"
                        f"It’s ready 🚀"
                    )
                    last_decrypt_version = dec_v

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_updates())

client.run(TOKEN)

