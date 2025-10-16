from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.shard_vault import ingest_shard_text, parse_blob


VALID_FIXTURE = Path("tests/fixtures/valid_shard.txt")
VALID_TXID = "7c47d09d5a7b32ce223cd9c4617eb2332958321e005716d5420f8ea24c5e27c3"
MISMATCH_FIXTURE = Path("tests/fixtures/sample_shard.txt")


def _load_fixture(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_parse_blob_extracts_payload_and_digest():
    text = _load_fixture(VALID_FIXTURE)
    txid, payload, digest = parse_blob(text)

    assert txid == VALID_TXID
    assert digest == VALID_TXID
    assert len(payload) > 0


def test_ingest_shard_text_writes_artifacts_and_manifest(tmp_path: Path):
    text = _load_fixture(VALID_FIXTURE)
    shards_root = tmp_path / "vault" / "shards"
    manifest_path = tmp_path / "echo_manifest.json"
    manifest_path.write_text(json.dumps({"clis": []}, indent=2) + "\n", encoding="utf-8")

    result = ingest_shard_text(text, shards_root=shards_root, manifest_path=manifest_path)

    bin_path = shards_root / f"{VALID_TXID}.bin"
    attestation_path = shards_root / f"{VALID_TXID}.json"

    assert bin_path.exists()
    assert attestation_path.exists()

    attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
    assert attestation["txid"] == VALID_TXID
    assert attestation["bytes"] == len(bin_path.read_bytes())
    assert attestation["sha256"] == VALID_TXID
    assert attestation["source"] == "ECHO:SHARD_VAULT"
    assert attestation["ingested_at"].endswith("Z")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    shard_entries = manifest.get("shards", [])
    assert any(entry.get("txid") == VALID_TXID for entry in shard_entries)

    assert result["txid"] == VALID_TXID
    assert Path(result["bin_path"]) == bin_path
    assert Path(result["attestation_path"]) == attestation_path


def test_ingest_shard_text_rejects_mismatched_digest():
    text = _load_fixture(MISMATCH_FIXTURE)

    with pytest.raises(ValueError):
        ingest_shard_text(text, shards_root="unused", manifest_path="unused.json")
