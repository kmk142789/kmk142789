"""End-to-end tests for the sovereign operational layer."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from echo.sovereign import (
    BeneficiaryEngine,
    ComplianceShield,
    DonationIntakeAPI,
    GovernanceRegistry,
    MultiSigAttestation,
    TransparencyPortal,
    Trustee,
    generate_signature,
)


def _setup_registry() -> GovernanceRegistry:
    registry = GovernanceRegistry(
        entity_name="Echo Bank",
        charter_id="echo-bank-charter",
        base_commit_hash="abc123",
        quorum=2,
    )
    trustee_a = Trustee(did="did:echo:josh", name="Josh", roles=("trustee", "steward"))
    trustee_b = Trustee(did="did:echo:lena", name="Lena", roles=("trustee", "steward"))
    trustee_c = Trustee(did="did:echo:aria", name="Aria", roles=("trustee",))
    for trustee in (trustee_a, trustee_b, trustee_c):
        registry.register_trustee(trustee)
    return registry


def test_governance_registry_requires_multisig(tmp_path: Path) -> None:
    registry = _setup_registry()
    summary = "Amendment: establish stewardship council"
    commit_hash = "deadbeef"
    witness = registry.witness_hash(summary, commit_hash)
    attestation = MultiSigAttestation(witness_hash=witness, required=2, required_roles=("steward",))
    for trustee in registry.trustees():
        if not trustee.has_role("steward"):
            continue
        attestation.sign(trustee, generate_signature(trustee, witness))
    version = registry.record_amendment(summary=summary, commit_hash=commit_hash, attestation=attestation)
    assert version.version == "1.0.1"
    assert registry.latest().summary == summary


def test_donation_intake_and_beneficiary_engine(tmp_path: Path) -> None:
    log_path = tmp_path / "donations.jsonl"
    intake = DonationIntakeAPI(log_path=log_path)
    eth_receipt = intake.record_eth_donation(donor="0xabc", amount_wei=5 * 10**18, tx_hash="0x1")
    btc_receipt = intake.record_btc_donation(donor="bc1donor", amount_sats=25_000_000, txid="btc-tx")
    fiat_receipt = intake.record_fiat_donation(
        donor="Alice",
        amount=Decimal("125.00"),
        currency="usd",
        provider="Stripe",
        receipt_id="stripe-1",
    )
    assert eth_receipt.metadata["network"] == "ethereum"
    assert btc_receipt.channel == "btc"
    assert fiat_receipt.metadata["provider"] == "Stripe"
    assert len(list(intake.jsonl_feed())) == 3

    engine = BeneficiaryEngine(intake, jsonl_path=tmp_path / "disbursements.jsonl")
    payout = engine.execute_payout(
        beneficiary="Little Footsteps",
        amount=Decimal("2.5"),
        currency="ETH",
        memo="Weekly stipend",
        triggered_by="automation",
        source_receipts=[eth_receipt.id],
    )
    assert payout.beneficiary == "Little Footsteps"
    assert payout.source_receipts == (eth_receipt.id,)
    assert len(list(engine.jsonl_feed())) == 1


def test_compliance_and_transparency_snapshot(tmp_path: Path) -> None:
    registry = _setup_registry()
    intake = DonationIntakeAPI(log_path=tmp_path / "donations.jsonl")
    eth_receipt = intake.record_eth_donation(donor="0xabc", amount_wei=10 * 10**18, tx_hash="0xabc")
    engine = BeneficiaryEngine(intake, jsonl_path=tmp_path / "disbursements.jsonl")
    payout = engine.execute_payout(
        beneficiary="Little Footsteps",
        amount=Decimal("3.0"),
        currency="ETH",
        memo="Scholarship",
        triggered_by="automation",
        source_receipts=[eth_receipt.id],
    )

    shield = ComplianceShield(entity_name="Echo Bank")
    donation_entry = shield.record_donation(eth_receipt)
    disbursement_entry = shield.record_disbursement(payout)
    assert donation_entry.category == "donation"
    assert disbursement_entry.category == "disbursement"

    portal = TransparencyPortal(
        governance=registry,
        intake=intake,
        beneficiary=engine,
        compliance=shield,
    )
    snapshot = portal.snapshot()
    assert snapshot["entity"] == "Echo Bank"
    assert snapshot["telemetry"]["donation_count"] == 1
    assert snapshot["telemetry"]["disbursement_count"] == 1
    assert snapshot["governance"]["history"][0]["version"].startswith("1.")
