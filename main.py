import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from pymongo import MongoClient

load_dotenv()
TOKEN = os.getenv("TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.mongo = MongoClient(MONGO_URI)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()  # Global sync (takes up to 1 hour to propagate)
        print(f"Globally synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Command sync failed: {e}")

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    await load_cogs()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

