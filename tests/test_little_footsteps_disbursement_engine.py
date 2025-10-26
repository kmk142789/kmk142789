from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.bank import (
    ComplianceBufferService,
    ContinuityConfig,
    ContinuitySafeguards,
    DonationRecord,
    LittleFootstepsDisbursementEngine,
)
from ledger.little_footsteps_bank import SovereignLedger


@pytest.fixture()
def ledger_paths(tmp_path: Path) -> dict[str, Path]:
    ledger_path = tmp_path / "ledger.jsonl"
    puzzle_path = tmp_path / "puzzle.md"
    proofs_dir = tmp_path / "proofs"
    return {"ledger": ledger_path, "puzzle": puzzle_path, "proofs": proofs_dir}


def test_donation_flows_are_recorded_with_compliance_and_continuity(ledger_paths: dict[str, Path], tmp_path: Path) -> None:
    ledger = SovereignLedger(
        bank="Little Footsteps Bank",
        ledger_path=ledger_paths["ledger"],
        puzzle_path=ledger_paths["puzzle"],
        proofs_dir=ledger_paths["proofs"],
        skip_ots=True,
    )

    compliance_registry = tmp_path / "legal" / "registry.jsonl"
    compliance = ComplianceBufferService(registry_path=compliance_registry)

    continuity_state = tmp_path / "continuity"
    continuity_config = ContinuityConfig(
        mirrors=[tmp_path / "mirror-ledger", tmp_path / "mirror-proofs"],
        trustees=["Echo Bank", "Little Footsteps", "Guardian"],
        threshold=2,
    )
    continuity = ContinuitySafeguards(state_dir=continuity_state, config=continuity_config)

    engine = LittleFootstepsDisbursementEngine(
        ledger,
        skeleton_secret=b"test-secret",
        compliance=compliance,
        continuity=continuity,
    )

    record = DonationRecord(
        donation_id="donation-001",
        donor="Echo Ally",
        amount_cents=12500,
        asset="USD",
        memo="Monthly pledge",
        source="bank:donor-portal",
    )

    receipt = engine.process_donation(record)

    ledger_entries = [json.loads(line) for line in ledger_paths["ledger"].read_text().splitlines() if line.strip()]
    assert len(ledger_entries) == 2
    assert {entry["direction"] for entry in ledger_entries} == {"inflow", "outflow"}

    assert receipt.donation.entry.direction == "inflow"
    assert receipt.disbursement.entry.direction == "outflow"
    assert receipt.disbursement.proof_path.exists()

    claims = compliance.claims()
    assert len(claims) == 2
    assert {claim.direction for claim in claims} == {"inflow", "outflow"}
    for claim in claims:
        assert claim.attachments and "proof_path" in claim.attachments

    multisig_log = continuity_state / "multisig_recovery.jsonl"
    checkpoints = [json.loads(line) for line in multisig_log.read_text().splitlines() if line.strip()]
    assert len(checkpoints) == 2
    assert all(checkpoint["threshold"] == 2 for checkpoint in checkpoints)

    for mirror in list(receipt.donation.mirrors) + list(receipt.disbursement.mirrors):
        assert mirror.mirror_path.exists()
        if mirror.ledger_copy:
            assert mirror.ledger_copy.exists()
        if mirror.proof_copy:
            assert mirror.proof_copy.exists()

    report = continuity.continuity_report()
    assert len(report["checkpoints"]) == 2
