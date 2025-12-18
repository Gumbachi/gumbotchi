"""Utility functions that are used in multiple places"""
from typing import TypeVar
import time


T = TypeVar("T")

def chunk(arr: list[T], chunksize: int) -> list[list[T]]:
    """Split a list into a list of lists of a specific size"""
    if not arr:
        return [[]]
    return [arr[i : i + chunksize] for i in range(0, len(arr), chunksize)]

def format_duration(duration: int) -> str:
    """Duration of seconds in string format"""
    if duration < 3600:
        return time.strftime("%M:%S", time.gmtime(duration))
    return time.strftime("%H:%M:%S", time.gmtime(duration))

def pluralize(word: str, count: int) -> str:
    """This is just for cleanliness."""
    extra = "s" if count != 1 else ""
    return f"{count} {word}{extra}"

def ellipsize(text: str, cutoff: int = 64) -> str:
    """Shrink a string to a certain size and ellipsize it"""
    if len(text) < cutoff:
        return text
    return text[:cutoff] + "..."

def wrap_and_ellipsize(text: str, cutoff: int = 64) -> str:
    """Shrink a string to a certain size and ellipsize it"""
    if len(text) < cutoff:
        return text

    if len(text) < cutoff * 2:
        return f"{text[:cutoff]}\n{text[cutoff:]}"

    return f"{text[:cutoff]}\n{text[cutoff:cutoff * 2]}..."
