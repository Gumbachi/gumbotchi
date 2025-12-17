from typing import Self

import discord

from .enums import RepeatMode
from .errors import NoVoiceClient
from .song import Song


class Jukebox:

    instances: dict[discord.Guild, Self] = {}

    def __init__(self, guild: discord.Guild):
        self.guild = guild

        self.current: Song | None = None
        self.queue: list[Song] = []
        self.history: list[Song] = []

        self.repeat = RepeatMode.RepeatOff
        self.shuffle = False

        self.last_action = "Vibe Established"

        self.view: discord.ui.DesignerView | None = None

        self.instances[guild] = self

    @property
    def voice_client(self) -> discord.VoiceClient:
        """Fetch the voice client for the guild associated with the player."""
        vcc = self.guild.voice_client
        if isinstance(vcc, discord.VoiceClient):
            return vcc

        raise NoVoiceClient("Voice Client Not Found")

    def play(self, song: Song):
        """Play the provided song."""
        self.current = song

        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.source = song
        else:
            self.voice_client.play(song, after=self.play_next_song)

    async def stop(self) -> None:
        """Stop the jukebox from playing and disconnect. Doesn't destroy the jukebox."""

        self.current = None

        try:
            self.view.update()
            self.voice_client.loop.create_task(self.view.message.edit(view=self.view))
            self.voice_client.stop()
            await self.voice_client.disconnect()
        except NoVoiceClient:
            pass


    def enqueue(self, song: Song):
        """Add a song to the queue."""
        self.queue.append(song)

    # async def disconnect(self):
    #     """Disconnect the bot"""
    #     await self.voice_client.disconnect()

    def play_next_song(self, error: Exception | None = None):
        """CANT BE ASYNC. Load the next song into the current song based on repeat type"""
        print(f"PLAY NEXT ENTERED: {error=}")

        if error:
            print(f"{type(error)}, {error}")

        if self.current is not None:
            # dont add duplicates
            if self.current.title not in [s.title for s in self.history]:
                self.history.insert(0, self.current.clone())


        # No more songs in the queue
        if self.repeat == RepeatMode.RepeatOff and not self.queue:
            self.voice_client.loop.create_task(self.stop())
            return


        if self.repeat == RepeatMode.RepeatOne:
            self.play(self.current.clone())
        elif self.repeat == RepeatMode.Repeat:
            self.enqueue(self.current.clone())
            self.play(self.queue.pop(0))
        else:
            self.play(self.queue.pop(0))


        # Update message for new song
        self.view.update()
        self.voice_client.loop.create_task(self.view.message.edit(view=self.view))


    # async def interaction_check(self, interaction: discord.Interaction) -> bool:
    #     """Try to ensure the bot cannot be griefed"""

    #     # User not in voice channel
    #     if not interaction.user.voice:
    #         await interaction.response.send_message(
    #             content="Gotta be in a voice channel to listen to music",
    #             ephemeral=True
    #         )
    #         return False

    #     try:
    #         vcc = self.voice_client
    #     except NoVoiceClient:
    #         return True

    #     if interaction.user.voice.channel != vcc.channel:
    #         await interaction.response.send_message(
    #             content="Trying to steal the bot are we?",
    #             ephemeral=True
    #         )
    #         return False

    #     return True
