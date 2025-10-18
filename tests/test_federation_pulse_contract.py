from __future__ import annotations

import json
import subprocess
from pathlib import Path

from federated_pulse.contract import emit_contract, generate_contract


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, text=True)


def _bootstrap_repo(path: Path) -> None:
    _run_git(path, "init")
    _run_git(path, "config", "user.name", "Echo Test")
    _run_git(path, "config", "user.email", "echo@example.com")

    (path / "pulse.txt").write_text("first\n", encoding="utf-8")
    _run_git(path, "add", "pulse.txt")
    _run_git(path, "commit", "-m", "Initial pulse")

    (path / "pulse.txt").write_text("first\nsecond\n", encoding="utf-8")
    _run_git(path, "commit", "-am", "Second resonance")


def test_emit_contract_writes_artifacts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _bootstrap_repo(repo)

    out_dir = tmp_path / "out"
    contract = emit_contract(repo, out_dir, limit=5)

    contract_path = out_dir / "repo_contract.json"
    heartbeat_path = out_dir / "repo_heartbeat.txt"

    assert contract_path.exists()
    assert heartbeat_path.exists()

    data = json.loads(contract_path.read_text(encoding="utf-8"))
    attestation = data["attestation_base58"]

    alphabet = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    assert attestation
    assert set(attestation) <= alphabet

    verse = data["recursive_verse"]
    assert len(verse) == len(data["commits"])
    assert any("Initial pulse" in line for line in verse)

    heartbeat_line = heartbeat_path.read_text(encoding="utf-8").strip()
    assert attestation in heartbeat_line
    assert heartbeat_line.startswith("federation_heartbeat ")

    assert contract.head.hash == data["head"]["hash"]
    assert len(contract.sovereign_cipher) == 64


def test_generate_contract_limit(tmp_path: Path) -> None:
    repo = tmp_path / "contract"
    repo.mkdir()
    _bootstrap_repo(repo)

    limited = generate_contract(repo, limit=1)
    assert len(limited.commits) == 1
    assert limited.recursive_verse[0].startswith("01 ∴")
