"""Integrity tests for the generated echo_map.json index."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from echo.substrate import _derive_p2pkh_from_hash

BASE_PATH = Path(__file__).resolve().parents[1]
MAP_PATH = BASE_PATH / "echo_map.json"


@pytest.fixture(scope="module")
def echo_map() -> list[dict[str, object]]:
    payload = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    return payload


def test_unique_puzzle_address_pairs(echo_map: list[dict[str, object]]) -> None:
    seen: set[tuple[int, str]] = set()
    for entry in echo_map:
        assert {"puzzle", "address", "hash160", "pkscript", "lineage", "tested", "updated_at"}.issubset(entry.keys())
        puzzle = entry["puzzle"]
        address = entry["address"] or ""
        assert isinstance(puzzle, int)
        key = (puzzle, address)
        assert key not in seen, f"duplicate entry detected for puzzle {puzzle} and address {address}"
        seen.add(key)

        updated_at = entry["updated_at"]
        datetime.fromisoformat(updated_at)

        assert entry["tested"] is True


def test_sample_p2pkh_derivations(echo_map: list[dict[str, object]]) -> None:
    samples = [entry for entry in echo_map if entry["address_family"] == "P2PKH"][:10]
    assert samples, "no P2PKH samples found"
    for entry in samples:
        hash160 = entry["hash160"]
        address = entry["address"]
        assert isinstance(hash160, str) and len(hash160) == 40
        assert isinstance(address, str) and address.startswith("1")
        derived = _derive_p2pkh_from_hash(hash160)
        assert derived == address


def test_scripts_have_hex_and_asm(echo_map: list[dict[str, object]]) -> None:
    for entry in echo_map:
        script = entry.get("pkscript", {})
        asm = script.get("asm")
        hex_script = script.get("hex")
        assert asm is not None
        assert hex_script is not None
        assert isinstance(asm, str)
        assert isinstance(hex_script, str)
        assert len(hex_script) % 2 == 0
