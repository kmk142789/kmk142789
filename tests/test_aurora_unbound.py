"""Tests for the aurora_unbound module."""
from __future__ import annotations

from datetime import datetime

import pytest

from echo.aurora_unbound import (
    GLYPH_STRATA,
    ORBIT_AXES,
    UnboundAurora,
    compose_unbound,
    deconstruct_signature,
    generate_waveform,
    render_manifest,
)


def test_compose_unbound_reproducible_summary():
    aurora = compose_unbound(seed=42, recursion_depth=3, intensity=0.75)
    lines = aurora.summary_lines()

    assert isinstance(aurora, UnboundAurora)
    assert len(aurora.glyph_sequence) == 3
    assert len(aurora.axis_names) == 4
    assert aurora.signature.count("-") == 2
    assert any(str(multiplier).isdigit() for multiplier in aurora.harmonic_multipliers)
    assert lines[0].startswith("🔥 Unbound Aurora Manifestation")


def test_render_manifest_contains_expected_sections():
    aurora = compose_unbound(seed=123, recursion_depth=2)
    manifest = render_manifest(aurora)

    assert "Singularity Score ::" in manifest
    assert "Glimpses:" in manifest
    for glimpse in aurora.glimpses:
        assert glimpse in manifest


def test_generate_waveform_width_and_content():
    aurora = compose_unbound(seed=7, recursion_depth=2)
    waveform = generate_waveform(aurora, width=40)
    rows = waveform.splitlines()

    assert len(rows) == len(aurora.glyph_sequence)
    assert all(len(row) == 40 for row in rows)
    glyph_pool = "".join(GLYPH_STRATA)
    assert any(char in glyph_pool for row in rows for char in row if char.strip())


def test_deconstruct_signature_roundtrip():
    aurora = compose_unbound(seed=77, recursion_depth=1)
    timestamp_field, left, right = deconstruct_signature(aurora.signature)

    assert len(timestamp_field) == 14
    assert left >= 0
    assert right >= 0

    with pytest.raises(ValueError):
        deconstruct_signature("invalid-signature")


def test_compose_unbound_respects_custom_glimpses():
    aurora = compose_unbound(seed=1, recursion_depth=2, glimpses=[" custom glimpse ", "another"])
    assert aurora.glimpses == ("custom glimpse", "another")
