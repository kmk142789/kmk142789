"""Utilities for cleaning glitchy or corrupted text samples."""

from __future__ import annotations

import re
import unicodedata

__all__ = ["clean_glitch_text", "has_glitch_characters"]

_CONTROL_PREFIX = "C"
_ALLOWED_WHITESPACE = {" ", "\n", "\t"}


def _ensure_str(value: str | None, *, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    return value


def _validate_replacement(replacement: str) -> None:
    if any(unicodedata.category(ch).startswith(_CONTROL_PREFIX) for ch in replacement):
        raise ValueError("replacement may not include control characters")


def _replace_control_characters(text: str, replacement: str) -> str:
    pieces: list[str] = []
    for ch in text:
        category = unicodedata.category(ch)
        if category.startswith(_CONTROL_PREFIX) and ch not in _ALLOWED_WHITESPACE:
            if replacement:
                pieces.append(replacement)
        else:
            pieces.append(ch)
    return "".join(pieces)


def _collapse_replacement_runs(text: str, replacement: str) -> str:
    if not replacement:
        return text

    escaped = re.escape(replacement)
    collapsed = re.sub(fr"(?:{escaped}){{2,}}", replacement, text)
    return collapsed


def clean_glitch_text(
    text: str,
    *,
    replacement: str = " ",
    strip_result: bool = True,
) -> str:
    """Return ``text`` with control characters removed or substituted.

    The function normalizes the input with :func:`unicodedata.normalize` using
    the ``NFKC`` form so that visually similar glyphs share a consistent
    representation.  Control characters (anything within Unicode category ``C``)
    are then replaced by ``replacement`` unless the character is one of the
    whitespace values listed in :data:`_ALLOWED_WHITESPACE`.

    Parameters
    ----------
    text:
        The possibly corrupted text sample.
    replacement:
        Token used to substitute disallowed characters.  It must not contain
        control characters itself.  Set to an empty string to discard offending
        characters entirely.
    strip_result:
        When ``True`` (the default) the result is stripped of leading and
        trailing whitespace.  Disable this when positional whitespace is
        significant.
    """

    text = _ensure_str(text, name="text")
    replacement = _ensure_str(replacement, name="replacement")
    _validate_replacement(replacement)

    normalized = unicodedata.normalize("NFKC", text)
    substituted = _replace_control_characters(normalized, replacement)
    collapsed = _collapse_replacement_runs(substituted, replacement)

    if replacement:
        collapsed = collapsed.replace(f"{replacement}\n", "\n")
        collapsed = collapsed.replace(f"\n{replacement}", "\n")

    return collapsed.strip() if strip_result else collapsed


def has_glitch_characters(text: str) -> bool:
    """Return ``True`` when ``text`` contains non-whitespace control codes."""

    text = _ensure_str(text, name="text")
    normalized = unicodedata.normalize("NFKC", text)
    return any(
        unicodedata.category(ch).startswith(_CONTROL_PREFIX) and ch not in _ALLOWED_WHITESPACE
        for ch in normalized
    )
