import discord

from ..model.jukebox import Jukebox

class CoverBackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Back")

    async def callback(self, interaction: discord.Interaction) -> None:
        ui = interaction.view
        ui.mode = ui.previous_mode
        ui.update()
        await interaction.response.edit_message(view=ui)

class CoverContainer(discord.ui.Container):

    def __init__(self, jukebox: Jukebox):
        super().__init__()

        section = discord.ui.Section()
        if jukebox.current:
            song = discord.ui.TextDisplay(f"**{jukebox.current.title}**")
            artist = discord.ui.TextDisplay(f"{jukebox.current.duration}")
            url = jukebox.current.thumbnail
        else:
            song = discord.ui.TextDisplay("**Nothing playing**")
            artist = discord.ui.TextDisplay("Why are you even here?")
            url = "https://files.gumbachi.com/assets/add-song.jpg"

        section = discord.ui.Section(song, artist, accessory=CoverBackButton())

        gallery = discord.ui.MediaGallery()
        gallery.add_item(url)

        self.add_item(section)
        self.add_item(gallery)
