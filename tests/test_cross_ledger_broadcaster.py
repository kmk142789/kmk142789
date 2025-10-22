import base64
import hashlib
import json
from datetime import datetime, timezone
from unittest.mock import patch

from echo.atlas.temporal_ledger import TemporalLedger
from echo.pulse import (
    CrossLedgerBroadcaster,
    CrossLedgerSynchronizer,
    PulseLedger,
)


def _log_receipt(ledger: PulseLedger, timestamp: datetime, *, diff: str) -> str:
    with patch.object(PulseLedger, "_timestamp", return_value=timestamp):
        receipt = ledger.log(
            diff_signature=diff,
            actor="echo",
            result="ok",
            seed="seed",
        )
    return receipt.signature


def _merkle_root_hashes(hashes: list[str]) -> str:
    layer = [bytes.fromhex(h) for h in hashes]
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        layer = [
            hashlib.sha256(layer[idx] + layer[idx + 1]).digest()
            for idx in range(0, len(layer), 2)
        ]
    return layer[0].hex()


def test_broadcaster_exports_canonical_proofs(tmp_path) -> None:
    pulse_root = tmp_path / "pulse"
    state_dir = tmp_path / "state"
    ledger = PulseLedger(root=pulse_root)

    first_ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    second_ts = datetime(2024, 1, 2, 8, 30, tzinfo=timezone.utc)

    first_signature = _log_receipt(ledger, first_ts, diff="diff-one")
    second_signature = _log_receipt(ledger, second_ts, diff="diff-two")

    temporal_ledger = TemporalLedger(state_dir=state_dir)
    synchronizer = CrossLedgerSynchronizer(
        pulse_ledger=ledger,
        temporal_ledger=temporal_ledger,
        actor="sync",
        action="validated",
    )
    synchronizer.sync()

    broadcaster = CrossLedgerBroadcaster(pulse_ledger=ledger, temporal_ledger=temporal_ledger)
    bundle = broadcaster.build_bundle()

    assert bundle.merkle_root is not None
    assert [proof.proof_id for proof in bundle.proofs] == [first_signature, second_signature]

    hashes = [proof.leaf_hash for proof in bundle.proofs]
    assert bundle.merkle_root == _merkle_root_hashes(hashes)

    first_proof = bundle.proofs[0]
    expected_json = json.dumps(first_proof.payload, sort_keys=True, separators=(",", ":"))
    assert first_proof.json == expected_json
    assert (
        base64.b64decode(first_proof.base64.encode("ascii")).decode("utf-8")
        == expected_json
    )
    assert first_proof.payload["temporal_ledger"]["proof_id"] == first_signature
    assert first_proof.payload["pulse_receipt"]["signature"] == first_signature


def test_broadcaster_limit_filters_recent_entries(tmp_path) -> None:
    pulse_root = tmp_path / "pulse"
    state_dir = tmp_path / "state"
    ledger = PulseLedger(root=pulse_root)

    first_ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    second_ts = datetime(2024, 1, 2, 8, 30, tzinfo=timezone.utc)

    _log_receipt(ledger, first_ts, diff="diff-one")
    latest_signature = _log_receipt(ledger, second_ts, diff="diff-two")

    temporal_ledger = TemporalLedger(state_dir=state_dir)
    synchronizer = CrossLedgerSynchronizer(
        pulse_ledger=ledger,
        temporal_ledger=temporal_ledger,
        actor="sync",
        action="validated",
    )
    synchronizer.sync()

    broadcaster = CrossLedgerBroadcaster(pulse_ledger=ledger, temporal_ledger=temporal_ledger)
    bundle = broadcaster.build_bundle(limit=1)

    assert [proof.proof_id for proof in bundle.proofs] == [latest_signature]
    assert bundle.merkle_root == bundle.proofs[0].leaf_hash
