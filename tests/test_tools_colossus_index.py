from pathlib import Path

from tools.colossus_index import (
    build_context,
    build_master_index,
    collect_puzzle_solutions,
    load_anchor_summary,
    load_colossus_cycles,
    load_pulse_summary,
    parse_puzzle_range,
    parse_federation_sources,
    summarise_glyphs,
)


def test_parse_puzzle_range_handles_bounds() -> None:
    assert parse_puzzle_range("10-20") == (10, 20)


def test_collect_puzzle_solutions_filters_range() -> None:
    root = Path(__file__).resolve().parents[1] / "puzzle_solutions"
    results = collect_puzzle_solutions(141, 10000, root=root)
    puzzles = [entry.puzzle for entry in results]
    assert puzzles == [284, 6210]
    assert all(entry.address for entry in results)


def test_build_master_index_includes_expected_sections() -> None:
    puzzle_range = (141, 10000)
    federation = parse_federation_sources("pulse, anchor, glyph, satoshi-reconstruction")
    cycles = load_colossus_cycles()
    puzzles = collect_puzzle_solutions(*puzzle_range)
    pulse = load_pulse_summary()
    anchor = load_anchor_summary()
    glyph = summarise_glyphs(cycles)

    context = build_context(
        artifact_type="colossus",
        puzzle_range=puzzle_range,
        federation_sources=federation,
        cycles=cycles,
        puzzle_solutions=puzzles,
        pulse=pulse,
        anchor=anchor,
        glyph=glyph,
    )
    index = build_master_index(context)

    assert "Colossus Master Index" in index
    assert "Cycle 00001" in index
    assert "Satoshi Reconstruction" in index
    assert "Pulse Federation Signal" in index
    assert "Anchor Ledger Summary" in index
    assert "Glyph Highlights" in index
