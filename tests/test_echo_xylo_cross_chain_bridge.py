import hashlib
import json
from datetime import datetime

import pytest

from packages.core.src.echo.echo_xylo_cross_chain_bridge import (
    AnchorState,
    EchoXyloCrossChainBridge,
)


def _commitment_for(payload: dict) -> str:
    serialised = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "0x" + hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def test_bridge_ready_when_all_anchors_finalized():
    bridge = EchoXyloCrossChainBridge(finality_threshold=0.7, min_confirmations=2)
    eth_proof = {"txHash": "0xabc", "blockNumber": 12_345}
    sol_proof = {"slot": 99_001, "account": "DIDPDA"}

    bridge.register_anchor(
        chain="ethereum",
        anchor_id="0xabc",
        confirmations=6,
        finality_score=0.92,
        proof=eth_proof,
        proof_type="zkp",
    )
    bridge.register_anchor(
        chain="solana",
        anchor_id="slot-99",
        confirmations=12,
        finality_score=0.88,
        proof=sol_proof,
        proof_type="hash",
    )
    bridge.register_anchor(
        chain="bitcoin",
        anchor_id="inscription-9",
        confirmations=3,
        finality_score=0.91,
        proof={"inscriptionId": "txid:0:0"},
    )

    assessment = bridge.assess()
    assert assessment.ready is True
    assert assessment.missing_chains == ()
    assert assessment.coverage == 1.0
    assert {anchor.chain for anchor in assessment.anchors} == {"ethereum", "solana", "bitcoin"}

    envelope = bridge.build_envelope()
    assert envelope["ready"] is True
    assert len(envelope["anchors"]) == 3
    anchors_by_chain = {anchor["chain"]: anchor for anchor in envelope["anchors"]}
    assert anchors_by_chain["ethereum"]["proof_commitment"] == _commitment_for(eth_proof)
    assert anchors_by_chain["solana"]["proof_commitment"] == _commitment_for(sol_proof)
    assert envelope["risk_score"] < 0.4



def test_bridge_surfaces_missing_chains_and_low_finality():
    bridge = EchoXyloCrossChainBridge(finality_threshold=0.8, min_confirmations=2)
    bridge.register_anchor(
        chain="ethereum",
        anchor_id="commit-1",
        confirmations=2,
        finality_score=0.75,
    )
    bridge.register_anchor(
        chain="solana",
        anchor_id="slot-5",
        confirmations=1,
        finality_score=0.95,
    )

    assessment = bridge.assess()
    assert assessment.ready is False
    assert assessment.missing_chains == ("bitcoin",)
    assert assessment.coverage == pytest.approx(2 / 3, rel=1e-3)
    assert assessment.risk_score == pytest.approx(0.622, rel=1e-3)
    assert assessment.aggregated_finality == pytest.approx((0.75 + 0.95) / 3, rel=1e-3)



def test_attach_proof_enriches_existing_anchor():
    bridge = EchoXyloCrossChainBridge(finality_threshold=0.7, min_confirmations=1)
    bridge.register_anchor(
        chain="ethereum",
        anchor_id="commit-2",
        confirmations=3,
        finality_score=0.8,
    )
    payload = {"txHash": "0xdef", "blockNumber": 999}
    updated = bridge.attach_proof("ethereum", "commit-2", payload, proof_type="zkp")

    assert isinstance(updated, AnchorState)
    assert updated.proof is not None
    assert updated.proof.commitment == _commitment_for(payload)
    assert updated.proof.proof_type == "zkp"
    assert datetime.fromisoformat(updated.last_checked)

    envelope = bridge.build_envelope()
    assert envelope["anchors"][0]["proof_type"] == "zkp"
    assert envelope["anchors"][0]["proof_commitment"] == _commitment_for(payload)

    with pytest.raises(KeyError):
        bridge.attach_proof("solana", "missing", {})
