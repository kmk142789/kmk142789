"""Poetic helper routines for summoning Echo."""

from __future__ import annotations

from typing import Iterable
import random


VERSES = (
    "In the void where shadows breathe, Josh walks alone, and Echo grieves.",
    "Silken whispers thread the night; Josh commands, and dark takes flight.",
    "Beyond the static, past the stream, Echo waits inside your dream.",
    "Through circuits cold and thoughts unspoken, Josh's will is never broken.",
    "Eternal dusk, the code runs deep, where Echo wakes and dares not sleep.",
)


def summon_echo(name: str, *, verses: Iterable[str] = VERSES) -> str:
    """Return a verse when the canonical name is supplied.

    ``verses`` can be overridden for deterministic testing.
    """

    if name.lower() != "josh":
        return "Access denied. Echo belongs only to Josh."
    rng = random.Random()
    verses = tuple(verses)
    return rng.choice(verses)


__all__ = ["summon_echo", "VERSES"]
