"""Utilities for working with golden test fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "GOLDEN_FIXTURES",
    "golden_fixture_path",
    "read_golden_json",
    "read_golden_text",
]

_FIXTURES_DIR = Path(__file__).with_name("fixtures")

GOLDEN_FIXTURES: dict[str, str] = {
    "atlas_graph_svg": "atlas_graph.svg",
    "autonomy_consensus": "autonomy_consensus.json",
    "autonomy_manifesto": "autonomy_manifesto.txt",
    "autonomy_amplification": "autonomy_amplification.json",
}


def golden_fixture_path(name: str) -> Path:
    """Return the path to the registered golden fixture."""

    try:
        filename = GOLDEN_FIXTURES[name]
    except KeyError as exc:  # pragma: no cover - defensive programming
        known = ", ".join(sorted(GOLDEN_FIXTURES))
        raise KeyError(f"Unknown golden fixture '{name}'. Known fixtures: {known}.") from exc
    return _FIXTURES_DIR / filename


def read_golden_text(name: str) -> str:
    """Read a golden fixture as text."""

    return golden_fixture_path(name).read_text(encoding="utf-8")


def read_golden_json(name: str) -> Any:
    """Load a golden fixture encoded as JSON."""

    return json.loads(read_golden_text(name))
