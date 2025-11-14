"""Unit tests for the sovereign orchestration helpers."""

from __future__ import annotations

from datetime import timedelta

from echo.sovereign import (
    CredentialIssuer,
    DID,
    FederationNode,
    Governance,
    SovereignEngine,
)


def _make_did(identifier: str) -> DID:
    return DID(id=f"did:echo:{identifier}", public_key_pem=f"pk-{identifier}")


def test_governance_enforces_unique_proposals() -> None:
    governance = Governance()
    proposal_id = "upgrade-1"
    governance.propose_upgrade(proposal_id, "Enable orbital relay")

    alice = _make_did("alice")
    bob = _make_did("bob")

    assert governance.vote(proposal_id, alice, True)
    assert governance.vote(proposal_id, bob, True)
    assert governance.enact_upgrade(proposal_id)

    snapshot = governance.proposal_snapshot()
    assert snapshot[proposal_id]["enacted"] is True


def test_credential_issuer_revokes_and_verifies() -> None:
    issuer_did = _make_did("issuer")
    subject = _make_did("subject")
    issuer = CredentialIssuer(issuer_did)

    credential = issuer.issue_credential(
        subject,
        {"role": "member"},
        valid_for=timedelta(hours=2),
    )

    assert issuer.verify_credential(credential)
    issuer.revoke_credential(credential.credential_id)
    assert issuer.verify_credential(credential) is False


def test_federation_broadcast_records_each_peer() -> None:
    node = FederationNode(_make_did("core"))
    for peer in ("alpha", "beta"):
        node.connect_peer(_make_did(peer))

    node.broadcast_event("Credential_Issued", "cred-1")
    assert len(node.broadcast_log) == 2
    assert {entry["peer"] for entry in node.broadcast_log} == {
        "did:echo:alpha",
        "did:echo:beta",
    }


def test_engine_processes_trigger_event_queue() -> None:
    engine = SovereignEngine(_make_did("core"))
    engine.federation.connect_peer(_make_did("observer"))
    subject = _make_did("subject")

    engine.enqueue_event(
        "Trigger_Credential_Issue",
        {"trigger_id": "event-7", "subject": subject.__dict__},
    )
    engine.run_event_loop()

    assert any(
        entry.startswith("Issued credential") for entry in engine.event_log
    )
    issued = next(iter(engine.issuer.issued_credentials()))
    last_broadcast = engine.federation.broadcast_log[-1]
    assert last_broadcast["event_type"] == "Credential_Issued"
    assert last_broadcast["payload"] == issued.credential_id
