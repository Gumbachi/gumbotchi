import discord

from ..model.enums import JukeboxMode
from .song_modal import SongModal

class AddSongButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="🪙", label="Add song")

    async def callback(self, interaction: discord.Interaction) -> None:
        modal = SongModal(interaction.view)
        await interaction.response.send_modal(modal)

class JukeboxModes(discord.ui.ActionRow):

    def __init__(self, mode: JukeboxMode):
        super().__init__()

        # This works because this Queue and Overview have different instances of this
        if mode == JukeboxMode.Overview:
            button = self.get_item("jukebox-overview")
        else:
            button = self.get_item("jukebox-queue")

        button.style = discord.ButtonStyle.blurple
        button.disabled = True


    @discord.ui.button(emoji="🎧", label="Overview", custom_id="jukebox-overview")
    async def on_overview(self, button: discord.ui.Button, interaction: discord.Interaction):
        ui = self.view
        ui.mode = JukeboxMode.Overview

        ui.update()
        await interaction.response.edit_message(view=ui)

    @discord.ui.button(emoji="📋", label="Queue", custom_id="jukebox-queue")
    async def on_queue(self, button: discord.ui.Button, interaction: discord.Interaction):
        ui = self.view
        ui.mode = JukeboxMode.Queue

        ui.update()
        await interaction.response.edit_message(view=ui)

    @discord.ui.button(emoji="🖼️", label="Cover", custom_id="jukebox-cover")
    async def on_cover(self, button: discord.ui.Button, interaction: discord.Interaction):
        ui = self.view
        ui.previous_mode = ui.mode # Remember the last mode
        ui.mode = JukeboxMode.Cover

        ui.update()
        await interaction.response.edit_message(view=ui)
