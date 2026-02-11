import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask
import threading

print("SCRIPT VERSION 200% DEBUG")

TOKEN = os.getenv("TOKEN")

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("ON_READY TRIGGERED")
    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global commands.")
    except Exception as e:
        print("SYNC FAILED:", e)

@bot.tree.command(name="test", description="Test command")
async def test(interaction: discord.Interaction):
    print("TEST COMMAND CALLED")
    await interaction.response.send_message("Bot is responding.")

bot.run(TOKEN)





