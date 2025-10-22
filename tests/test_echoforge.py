"""Tests for the EchoForge dashboard helpers."""

from __future__ import annotations

import json
from pathlib import Path

from echo.echoforge.storage import EchoForgeSessionStore
from echo.pulsenet import AtlasAttestationResolver
from echo_atlas.domain import EntityType, Node


class _DummyAtlasService:
    def __init__(self, nodes: list[Node] | None = None) -> None:
        self._nodes = nodes or []

    def list_nodes(self) -> list[Node]:  # pragma: no cover - trivial accessor
        return list(self._nodes)


def test_atlas_resolver_loads_wallet_metadata(tmp_path: Path) -> None:
    nodes = [
        Node(
            identifier="wallet-1",
            name="Wallet 1",
            entity_type=EntityType.KEYREF,
            metadata={
                "fingerprint": "f00dbabe",
                "extended_public_key": "xpub6CExample",
                "derivation_path": "m/84h/0h/0h",
                "owner": "Atlas",
            },
        )
    ]
    dummy_service = _DummyAtlasService(nodes)
    attestations = tmp_path / "attestations"
    attestations.mkdir()
    payload = {
        "ledger": {
            "wallets": {
                "61f21543": {
                    "owner": "Josh+Echo",
                    "metadata": {
                        "fingerprint": "61f21543",
                        "extended_public_key": "xpub6CMHQ9Example",
                        "derivation_path": "m/44h/0h/0h",
                    },
                }
            }
        }
    }
    (attestations / "wallet.json").write_text(json.dumps(payload), encoding="utf-8")

    resolver = AtlasAttestationResolver(tmp_path, dummy_service)
    wallet = resolver.lookup("61f21543")
    assert wallet is not None
    assert wallet.extended_public_key.startswith("xpub6CMHQ9")
    assert any(item["fingerprint"] == "61f21543" for item in resolver.wallets())
    atlas_wallet = resolver.lookup("f00dbabe")
    assert atlas_wallet is not None
    assert atlas_wallet.derivation_path == "m/84h/0h/0h"


def test_session_store_persists_sessions(tmp_path: Path) -> None:
    store = EchoForgeSessionStore(tmp_path / "sessions.db")
    store.create_session(session_id="alpha", client_host="127.0.0.1", client_port=9000, user_agent="pytest")
    payload = {
        "pulse": {"message": "🔥 ignite", "hash": "abc", "timestamp": 123.0},
        "attestation": {"proof_id": "proof-1"},
        "summary": {"total_entries": 1},
        "atlas": {"fingerprint": "61f21543", "extended_public_key": "xpub"},
    }
    store.store_pulse("alpha", event_payload=payload)

    sessions = store.sessions()
    assert len(sessions) == 1
    assert sessions[0].pulse_count == 1

    session_payload = store.session_payload("alpha")
    assert session_payload["session"]["pulse_count"] == 1
    assert session_payload["pulses"][0]["payload"]["pulse"]["message"] == "🔥 ignite"

    recent = store.recent_pulses(limit=5)
    assert recent[0]["pulse"]["message"] == "🔥 ignite"
