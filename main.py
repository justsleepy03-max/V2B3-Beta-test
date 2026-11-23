import asyncio
import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
SLEEPYS_LAB_GUILD_ID = 1574424192307175494
DATA_DIR = "/app/data" if os.path.isdir("/app/data") else "./lab_data"
os.makedirs(DATA_DIR, exist_ok=True)

COGS = [
    "dungeon_boss_cog",
    "bag_cog",
    "shop_cog",
    "area_cog",
    "quest_cog",
]


class V2B3Bot(commands.Bot):

  def __init__(self):
    intents = discord.Intents.default()
    intents.message_content = True
    super().__init__(command_prefix="!", intents=intents)

  async def setup_hook(self):
    for cog in COGS:
      await self.load_extension(cog)

    guild = discord.Object(id=SLEEPYS_LAB_GUILD_ID)
    self.tree.copy_global_to(guild=guild)
    synced = await self.tree.sync(guild=guild)
    print(f"Instantly synced {len(synced)} commands to Sleepys Lab ({SLEEPYS_LAB_GUILD_ID})!")

  async def on_ready(self):
    print(f"Logged in as {self.user} (ID: {self.user.id})")
    print("V2B3 Lab engine is fully online!")


async def main():
  if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN environment variable for V2B3.")
  bot = V2B3Bot()
  async with bot:
    await bot.start(TOKEN)


if __name__ == "__main__":
  asyncio.run(main())
