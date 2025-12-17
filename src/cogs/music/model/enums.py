from enum import Enum, auto


class RepeatMode(Enum):
    Repeat = auto()
    RepeatOne = auto()
    RepeatOff = auto()


class JukeboxMode(Enum):
    Overview = auto()
    Queue = auto()
    Cover = auto()
