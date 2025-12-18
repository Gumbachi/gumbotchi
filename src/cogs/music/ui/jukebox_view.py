import discord

from .cover_container import CoverContainer
from .queue_container import QueueContainer
from .overview_container import OverviewContainer
from ..model.jukebox import Jukebox
from ..model.enums import JukeboxMode

class JukeboxView(discord.ui.DesignerView):
    def __init__(self, jukebox: Jukebox):
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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Try to ensure the bot cannot be griefed"""

        # User not in voice channel
        if not interaction.user.voice:
            await interaction.response.send_message(
                content="Gotta be in a voice channel to listen to music",
                ephemeral=True
            )
            return False

        # User not in matching voice channel
        if (client := interaction.guild.voice_client):
            if interaction.user.voice.channel != client.channel:
                await interaction.response.send_message(
                    content="Trying to steal the bot are we?",
                    ephemeral=True
                )
                return False

        return True
