import discord
from discord.ext import commands
from discord import app_commands
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = os.getenv("TOKEN")

# Minimal HTTP server for Render
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

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands.")

@bot.tree.command(name="test", description="Test command")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Bot is responding properly.")

bot.run(TOKEN)








