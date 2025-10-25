"""Smoke and schema tests for the Puzzle Lab toolkit."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from echo_puzzle_lab import load_records, validate_against_schema


@pytest.fixture()
def fixture_map(tmp_path: Path) -> Path:
    sample = [
        {
            "puzzle": 1,
            "address": "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH",
            "address_family": "P2PKH",
            "hash160": "751e76e8199196d454941c45d1b3a323f1433bd6",
            "pkscript": {
                "asm": "OP_DUP OP_HASH160 751e76e8199196d454941c45d1b3a323f1433bd6 OP_EQUALVERIFY OP_CHECKSIG",
                "hex": "76a914751e76e8199196d454941c45d1b3a323f1433bd688ac",
            },
            "ud": {"domains": [], "owner": None, "records": {}},
            "lineage": {"source_files": ["docs/Puzzle_001.md"], "commit": None, "pr": None},
            "tested": True,
            "updated_at": "2024-01-01T00:00:00+00:00",
        },
        {
            "puzzle": 2,
            "address": "1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb",
            "address_family": "P2PKH",
            "hash160": "7dd65592d0ab2fe0d0257d571abf032cd9db93dc",
            "pkscript": {
                "asm": "OP_DUP OP_HASH160 7dd65592d0ab2fe0d0257d571abf032cd9db93dc OP_EQUALVERIFY OP_CHECKSIG",
                "hex": "76a9147dd65592d0ab2fe0d0257d571abf032cd9db93dc88ac",
            },
            "ud": {"domains": [], "owner": None, "records": {}},
            "lineage": {"source_files": ["docs/Puzzle_002.md"], "commit": None, "pr": "#100"},
            "tested": True,
            "updated_at": "2024-01-02T00:00:00+00:00",
        },
    ]
    destination = tmp_path / "echo_map.json"
    destination.write_text(json.dumps(sample, indent=2))
    return destination


def test_echo_map_matches_schema() -> None:
    """All committed entries should match the declared schema."""

    records = load_records()
    errors = validate_against_schema(records)
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize(
    "command",
    [["stats", "-j"], ["verify", "--puzzles", "1"]],
)
def test_cli_smoke(command: list[str], fixture_map: Path) -> None:
    env = os.environ.copy()
    env["ECHO_MAP_PATH"] = str(fixture_map)
    result = subprocess.run(
        [sys.executable, "-m", "echo_cli", *command],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    if "-j" in command:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        assert payload["total_puzzles"] == 2
        assert payload["ud_bound"]["bound"] == 0
