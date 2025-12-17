import discord

from .shared_components import AddSongButton, JukeboxModes
from ..model.enums import JukeboxMode
from ..model.jukebox import Jukebox

class QueueActions(discord.ui.ActionRow):

    @discord.ui.button(emoji="\u2B05", custom_id="jukebox-page-left")
    async def on_page_left(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(label=f"{'-' * 15} Page 1 / 4 {'-' * 15}", disabled=True)
    async def on_button_two(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(emoji="\u27A1", custom_id="jukebox-page-right")
    async def on_page_right(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass

class QueueItem(discord.ui.Section):
    def __init__(self):
        super().__init__()

        self.add_text("**Queued Song Name**")
        self.add_text("Queued Song Artist • 03:22")

        accessory = discord.ui.Button(label="X", style=discord.ButtonStyle.red)
        self.set_accessory(accessory)

class QueueContainer(discord.ui.Container):

    pagesize = 5

    def __init__(self, jukebox: Jukebox):
        super().__init__()

        # Header display
        title = discord.ui.TextDisplay("### Queue  •  12 Songs")
        header = discord.ui.Section(title, accessory=AddSongButton())
        self.add_item(header)
        self.add_separator(divider=False)

        # Queue list
        for _ in range(self.pagesize):
            self.add_item(QueueItem())
            self.add_separator()

        # Pager
        self.add_item(QueueActions())

        # Mode Select
        self.add_separator(divider=False, spacing=1)
        self.add_text("### Modes")
        self.add_item(JukeboxModes(mode=JukeboxMode.Queue))

    @property
    def total_pages(self) -> int:
        """Calculate the total pages the queue takes."""
        return 4
        # amount = len(utils.chunk(self.queue, self.PAGESIZE))
        # return amount or 1  # cant have 0 pages
