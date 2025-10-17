from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from echo.crypto import sign as sign_utils
from echo.pulseweaver.pulse_bus import PulseBus


def _derive_public_key(private_hex: str) -> str:
    secret = int(private_hex, 16)
    point = sign_utils._scalar_multiply(secret, sign_utils._SECP256K1_G)  # type: ignore[attr-defined]
    if point is None:  # pragma: no cover - defensive
        raise RuntimeError("failed to derive public key")
    x, y = point
    return (b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")).hex()


def test_emit_and_ingest_roundtrip(tmp_path):
    private_key = "1" * 64
    public_key = _derive_public_key(private_key)
    key_id = "test-key"

    bus = PulseBus(state_dir=tmp_path, signing_key={"private_key": private_key, "key_id": key_id})
    bus.register_key(key_id, public_key)

    outbox_entry = bus.emit(
        repo="echo/example",
        ref="deadbeef",
        kind="fix",
        summary="repair",
        proof_id="proof-1",
        timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )

    assert outbox_entry.path.exists()
    payload = json.loads(outbox_entry.path.read_text(encoding="utf-8"))
    assert payload["key_id"] == key_id

    envelope = bus.ingest(payload)
    assert envelope.repo == "echo/example"
    inbox_files = list((tmp_path / "pulses" / "inbox").glob("*.json"))
    assert inbox_files, "pulse should be stored in inbox"

    # idempotent ingest
    second = bus.ingest(payload)
    assert second.signature == envelope.signature
