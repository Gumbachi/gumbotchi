from typing import Self
import asyncio

import discord

import common.utils as utils
from .enums import RepeatMode, JukeboxMode
from .song import Song

class Jukebox:

    instances: dict[discord.Guild, Self] = {}
    progress_characters = 18
    max_queue = 60

    def __init__(self, guild: discord.Guild):
        self.guild = guild

        self.current: Song | None = None
        self.queue: list[Song] = []
        self.history: list[Song] = []

        self.repeat = RepeatMode.RepeatOff
        self.shuffle = False

        self.last_action = "Vibe Established"
        self.page = 0

        self.view: discord.ui.DesignerView | None = None

        # This value represent the time elapsed by voice client
        # not including the currently playing song
        self.elapsed_delta: int = 0

        self.instances[guild] = self

    @property
    def next_up(self) -> Song | None:
        """Calculate the next up song based on repeat/shuffle etc."""
        if self.current is None:
            return None

        if not self.queue and self.repeat == RepeatMode.RepeatOff:
            return None

        if self.repeat == RepeatMode.RepeatOne:
            return self.current

        if not self.queue and self.repeat == RepeatMode.Repeat:
            return self.current

        return self.queue[0]

    @property
    def duration_bar(self) -> str:
        """Renders a duration bar based on tradition."""
        if not self.current:
            return "-----------"

        try:
            elapsed = self.voice_client.elapsed().seconds - self.elapsed_delta
        except AttributeError:
            elapsed = 0

        # Calculate how many ⌃ will be needed
        elapsed_chars = int(elapsed / self.current.duration_in_seconds * self.progress_characters)
        non_elapsed_chars = self.progress_characters - elapsed_chars

        elapsed_fmt = utils.format_duration(elapsed)
        song_duration_fmt = utils.format_duration(self.current.duration_in_seconds)

        squiggly = ("◠◡" * self.progress_characters)[:elapsed_chars]
        not_squiggly = '―' * non_elapsed_chars

        return f"`{elapsed_fmt}` `{squiggly}◯{not_squiggly}` `{song_duration_fmt}`"

    @property
    def voice_client(self) -> discord.VoiceClient | None:
        """Fetch the voice client for the guild associated with the player."""
        return self.guild.voice_client

    async def connect(self, channel: discord.VoiceChannel) -> discord.VoiceClient:
        """Connect to voice channel and begin update loop for playing a song."""
        client = await channel.connect()
        loop = client.loop
        loop.create_task(self.update_loop())
        return client

    async def update_loop(self):
        """Update the jukebox while a song is playing."""
        while self.voice_client and self.view:

            # Calculate sleep interval based on if there will be visual change
            if self.current:
                interval = self.current.duration_in_seconds // self.progress_characters
                assert interval != 0

                # Prevent short interval by doubling until greater than baseline
                original_interval = interval
                while interval < 8:
                    interval += original_interval
            else:
                interval = 10

            await asyncio.sleep(interval)
            if (self.voice_client
                and self.voice_client.is_playing()
                and self.view.mode != JukeboxMode.Queue # Queue screen doesnt need updates
            ):
                self.view.update()
                await self.view.message.edit(view=self.view)

    def play(self, song: Song):
        """Play the provided song."""
        self.current = song

        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.source = song
        else:
            self.voice_client.play(song, after=self.play_next_song)

        try:
            self.elapsed_delta += self.voice_client.elapsed().seconds
        except AttributeError:
            pass

    async def stop(self) -> None:
        """Stop the jukebox from playing and disconnect. Doesn't destroy the jukebox."""

        self.current = None

        if self.voice_client:
            self.view.update()
            self.voice_client.loop.create_task(self.view.message.edit(view=self.view))
            self.voice_client.stop()
            await self.voice_client.disconnect()
            self.elapsed_delta = 0

    def enqueue(self, song: Song):
        """Add a song to the queue."""
        self.queue.append(song)

    def play_next_song(self, error: Exception | None = None):
        """CANT BE ASYNC. Load the next song into the current song based on repeat type"""

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
