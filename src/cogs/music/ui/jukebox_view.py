import discord

from .cover_container import CoverContainer
from .queue_container import QueueContainer
from .overview_container import OverviewContainer
from ..model.jukebox import Jukebox
from ..model.enums import JukeboxMode

class JukeboxView(discord.ui.DesignerView):
    def __init__(self, jukebox: Jukebox) -> None:
        super().__init__(timeout=None)

        self.jukebox = jukebox

        self.mode = JukeboxMode.Overview
        self.previous_mode = JukeboxMode.Overview

        # Default view container
        self.add_item(OverviewContainer(jukebox))

    def update(self):
        """Rebuild the view updated values. Should be called before message update."""
        self.clear_items()
        match self.mode:
            case JukeboxMode.Queue:
                self.add_item(QueueContainer(self.jukebox))
            case JukeboxMode.Cover:
                self.add_item(CoverContainer(self.jukebox))
            case _:
                self.add_item(OverviewContainer(self.jukebox))
