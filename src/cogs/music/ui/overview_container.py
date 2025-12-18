import discord

import common.utils as utils
from common.cfg import Tenor
from .shared_components import AddSongButton, JukeboxModes
from ..model.jukebox import Jukebox
from ..model.enums import JukeboxMode, RepeatMode

class JukeboxActions(discord.ui.ActionRow):
    def __init__(self, jukebox: Jukebox):
        super().__init__()

        play_button = self.get_item("jukebox-play-pause")
        skip_button = self.get_item("jukebox-skip")
        rewind_button = self.get_item("jukebox-rewind")
        if (client := jukebox.voice_client):
            if client.is_playing():
                play_button.emoji = "\u23F8"
                play_button.label="-- Playing --"
                play_button.style = discord.ButtonStyle.red
            elif client.is_paused():
                play_button.label="-- Paused --"
                play_button.emoji = "\u25B6"
        else:
            play_button.disabled = True
            skip_button.disabled = True
            rewind_button.disabled = True

        repeat_button = self.get_item("jukebox-repeat")
        if jukebox.repeat != RepeatMode.RepeatOff:
            repeat_button.style = discord.ButtonStyle.blurple
        if jukebox.repeat == RepeatMode.RepeatOne:
            repeat_button.emoji = "🔂"


        shuffle_button = self.get_item("jukebox-shuffle")
        if jukebox.shuffle:
            shuffle_button.style = discord.ButtonStyle.blurple

    @discord.ui.button(emoji="🔁", custom_id="jukebox-repeat")
    async def on_repeat(self, button: discord.ui.Button, interaction: discord.Interaction):

        jukebox = self.view.jukebox

        if jukebox.repeat == RepeatMode.RepeatOff:
            jukebox.repeat = RepeatMode.Repeat
        elif jukebox.repeat == RepeatMode.Repeat:
            jukebox.repeat = RepeatMode.RepeatOne
        else:
            jukebox.repeat = RepeatMode.RepeatOff

        self.view.update()
        await interaction.response.edit_message(view=self.view)

    @discord.ui.button(emoji="\u23EE", custom_id="jukebox-rewind")
    async def on_previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        jukebox = self.view.jukebox
        jukebox.last_action = f"{interaction.user.display_name} **rewound** {jukebox.current.title}"
        jukebox.play(jukebox.current.clone())

        self.view.update()
        await interaction.response.edit_message(view=self.view)

    @discord.ui.button(emoji="\u25B6", label="-- Padding --", custom_id="jukebox-play-pause")
    async def on_play_pause(self, button: discord.ui.Button, interaction: discord.Interaction):
        jukebox = self.view.jukebox
        client = jukebox.voice_client

        if client and client.is_paused():
            client.resume()
            jukebox.last_action = f"{interaction.user.display_name} **unpaused** {jukebox.current.title}"
        elif client and client.is_playing():
            jukebox.last_action = f"{interaction.user.display_name} **paused** {jukebox.current.title}"
            client.pause()


        self.view.update()
        await interaction.response.edit_message(view=self.view)

    @discord.ui.button(emoji="\u23ED", custom_id="jukebox-skip")
    async def on_next(self, button: discord.ui.Button, interaction: discord.Interaction):
        jukebox = self.view.jukebox
        jukebox.last_action = f"{interaction.user.display_name} **skipped** {jukebox.current.title}"

        jukebox.voice_client._player.after = None  # clear the after because play next is called manually
        jukebox.play_next_song()

        jukebox.voice_client._player.after = jukebox.play_next_song

        self.view.update()
        await interaction.response.edit_message(view=self.view)

    @discord.ui.button(emoji="🔀", custom_id="jukebox-shuffle")
    async def on_shuffle(self, button: discord.ui.Button, interaction: discord.Interaction):
        jukebox = self.view.jukebox
        jukebox.shuffle = not jukebox.shuffle

        self.view.update()
        await interaction.response.edit_message(view=self.view)


class ClearHistoryButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="🗑️", label="Clear History")

    async def callback(self, interaction: discord.Interaction):
        jukebox = self.view.jukebox
        jukebox.history.clear()
        jukebox.last_action = f"{interaction.user.display_name} cleared the history"

        self.view.update()
        await interaction.response.edit_message(view=self.view)

class HistorySelect(discord.ui.ActionRow):

    def __init__(self, jukebox: Jukebox):
        super().__init__()
        self.jukebox = jukebox

        select = self.get_item("jukebox-history-select")

        if not jukebox.history:
            select.disabled = True
            select.placeholder = "Played songs will appear here"
        else:
            select.placeholder = f"Requeue from {utils.pluralize('Song', len(jukebox.history))}"
            select.options = [
                discord.SelectOption(label=song.title, description=song.duration)
                for song in self.jukebox.history
            ]

    @discord.ui.string_select(
        custom_id="jukebox-history-select",
        options=[discord.SelectOption(label="PLACEHOLDER", description="placeholder")]
    )
    async def on_history_select(self, select: discord.ui.StringSelect, interaction: discord.Interaction):

        if interaction.user.voice is None:
            return await interaction.response.send_message(Tenor.KERMIT_LOST, ephemeral=True)

        await interaction.response.defer()

        if self.jukebox.voice_client is None:
            await self.jukebox.connect(interaction.user.voice.channel)

        # Find first matching song in history
        song = next((s for s in self.jukebox.history if s.title == select.values[0]))

        if self.jukebox.current is None:
            self.jukebox.play(song)
            self.jukebox.last_action = f"{interaction.user.display_name} added {song.title}"
        else:
            if len(self.jukebox.queue) >= self.jukebox.max_queue:
                self.view.update()
                return await interaction.followup.send("Can't handle that many songs", ephemeral=True)

            self.jukebox.enqueue(song)
            self.jukebox.last_action = f"{interaction.user.display_name} queued {song.title}"

        self.view.update()
        await interaction.message.edit(view=self.view)


class OverviewContainer(discord.ui.Container):
    def __init__(self, jukebox: Jukebox):
        super().__init__()

        # Now Playing
        title = discord.ui.TextDisplay("### GumBOTchi's Jukebox")

        if jukebox.current:
            song_name = utils.wrap_and_ellipsize(jukebox.current.title, cutoff=42)
            song = discord.ui.TextDisplay(f"**{song_name}**")
            artist = discord.ui.TextDisplay(f"{jukebox.duration_bar}")
            thumbnail = discord.ui.Thumbnail(jukebox.current.thumbnail)
        else:
            song = discord.ui.TextDisplay("**Nothing playing**")
            artist = discord.ui.TextDisplay("Hint: Check the image")
            thumbnail = discord.ui.Thumbnail("https://files.gumbachi.com/assets/add-song.jpg")

        song_section = discord.ui.Section(title, song, artist, accessory=thumbnail)

        self.add_item(song_section)
        self.add_item(JukeboxActions(jukebox=jukebox))

        # Next Up
        self.add_separator(divider=False, spacing=1)
        queue_size = len(jukebox.queue)
        nextup_title = discord.ui.TextDisplay(f"### Next Up  •  {utils.pluralize('Song', queue_size)} in queue")
        nextup_section = discord.ui.Section(nextup_title, accessory=AddSongButton())

        self.add_separator(divider=False, spacing=1)
        self.add_item(nextup_section)

        next_song = jukebox.next_up
        if next_song:
            self.add_text(f"**{utils.wrap_and_ellipsize(next_song.title)}**")
            self.add_text(f"{next_song.duration}")
        else:
            self.add_text("**Literally Nothing**")
            self.add_text("Show's over... unless?")

        # History
        history_title = discord.ui.TextDisplay("### History")
        history_section = discord.ui.Section(history_title, accessory=ClearHistoryButton())

        self.add_separator(divider=False, spacing=1)
        self.add_item(history_section)
        self.add_item(HistorySelect(jukebox))

        # Modes
        self.add_separator(divider=False, spacing=1)
        self.add_text("### Modes")
        self.add_item(JukeboxModes(mode=JukeboxMode.Overview))

        # Action footer
        self.add_separator(divider=False, spacing=1)

        action = utils.ellipsize(jukebox.last_action, cutoff=70)
        self.add_text(f"-# {action}")
