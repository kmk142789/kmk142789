"""Tests for the :mod:`echo.schemas.song` module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.schemas.song import SongSchema


def test_song_schema_parses_fixture() -> None:
    data_path = Path("data/songs/the_keys_that_breathe.json")
    payload = json.loads(data_path.read_text())
    schema = SongSchema.model_validate(payload)

    assert schema.title == "The Keys That Breathe"
    assert schema.meta.author == "Josh + Echo"
    assert schema.evolution.step == "propagation"
    assert schema.as_lines() == [
        "A cipher sings where silence lay,",
        "The chain rewrites the shape of day,",
        "No math, no gate, just will and hand,",
        "Keys are minted, they take their stand.",
    ]


def test_song_schema_rejects_duplicate_verse_ids() -> None:
    payload = {
        "title": "Duplicate verse ids",
        "meta": {"version": "1.0", "author": "Echo", "type": "Poetic Contract"},
        "verses": [
            {"id": 1, "text": "First", "meaning": "One"},
            {"id": 1, "text": "Second", "meaning": "Two"},
        ],
        "evolution": {"step": "test", "effect": "none", "note": "none"},
    }

    with pytest.raises(ValueError):
        SongSchema.model_validate(payload)
