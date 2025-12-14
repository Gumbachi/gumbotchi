import asyncio
import time
from typing import Any

import discord
from yt_dlp import YoutubeDL

from .errors import SongError

YDL_OPTS = {
    "format": "ba",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4
}

FFMPEG_OPTS = {
    "executable": "ffmpeg",
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class Song(discord.PCMVolumeTransformer):
    """Represents song/youtube video as a discord audio object."""

    __slots__ = (
        "_metadata", "title", "duration_in_seconds",
        "url", "webpage_url", "thumbnail", "songvolume"
    )

    def __init__(
        self,
        source: discord.FFmpegPCMAudio,
        metadata: dict[str, Any],
        volume: float = 0.5,
    ) -> None:
        super().__init__(original=source, volume=volume)
        self._metadata = metadata
        self.title: str = metadata["title"]
        self.duration_in_seconds: int = metadata["duration"]
        self.url: str = metadata["url"]
        self.webpage_url: str = metadata["webpage_url"]
        self.thumbnail: str = metadata["thumbnail"]
        self.songvolume = volume

    def __str__(self):
        return f"[{self.title}]({self.webpage_url})\n{self.duration}"

    def __repr__(self):
        return f"Song({self.title=})"

    def clone(self):
        """Creates a duplicate discord Song object that hasn't been used."""
        return Song(
            source=discord.FFmpegPCMAudio(self.url, **FFMPEG_OPTS),
            metadata=self._metadata,
            volume=self.songvolume
        )

    @property
    def duration(self) -> str:
        """Duration of the song in string format"""
        if self.duration_in_seconds < 3600:
            return time.strftime("%M:%S", time.gmtime(self.duration_in_seconds))
        return time.strftime("%H:%M:%S", time.gmtime(self.duration_in_seconds))

    @classmethod
    async def from_query(cls, query: str, loop: asyncio.AbstractEventLoop | None = None):
        """Uses youtubeDL(ytdlp) to query song data."""

        loop = loop or asyncio.get_event_loop()

        with YoutubeDL(YDL_OPTS) as ydl:
            song_info = await loop.run_in_executor(
                None,
                lambda: ydl.extract_info(f"ytsearch:{query}", download=False)
            )

            try:
                info = song_info["entries"][0]
                audio = discord.FFmpegPCMAudio(info["url"], **FFMPEG_OPTS)
                return cls(source=audio, metadata=info)
            except IndexError:
                raise SongError(f"No results found for {query}")
