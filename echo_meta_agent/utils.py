"""Utility helpers for the Echo Meta Agent."""

from __future__ import annotations

import json
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Tuple


def safe_truncate(value: Any, limit: int = 200) -> str:
    """Return a safe string representation truncated to *limit* characters."""

    if value is None:
        return ""
    try:
        text = json.dumps(value, ensure_ascii=False)
    except TypeError:
        text = str(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}…"


def parse_arguments(tokens: Iterable[str]) -> Tuple[List[str], Dict[str, Any]]:
    """Parse CLI style tokens into positional and keyword arguments."""

    args: List[str] = []
    kwargs: Dict[str, Any] = {}
    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            kwargs[key] = _coerce_value(value)
        elif token:
            args.append(token)
    return args, kwargs


def _coerce_value(value: str) -> Any:
    """Attempt to convert a string to bool/int/float when reasonable."""

    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def fuzzy_find(query: str, candidates: Iterable[str]) -> str | None:
    """Return the best fuzzy match for *query* from *candidates* using a ratio."""

    best_score = 0.0
    best_candidate: str | None = None
    for candidate in candidates:
        score = SequenceMatcher(a=query.lower(), b=candidate.lower()).ratio()
        if score > best_score:
            best_score = score
            best_candidate = candidate
    if best_score >= 0.6:
        return best_candidate
    return None
