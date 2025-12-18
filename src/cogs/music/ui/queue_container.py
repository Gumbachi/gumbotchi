import discord

import common.utils as utils
from .shared_components import AddSongButton, JukeboxModes
from ..model.enums import JukeboxMode
from ..model.song import Song
from ..model.jukebox import Jukebox

PAGESIZE = 5

class QueueActions(discord.ui.ActionRow):

    def __init__(self, jukebox: Jukebox, pages: int):
        super().__init__()
        self.jukebox = jukebox
        self.pages = pages

        display = self.get_item("page-display")
        display.label = f"{'-' * 15} Page {jukebox.page + 1} / {self.pages} {'-' * 15}"

        left = self.get_item("jukebox-page-left")
        left.disabled = self.pages <= 1

        right = self.get_item("jukebox-page-right")
        right.disabled = self.pages <= 1


    @discord.ui.button(emoji="⬅️", custom_id="jukebox-page-left")
    async def on_page_left(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Wrap around
        if self.jukebox.page == 0:
            self.jukebox.page == self.pages - 1
        else:
            self.jukebox.page -= 1

        self.view.update()
        await interaction.response.edit_message(view=self.view)

    @discord.ui.button(disabled=True, custom_id="page-display")
    async def placeholder(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(emoji="➡️", custom_id="jukebox-page-right")
    async def on_page_right(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Wrap around
        if self.jukebox.page == self.pages - 1:
            self.jukebox.page = 0
        else:
            self.jukebox.page += 1

        self.view.update()
        await interaction.response.edit_message(view=self.view)

class QueueItem(discord.ui.Section):
    def __init__(self, song: Song, index: int):
        super().__init__()
        self.add_text(f"**{utils.wrap_and_ellipsize(song.title, cutoff=48)}**")
        self.add_text(f"**{index + 1}**  •  {utils.format_duration(song.duration_in_seconds)}")
        self.set_accessory(QueueRemoveButton(index))

class QueueRemoveButton(discord.ui.Button):
    def __init__(self, index: int):
        super().__init__(emoji="🗑️", style=discord.ButtonStyle.red)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        jukebox = self.view.jukebox
        jukebox.queue.pop(self.index)
        jukebox.last_action = f"{interaction.user.display_name} **unqueued** {jukebox.current.title}"

        # Switch back a page if deleting last item on a page
        if jukebox.queue and len(jukebox.queue) % PAGESIZE == 0:
            jukebox.page -= 1

        self.view.update()
        await interaction.response.edit_message(view=self.view)

class QueueContainer(discord.ui.Container):


    def __init__(self, jukebox: Jukebox):
        super().__init__()

        # Header display
        title = discord.ui.TextDisplay(f"### Queue  •  {utils.pluralize('Song', len(jukebox.queue))}")
        header = discord.ui.Section(title, accessory=AddSongButton())
        self.add_item(header)
        self.add_separator(divider=False)

        song_chunks = utils.chunk(jukebox.queue, PAGESIZE)

        # Queue list
        for i, song in enumerate(song_chunks[jukebox.page]):
            queue_index = PAGESIZE * jukebox.page + i
            self.add_item(QueueItem(song, index=queue_index))
            self.add_separator()

        # Pager
        self.add_item(QueueActions(jukebox, pages=len(song_chunks)))

        # Mode Select
        self.add_separator(divider=False, spacing=1)
        self.add_text("### Modes")
        self.add_item(JukeboxModes(mode=JukeboxMode.Queue))
