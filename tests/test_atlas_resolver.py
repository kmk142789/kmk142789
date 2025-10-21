from __future__ import annotations

from echo.continuum_atlas import (
    AtlasState,
    export_attestation,
    resolve_apps,
    resolve_domains,
    resolve_keys,
)


def test_resolve_keys_collects_wallets_and_pending() -> None:
    state = resolve_keys(
        [
            {
                "owner": "Echo Collective",
                "wallet": "0xabc",
                "proof": "sig-123",
                "confidence": 0.97,
                "network": "ethereum",
            },
            {"owner": "", "wallet": "0xdef", "proof": "sig-456"},
            {"wallet": "0xghi", "proof": "sig-789"},
        ]
    )

    wallets = state.ledger["wallets"]
    assert wallets["0xabc"]["owner"] == "Echo Collective"
    assert wallets["0xabc"]["proofs"] == ["sig-123"]
    assert wallets["0xabc"]["metadata"]["network"] == "ethereum"
    assert state.pending[0]["identifier"] == "0xdef"
    assert state.pending[0]["reason"] == "missing owner"
    assert state.pending[1]["identifier"] == "0xghi"
    assert state.pending[1]["reason"] == "missing owner"


def test_resolve_domains_and_apps_merge() -> None:
    state = AtlasState()
    resolve_domains(
        [
            {
                "owner": "Echo Collective",
                "domain": "echo.xyz",
                "proof": "dns-sig",
                "status": "active",
            },
            {"domain": "mystery.io", "owner": ""},
        ],
        state=state,
    )

    resolve_apps(
        [
            {
                "owner": "Echo Collective",
                "app": "echo-hub",
                "platform": "web",
                "version": "1.2.3",
                "proof": "manifest-sig",
            },
            {"app": "orphan-app"},
        ],
        state=state,
    )

    domains = state.ledger["domains"]
    apps = state.ledger["apps"]

    assert domains["echo.xyz"]["metadata"]["status"] == "active"
    assert domains["echo.xyz"]["proofs"] == ["dns-sig"]
    assert apps["echo-hub"]["metadata"]["platform"] == "web"
    assert apps["echo-hub"]["proofs"] == ["manifest-sig"]

    pending_types = {item["type"] for item in state.pending}
    assert pending_types == {"domain", "app"}


def test_export_attestation_generates_signature() -> None:
    state = AtlasState()
    resolve_keys(
        [
            {
                "owner": "Echo Collective",
                "wallet": "0x123",
                "proof": "sig-123",
            }
        ],
        state=state,
    )
    payload = {
        "project": "Continuum",
        "owner": "Echo",
        "generated_at": "2025-05-11T00:00:00Z",
        "source": "oracle-report.md",
        "weights": {},
        "expansion_targets": [],
        "stability_score": {"current": 0.7, "predicted": 0.7},
    }

    attestation = export_attestation(state, payload, signer="atlas-bot")
    attestation_again = export_attestation(state, payload, signer="atlas-bot")

    assert attestation == attestation_again
    assert attestation["signature"].isalnum()
    assert attestation["ledger"]["wallets"]["0x123"]["owner"] == "Echo Collective"
    assert attestation["compass_summary"][0].startswith("Continuum Compass ::")


def test_resolution_handles_empty_inputs() -> None:
    state = AtlasState()
    resolve_keys([], state=state)
    resolve_domains([], state=state)
    resolve_apps([], state=state)

    snapshot = state.snapshot()
    assert snapshot["ledger"] == {"wallets": {}, "domains": {}, "apps": {}}
    assert snapshot["pending"] == []
