"""Tests for :mod:`echo.creative_bloom`."""
from __future__ import annotations

import pytest

from echo.creative_bloom import (
    BloomPetal,
    BloomReport,
    BloomSeed,
    CreativeBloom,
    render_bloom_table,
)


def test_cultivate_generates_petals_and_report_summary() -> None:
    seeds = [
        BloomSeed(theme="lighthouse retrospectives", intensity=0.7, sparks=("retrospective", "signal")),
        BloomSeed(theme="ledger story circles", intensity=0.9, sparks=("story",)),
    ]

    bloom = CreativeBloom(base_vividness=0.4)
    report = bloom.cultivate(seeds, cycles=2)

    assert report.petal_count == 4
    assert pytest.approx(0.7, rel=1e-3) == report.average_vividness
    assert report.theme_summary == ("lighthouse retrospectives", "ledger story circles")
    assert {petal.headline for petal in report.petals} == {
        "lighthouse retrospectives :: cycle 1",
        "lighthouse retrospectives :: cycle 2",
        "ledger story circles :: cycle 1",
        "ledger story circles :: cycle 2",
    }
    assert all("cycle-" in petal.tags[-1] for petal in report.petals)


def test_render_bloom_table_formats_content() -> None:
    petals = (
        BloomPetal(headline="lighthouse retrospectives :: cycle 1", vividness=0.5, tags=("retrospective", "signal")),
        BloomPetal(headline="ledger story circles :: cycle 1", vividness=0.8, tags=("story", "cycle-1")),
    )
    report = BloomReport(petals=petals, average_vividness=0.65, theme_summary=("lighthouse retrospectives", "ledger story circles"))

    table = render_bloom_table(report)

    assert "Average vividness :: 0.650" in table
    assert "1. lighthouse retrospectives :: cycle 1" in table
    assert "retrospective, signal" in table
    assert "(untagged)" not in table


def test_render_bloom_table_handles_empty_report() -> None:
    empty_report = BloomReport(petals=tuple(), average_vividness=0.0, theme_summary=tuple())
    assert (
        render_bloom_table(empty_report)
        == "No bloom petals available. Invite new seeds to the garden."
    )


def test_seed_validation_rejects_blank_theme() -> None:
    with pytest.raises(ValueError):
        BloomSeed(theme="   ", intensity=0.5)


def test_cultivate_rejects_invalid_cycles() -> None:
    bloom = CreativeBloom()
    with pytest.raises(ValueError):
        bloom.cultivate([BloomSeed(theme="echo", intensity=0.3)], cycles=0)
