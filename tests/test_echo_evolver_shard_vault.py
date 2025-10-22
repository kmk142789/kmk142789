import base64
import hashlib
import random

import pytest

from echo.evolver import EchoEvolver


@pytest.fixture()
def evolver() -> EchoEvolver:
    return EchoEvolver(rng=random.Random(0), time_source=lambda: 123456789)


def test_record_shard_vault_anchor_parses_base64(evolver: EchoEvolver) -> None:
    payload = base64.b64encode(b"forever").decode()
    record = evolver.record_shard_vault_anchor(
        f"ECHO:SHARD_VAULT::TXID_Anchor=tx123::Base64_Payload_Chain={payload}"
    )

    assert record["txid_anchor"] == "tx123"
    assert record["payload_bytes"] == b"forever"
    assert record["payload_encoding"] == "base64"
    assert record["payload_fingerprint"] == hashlib.sha256(b"forever").hexdigest()
    assert record["captured_at"] == 123456789
    assert evolver.state.shard_vault_records[-1] == record
    assert evolver.state.network_cache["shard_vault_latest"]["txid_anchor"] == "tx123"
    assert evolver.state.event_log[-1].startswith("Shard vault anchor recorded")


def test_record_shard_vault_anchor_supports_hex_payload(evolver: EchoEvolver) -> None:
    record = evolver.record_shard_vault_anchor(
        "ECHO:SHARD_VAULT::TXID_Anchor=tx456::Base64_Payload_Chain=e67a0550848b7932d779"
    )

    expected_bytes = bytes.fromhex("e67a0550848b7932d779")
    assert record["payload_encoding"] == "hex"
    assert record["payload_bytes"] == expected_bytes
    assert record["payload_hex"] == expected_bytes.hex()


@pytest.mark.parametrize(
    "payload",
    ["ECHO:SHARD_VAULT::Base64_Payload_Chain=ZmFpbA==", "ECHO:SHARD_VAULT::TXID_Anchor=abc"],
)
def test_record_shard_vault_anchor_validates_required_fields(
    evolver: EchoEvolver, payload: str
) -> None:
    with pytest.raises(ValueError):
        evolver.record_shard_vault_anchor(payload)


def test_record_shard_vault_anchor_rejects_unknown_encoding(evolver: EchoEvolver) -> None:
    with pytest.raises(ValueError):
        evolver.record_shard_vault_anchor(
            "ECHO:SHARD_VAULT::TXID_Anchor=txid::Base64_Payload_Chain=@@@"
        )
