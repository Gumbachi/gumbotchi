from queue import Queue
from typing import Self

import discord

import common.utils as utils
from common.cfg import Tenor

from .enums import RepeatType
from .errors import NoVoiceClient
from .song import Song
# from ..ui.song_modal import SongModal


class Jukebox:

    instances: dict[discord.Guild, Self] = {}

    def __init__(self, guild: discord.Guild):
        self.guild = guild

        self.queue: Queue[Song] = []
        self.history: list[Song] = []
        self.repeat = RepeatType.REPEATOFF
        self.current: Song | None = None
        self.description = "Primed and ready"
        self.footer = ""

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
            self.update_play_buttons()

    def stop(self) -> None:
        """Stop the jukebox from playing"""

        self.current = None

        try:
            self.voice_client.stop()
        except NoVoiceClient:
            pass

        self.update_play_buttons()

        try:
            self.disconnect()
        except NoVoiceClient:
            pass


    def enqueue(self, song: Song):
        """Add a song to the queue."""
        self.queue.append(song)
        self.update_page_buttons()

    def disconnect(self):
        """Disconnect the bot"""
        self.voice_client.loop.create_task(self.voice_client.disconnect())

    def play_next_song(self, error: Exception | None = None):
        """Load the next song into the current song based on repeat type"""

        print(f"PLAY NEXT ENTERED: {error=}")

        if error:
            print(f"{type(error)}, {error}")

        if self.current is not None:
            # dont add duplicates
            if self.current.title not in [s.title for s in self.history]:
                self.history.insert(0, self.current.clone())

            self.update_history_select()

        match self.repeat:
            case RepeatType.REPEATOFF:
                if self.queue:
                    self.play(self.queue.pop(0))
                else:
                    self.stop()
            case RepeatType.REPEAT:
                self.enqueue(self.current.clone())
                self.play(self.queue.pop(0))
            case RepeatType.REPEATONE:
                if self.current is not None:
                    self.play(self.current.clone())

        self.update_page_buttons()

        self.voice_client.loop.create_task(
            self.message.edit(embed=self.embed, view=self)
        )

    @discord.ui.select(
        placeholder="Queue a song from history...",
        options=[
            discord.SelectOption(
                label="PLACEHOLDER",
                description="You found an easter egg"
            )
        ],
        disabled=True
    )
    async def history_select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):

        if interaction.user.voice is None:
            return await interaction.response.send_message(Tenor.KERMIT_LOST, ephemeral=True)

        await interaction.response.defer()

        vc = interaction.user.voice.channel

        try:
            _ = self.voice_client
        except NoVoiceClient:
            await vc.connect()

        # select the song
        for song in self.history:
            if song.title == select.values[0]:
                song_to_play = song
                break
        else:
            song_to_play = await Song.from_query(select.values[0], loop=self.voice_client.loop)

        if self.current is None:
            self.play(song_to_play.clone())
            self.description = f"{interaction.user.name} got this party started with {song.title}"
        else:
            self.enqueue(song_to_play.clone())
            self.description = f"{interaction.user.display_name} queued {song.title}"

        await interaction.edit_original_response(embed=self.embed, view=self)

    @discord.ui.button(emoji="🔁", row=1)
    async def repeat_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Repeat button cycles repeat type for the jukebox"""
        match self.repeat:
            case RepeatType.REPEATOFF:
                self.repeat = RepeatType.REPEAT
                button.style = discord.ButtonStyle.green
            case RepeatType.REPEAT:
                self.repeat = RepeatType.REPEATONE
                button.emoji = "🔂"
            case RepeatType.REPEATONE:
                self.repeat = RepeatType.REPEATOFF
                button.emoji = "🔁"
                button.style = discord.ButtonStyle.gray

        await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji="⏪", row=1, disabled=True)
    async def rewind_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Restarts the song the jukebox is playing."""
        self.play(self.current.clone())
        self.footer = f"{interaction.user.display_name} rewound {self.current.title}"
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(emoji="▶️", row=1, disabled=True)
    async def play_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.voice_client.is_paused():
            self.voice_client.resume()

        elif self.voice_client.is_playing():
            self.voice_client.pause()

        self.update_play_buttons()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(emoji="⏩", row=1, disabled=True)
    async def skip_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Restarts the song the jukebox is playing."""
        self.voice_client._player.after = None  # clear the after because play next is called manually
        self.play_next_song()

        try:
            # reset the after because play next is called manually
            self.voice_client._player.after = self.play_next_song
        except NoVoiceClient:
            print("MISSING VC")

        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(emoji="🖼️", row=1, )
    async def cover_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.cover_display = not self.cover_display
        button.style = discord.ButtonStyle.green if self.cover_display else discord.ButtonStyle.gray
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(emoji="🗑️", row=2)
    async def clear_history_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Clears the history the bot has recorded."""
        self.history.clear()
        self.update_history_select()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(emoji="\u25C0", row=2, disabled=True)
    async def left_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page > 1:
            self.page -= 1

        self.update_page_buttons()
        await interaction.response.edit_message(embed=self.embed, view=self)

    def page_right(self):
        if self.page < self.total_pages:
            self.page += 1

    def page_left(self):
        if self.page > 1:
            self.page -= 1


    @discord.ui.button(emoji="🪙", style=discord.ButtonStyle.gray, row=2)
    async def add_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(SongModal(self))

    @discord.ui.button(emoji="\u25B6", row=2, disabled=True)
    async def right_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page < self.total_pages:
            self.page += 1

        self.update_page_buttons()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(emoji="♾️", row=2)
    async def infinite_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Sets the bot to automatically pick songs"""
        if self.infinite:
            self.infinite = False
            button.style = discord.ButtonStyle.gray
        else:
            self.infinite = True
            button.style = discord.ButtonStyle.green

        await interaction.response.edit_message(embed=self.embed, view=self)

    def update_play_buttons(self):
        """Update the design of the buttons to relect the voice client state."""
        if self.voice_client.is_playing():
            self.play_button.disabled = False
            self.play_button.style = discord.ButtonStyle.red
            self.play_button.emoji = "⏸"
            self.rewind_button.disabled = False
            self.skip_button.disabled = False

        elif self.voice_client.is_paused():
            self.play_button.disabled = False
            self.play_button.style = discord.ButtonStyle.green
            self.play_button.emoji = "▶️"
            self.rewind_button.disabled = False
            self.skip_button.disabled = False

        else:
            self.play_button.disabled = True
            self.play_button.style = discord.ButtonStyle.gray
            self.play_button.emoji = "▶️"
            self.rewind_button.disabled = True
            self.skip_button.disabled = True

    def update_page_buttons(self):
        """update the state of the page buttons"""
        if self.page > self.total_pages:
            self.page = self.total_pages

        self.left_button.disabled = self.page == 1
        self.right_button.disabled = self.page == self.total_pages

    def update_history_select(self):
        """updates the select box for history"""
        if not self.history:
            self.history_select.disabled = True
            self.history_select.options = [
                discord.SelectOption(
                    label="PlACEHOLDER",
                    description="You found an easter egg"
                )
            ]
        else:
            self.history_select.disabled = False
            self.history_select.options = [
                discord.SelectOption(
                    label=song.title,
                    description=song.duration
                ) for song in self.history
            ]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Try to ensure the bot cannot be griefed"""

        # User not in voice channel
        if not interaction.user.voice:
            await interaction.response.send_message(
                content="My brother in christ you need to be in a voice channel to listen to music",
                ephemeral=True
            )
            return False

        try:
            vcc = self.voice_client
        except NoVoiceClient:
            return True

        if interaction.user.voice.channel != vcc.channel:
            await interaction.response.send_message(
                content="Trying to steal the bot are we?",
                ephemeral=True
            )
            return False
