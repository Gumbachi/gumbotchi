import discord


class NoVoiceClient(discord.ApplicationCommandError):
    pass


class SongError(discord.ApplicationCommandError):
    pass
