from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from echo.orchestrator.proof_service import (
    NetworkConfig,
    ProofOrchestratorService,
    Secp256k1Wallet,
)


def _credential(identifier: str) -> dict:
    return {
        "id": identifier,
        "issuer": "did:example:issuer",
        "credentialSubject": {
            "id": "did:example:holder",
            "role": "member",
        },
        "proof": {
            "type": "Ed25519Signature2020",
            "created": datetime.now(timezone.utc).isoformat(),
        },
        "issuanceDate": datetime.now(timezone.utc).isoformat(),
    }


def test_submit_without_networks(tmp_path: Path) -> None:
    service = ProofOrchestratorService(tmp_path)
    result = service.submit_proof([_credential("vc-1")])

    assert result.credential_count == 1
    assert result.aggregated_proof.scheme == "zk-snark"

    stored = service.query_status(result.submission_id)
    assert stored is not None
    assert stored["aggregated_proof"]["id"] == result.aggregated_proof.identifier


def test_dispatch_with_partial_failure(tmp_path: Path) -> None:
    service = ProofOrchestratorService(tmp_path)
    credentials = [_credential("vc-1"), _credential("vc-2")]

    networks = [
        NetworkConfig(name="alpha", chain_id="1"),
        NetworkConfig(name="beta", chain_id="2"),
    ]

    signer = Secp256k1Wallet.from_private_key_hex("11" * 32)

    result = service.submit_proof(
        credentials,
        networks=networks,
        signers={"alpha": signer},
    )

    assert any(item.status == "failed" for item in result.dispatch_results)
    assert service.pending_fallbacks(), "Expected fallback payload for failed network"
