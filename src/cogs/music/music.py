import shutil

import discord

from .model.jukebox import Jukebox
from .ui.jukebox_view import JukeboxView


class Music(discord.Cog):
    """Handles simple commands and listeners."""

    @discord.slash_command(name="viewtest")
    async def send_testview(self, ctx: discord.ApplicationContext):
        """Send a test view message."""
        await ctx.respond(view=JukeboxView())

    @discord.slash_command(name="jukebox")
    @discord.option(name="fresh", description="Start with a brand new jukebox. Deletes the previous", default=False)
    async def send_jukebox(self, ctx: discord.ApplicationContext, fresh: bool):
        """Get the music player and its buttons."""
        # await ctx.response.defer()

        # stop and remove old jukebox if there is one
        if fresh and (jukebox := Jukebox.instances.get(ctx.guild)):
            jukebox.stop()
            Jukebox.instances.pop(ctx.guild)

        # get or create new jukebox
        jukebox = Jukebox.instances.get(ctx.guild, Jukebox(ctx.guild))
        view = JukeboxView(jukebox)

        await ctx.response.send_message(view=view)
        jukebox.view = view


def setup(bot: discord.Bot):
    """Entry point for loading cogs. Required for all cogs"""

    if shutil.which("ffmpeg") is None:
        raise FileNotFoundError("FFMPEG is not available. Make sure it's added to path")

    bot.add_cog(Music(bot))
