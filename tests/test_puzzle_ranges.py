from __future__ import annotations

from pathlib import Path

import pytest

from satoshi.puzzle_ranges import (
    RangePair,
    format_summary,
    load_range_file,
    parse_range_pair,
    summarise_ranges,
)


def test_parse_range_pair_basic() -> None:
    pair = parse_range_pair("0a:0f")
    assert pair.start == 0x0A
    assert pair.end == 0x0F
    assert pair.width == 6
    assert pair.bit_length == 4


def test_load_range_lines_skips_comments(tmp_path: Path) -> None:
    content = """
    # comment line
    01:ff

    """
    path = tmp_path / "ranges.txt"
    path.write_text(content, encoding="utf-8")
    ranges = load_range_file(path)
    assert ranges == (RangePair(start=0x01, end=0xFF),)


def test_summarise_puzzle71_ranges() -> None:
    path = Path("satoshi/puzzle71_scan_ranges.txt")
    ranges = load_range_file(path)
    summary = summarise_ranges(ranges)

    assert summary.count == 60
    assert summary.range_min == int("41f811ff8000000000", 16)
    assert summary.range_max == int("7f8082b2bfffffffff", 16)
    assert summary.unique_widths == (1 << 36,)
    assert summary.bit_lengths == (71,)
    assert summary.puzzle_bits == 71
    assert summary.puzzle_min == 1 << 70
    assert summary.puzzle_max == (1 << 71) - 1
    assert summary.total_keys == 60 * (1 << 36)
    assert summary.coverage_ratio == pytest.approx(3.4924596548080444e-09)

    report = format_summary(summary)
    assert "Total ranges: 60" in report
    assert "Inferred puzzle bits: 71" in report
