import discord

from common.cfg import Tenor
from ..model.errors import NoVoiceClient, SongError
from ..model.song import Song

class SongModal(discord.ui.DesignerModal):

    def __init__(self, view: discord.ui.BaseView):
        super().__init__(title="Coin Inserted")
        self.view = view
        self.jukebox = view.jukebox

        label = discord.ui.Label("Song Query")
        label.set_input_text(
            style=discord.InputTextStyle.short,
            placeholder="Search query or URL",
            min_length=1,
            max_length=200,
            custom_id="song-modal-input"
        )

        self.add_item(label)

    async def callback(self, interaction: discord.Interaction):

        # no user voice state
        if interaction.user.voice is None:
            return await interaction.response.send_message(Tenor.KERMIT_LOST, ephemeral=True)

        user_vc = interaction.user.voice.channel

        query = self.get_item("song-modal-input").value

        await interaction.response.defer()

        try:
            _ = self.jukebox.voice_client
        except NoVoiceClient:
            await user_vc.connect()

        song = await Song.from_query(query, loop=self.jukebox.voice_client.loop)

        if self.jukebox.current is None:
            self.jukebox.play(song)
            self.jukebox.last_action = f"{interaction.user.display_name} added {song.title}"
        else:
            self.jukebox.enqueue(song)
            self.jukebox.last_action = f"{interaction.user.display_name} queued {song.title}"

        # await interaction.followup.delete()

        self.view.update()
        await interaction.message.edit(view=self.view)

    async def on_error(self, error: Exception, interaction: discord.Interaction):

        if isinstance(error, SongError):
            return await interaction.followup.send("Failed to queue song", ephemeral=True)

        raise error
