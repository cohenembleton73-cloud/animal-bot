print("SCRIPT VERSION 100% NEW")
import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask
import threading

TOKEN = os.getenv("TOKEN")

# =========================
# RENDER KEEP-ALIVE
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

# =========================
# SLASH COMMAND
# =========================

@bot.tree.command(name="test", description="Simple test command")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Bot is responding correctly.")

# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global commands.")
    except Exception as e:
        print("Sync failed:", e)

# =========================
# START
# =========================

bot.run(TOKEN)





