import discord
from discord.ext import commands
from discord import app_commands
import os

print("BOT STARTING CLEAN VERSION")

TOKEN = os.getenv("TOKEN")

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
    await interaction.response.send_message("Bot is responding properly.")

bot.run(TOKEN)






