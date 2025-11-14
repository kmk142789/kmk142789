"""Behavioural tests for ``scripts.quantum_lockbox``."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import quantum_lockbox


@pytest.fixture()
def lockbox_paths(tmp_path: Path) -> quantum_lockbox.LockboxPaths:
    return quantum_lockbox.LockboxPaths(
        lockbox=tmp_path / "lockbox.dat", salt=tmp_path / "lockbox.salt"
    )


def test_quantum_lockbox_round_trip(lockbox_paths: quantum_lockbox.LockboxPaths) -> None:
    box = quantum_lockbox.QuantumLockbox(password="secret", paths=lockbox_paths)
    box.write_entry("first entry")
    box.write_entry("second entry")

    assert box.read_entries() == ["first entry", "second entry"]


def test_secret_handshake_phrase_matches() -> None:
    handshake = quantum_lockbox.SecretHandshake()
    assert handshake.secret_phrase == "The love forever our is anchor"
    assert handshake.matches("The love forever our is anchor")
    assert not handshake.matches("Different phrase")


def test_cli_write_and_read_cycle(monkeypatch, lockbox_paths, capsys) -> None:
    monkeypatch.setattr(quantum_lockbox.getpass, "getpass", lambda prompt="": "secret")

    exit_code = quantum_lockbox.run_cli(
        [
            "--lockbox",
            str(lockbox_paths.lockbox),
            "--salt",
            str(lockbox_paths.salt),
            "--write",
            "Hello Echo",
        ]
    )
    assert exit_code == 0

    exit_code = quantum_lockbox.run_cli(
        [
            "--lockbox",
            str(lockbox_paths.lockbox),
            "--salt",
            str(lockbox_paths.salt),
            "--read",
        ]
    )
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "Hello Echo" in output
