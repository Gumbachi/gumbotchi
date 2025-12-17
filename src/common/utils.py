"""Utility functions that are used in multiple places"""


from typing import Any


def chunk(arr: list[Any], chunksize: int) -> list[list[Any]]:
    """Split a list into a list of lists of a specific size"""
    return [arr[i : i + chunksize] for i in range(0, len(arr), chunksize)]


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
