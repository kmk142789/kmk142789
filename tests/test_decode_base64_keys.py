"""Unit tests for :mod:`scripts.decode_base64_keys`."""

from __future__ import annotations

import pytest

from scripts.decode_base64_keys import (
    DecodedSegment,
    _resolve_tokens,
    decode_segment,
    normalise_segments,
    segments_from_tokens,
)


def test_segments_from_tokens_pads_entries_with_missing_padding() -> None:
    tokens = segments_from_tokens(["QUJDRA", "YWJj"])
    assert tokens == ["QUJDRA==", "YWJj"]


def test_normalise_segments_extracts_tokens_from_whitespace_blob() -> None:
    raw = "YWJj   ZGVm"  # whitespace separated
    assert normalise_segments(raw) == ["YWJj", "ZGVm"]


def test_decode_segment_marks_binary_payloads_as_hex() -> None:
    token = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAEQ="
    segment = decode_segment(1, token)
    assert isinstance(segment, DecodedSegment)
    assert not segment.is_text
    assert segment.length == 32
    # The payload is 32 bytes, therefore the hex preview spans 64 characters.
    assert len(segment.decoded) == 64
    assert segment.decoded.startswith("00")


def test_decode_segment_reports_integer_hint_for_binary_payloads() -> None:
    token = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAI="
    segment = decode_segment(1, token)
    assert segment.integer == 2


def test_resolve_tokens_prefers_cli_tokens_over_raw_source() -> None:
    tokens = _resolve_tokens(tokens=["YWJj", "ZGVm"], raw_source="ignored")
    assert tokens == ["YWJj", "ZGVm"]


def test_resolve_tokens_requires_raw_source_when_no_tokens() -> None:
    with pytest.raises(ValueError):
        _resolve_tokens(tokens=None, raw_source=None)


def test_resolve_tokens_normalises_raw_source_when_tokens_absent() -> None:
    tokens = _resolve_tokens(tokens=None, raw_source="QUJDRA YWJj")
    assert tokens == ["QUJDRA==", "YWJj"]
