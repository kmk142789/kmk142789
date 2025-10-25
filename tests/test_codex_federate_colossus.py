import argparse

import codex
import pytest


def test_parse_puzzle_range_valid():
    assert codex.parse_puzzle_range("10-42") == (10, 42)


def test_parse_puzzle_range_invalid():
    with pytest.raises(argparse.ArgumentTypeError):
        codex.parse_puzzle_range("42")


def test_collect_puzzle_entries(tmp_path):
    puzzle_dir = tmp_path / "puzzles"
    puzzle_dir.mkdir()
    puzzle_path = puzzle_dir / "puzzle_150.md"
    puzzle_path.write_text("# Puzzle 150\n\n```\n1AExampleAddress\n```\n", encoding="utf-8")

    entries, missing = codex.collect_puzzle_entries(150, 152, puzzle_dir)
    assert [entry.puzzle_id for entry in entries] == [150]
    assert entries[0].address == "1AExampleAddress"
    assert missing == [151, 152]
