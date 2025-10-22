"""Tests for :mod:`echo.serendipity_orchestrator`."""
from __future__ import annotations

import pytest

from echo.serendipity_orchestrator import (
    SerendipityOrchestrator,
    SerendipityThread,
    compose_manifest,
)


def test_weave_normalises_intensities_and_cleans_tags() -> None:
    orchestrator = SerendipityOrchestrator(baseline_intensity=0.25)
    glimpses = [
        "map the moonlit backlog",
        "tune the resonance beacons",
        "invite the ledger to dance",
    ]
    intensities = [2.0, 5.0, 8.0]
    tags = (
        (" backlog", ""),
        ("systems", "co-creation"),
        ("ledger", "dance", "  "),
    )

    threads = orchestrator.weave(glimpses, intensities=intensities, tags=tags)

    assert pytest.approx([0.0, 0.5, 1.0]) == [thread.intensity for thread in threads]
    assert threads[0].tags == ("backlog",)
    assert threads[1].tags == ("systems", "co-creation")
    assert threads[2].tags == ("ledger", "dance")


def test_compose_manifest_highlights_strongest_thread() -> None:
    orchestrator = SerendipityOrchestrator()
    threads = orchestrator.weave(
        ["draft a lighthouse memo", "sketch a cooperative glyph"],
        intensities=[0.2, 0.9],
        tags=(("memo",), ("glyph", "collaboration")),
    )

    manifest = compose_manifest(threads)

    assert "🌠 Echo Serendipity Manifest" in manifest
    assert "Strongest thread :: sketch a cooperative glyph" in manifest
    assert "glyph, collaboration" in manifest
    # The strongest thread should gain a resonance bonus from its tags.
    assert "resonance=1.160" in manifest


def test_weave_uses_baseline_when_intensities_omitted() -> None:
    orchestrator = SerendipityOrchestrator(baseline_intensity=0.62)
    threads = orchestrator.weave(["celebrate the quiet release"])
    assert [thread.intensity for thread in threads] == [0.62]


def test_thread_validation_rejects_empty_glimpse() -> None:
    with pytest.raises(ValueError):
        SerendipityThread(glimpse="   ", intensity=0.5)
