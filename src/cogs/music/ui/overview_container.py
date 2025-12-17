import discord

import common.utils as utils
from .shared_components import AddSongButton, JukeboxModes
from ..model.jukebox import Jukebox
from ..model.enums import JukeboxMode, RepeatMode

class JukeboxActions(discord.ui.ActionRow):
    def __init__(self, jukebox: Jukebox):
        super().__init__()

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

    @discord.ui.button(emoji="\u23EE", custom_id="jukebox-previous")
    async def on_previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        jukebox = self.view.jukebox
        jukebox.last_action = f"{interaction.user.display_name} rewound {jukebox.current.title}"
        jukebox.play(jukebox.current.clone())

        self.view.update()
        await interaction.response.edit_message(view=self.view)

    @discord.ui.button(emoji="\u25B6", label=f"{'-' * 4} Play {'-' * 4}", custom_id="jukebox-play-pause")
    async def on_play_pause(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(emoji="\u23ED", custom_id="jukebox-next")
    async def on_next(self, button: discord.ui.Button, interaction: discord.Interaction):
        jukebox = self.view.jukebox
        jukebox.last_action = f"{interaction.user.display_name} skipped {jukebox.current.title}"

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

    @discord.ui.string_select(
        placeholder="Requeue from history  •  58 songs",
        options=[
            discord.SelectOption(
                label="PlACEHOLDER",
                description="You found an easter egg"
            )
        ]
    )
    async def on_history_select(self, select: discord.ui.StringSelect, interaction: discord.Interaction):
        pass


class OverviewContainer(discord.ui.Container):
    def __init__(self, jukebox: Jukebox):
        super().__init__()

        # Now Playing
        title = discord.ui.TextDisplay("### GumBOTchi's Jukebox")

        if jukebox.current:
            song_name = utils.wrap_and_ellipsize(jukebox.current.title, cutoff=42)
            song = discord.ui.TextDisplay(f"**{song_name}**")
            artist = discord.ui.TextDisplay(f"{jukebox.current.duration}")
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
        nextup_title = discord.ui.TextDisplay(f"### Next Up  •  {len(jukebox.queue)} Songs in queue")
        nextup_section = discord.ui.Section(nextup_title, accessory=AddSongButton())

        self.add_separator(divider=False, spacing=1)
        self.add_item(nextup_section)
        self.add_text("**Literally Nothing**")
        self.add_text("Shows over... unless?")

        # History
        history_title = discord.ui.TextDisplay("### History")
        history_section = discord.ui.Section(history_title, accessory=ClearHistoryButton())

        self.add_separator(divider=False, spacing=1)
        self.add_item(history_section)
        self.add_item(HistorySelect())

        # Modes
        self.add_separator(divider=False, spacing=1)
        self.add_text("### Modes")
        self.add_item(JukeboxModes(mode=JukeboxMode.Overview))

        # Action footer
        self.add_separator(divider=False, spacing=1)

        action = utils.ellipsize(jukebox.last_action, cutoff=70)
        self.add_text(f"-# {action}")
