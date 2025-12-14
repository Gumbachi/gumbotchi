"""Runs the discord bot"""
import os

import discord

# Create bot based on environment
if os.getenv("DEBUG") is not None:
    print("DEBUG ENVIRONMENT")
    bot = discord.Bot(
        owner_id=128595549975871488,
        intents=discord.Intents.all(),
        debug_guilds=[565257922356051973]
    )
else:
    print("LIVE ENVIRONMENT")
    bot = discord.Bot(
        owner_id=128595549975871488,
        intents=discord.Intents.all(),
    )


@bot.listen()
async def on_ready() -> None:
    """Bot is now ready to rumble."""
    print("Ready to go.")

# .py files to load up
cogs = [
    "cogs.general.general",
    "cogs.pog.pog",
    "cogs.roast.roast",
    "cogs.games.rps.rps",
    "cogs.games.tictactoe.tictactoe",
    "cogs.games.connectfour.connectfour",
    "cogs.music.music",
    # "cogs.sbonks.sbonks"
]

if __name__ == '__main__':

    # Load opus manually if necessary (NixOS)
    if libopus := os.getenv("OPUS"):
        discord.opus.load_opus(libopus)

    bot.load_extensions(*cogs)
    bot.run(os.getenv("TOKEN"))  # runs the bot
