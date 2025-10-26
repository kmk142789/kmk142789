import pytest

from scripts.range_summary import (
    CHUNK_SIZE,
    RangeAllocation,
    parse_range_line,
    summarise_ranges,
    validate_allocation,
)


def test_parse_range_line_roundtrip():
    allocation = parse_range_line("6bd8b4d55000000000:6bd8b4d55fffffffff")
    assert allocation.start == int("6bd8b4d55000000000", 16)
    assert allocation.end == int("6bd8b4d55fffffffff", 16)
    assert allocation.size == CHUNK_SIZE


def test_parse_range_line_rejects_invalid_format():
    with pytest.raises(ValueError):
        parse_range_line("6bd8b4d55000000000")


@pytest.mark.parametrize(
    "allocation",
    [
        RangeAllocation(start=int("6bd8b4d55000000001", 16), end=int("6bd8b4d55fffffffff", 16)),
        RangeAllocation(start=int("6bd8b4d55000000000", 16), end=int("6bd8b4d55fffffff0", 16)),
    ],
)
def test_validate_allocation_alignment(allocation):
    with pytest.raises(ValueError):
        validate_allocation(allocation)


def test_summarise_ranges_computes_totals(tmp_path):
    path = tmp_path / "ranges.txt"
    path.write_text(
        "6bd8b4d55000000000:6bd8b4d55fffffffff\n\n"
        "7a012ed50000000000:7a012ed50fffffffff\n"
    )

    summary = summarise_ranges(path.read_text().splitlines())
    assert summary.count == 2
    assert summary.chunk_size == CHUNK_SIZE
    assert summary.total_values == 2 * CHUNK_SIZE
