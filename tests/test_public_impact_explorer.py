from __future__ import annotations

import json
from pathlib import Path

import pytest

from pulse_dashboard.impact import PublicImpactExplorer


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def test_public_impact_explorer_compiles_snapshot(tmp_path: Path) -> None:
    ledger_entries = [
        {
            "type": "deposit",
            "amount_wei": 1_000_000_000_000_000_000,
            "tx_hash": "0x1",
            "actor": "0xDonorOne",
            "timestamp": 1_700_000_000,
        },
        {
            "type": "deposit",
            "amount_wei": 500_000_000_000_000_000,
            "tx_hash": "0x2",
            "actor": "0xDonorTwo",
            "timestamp": 1_700_010_000,
        },
        {
            "type": "payout",
            "amount_wei": 300_000_000_000_000_000,
            "tx_hash": "0x3",
            "actor": "0xLilFootsteps",
            "timestamp": 1_700_020_000,
        },
    ]
    write_json(tmp_path / "ledger" / "nonprofit_bank_ledger.json", ledger_entries)

    policy = {
        "stablecoin_targets": [
            {"symbol": "USDC", "target_pct": 50},
            {"symbol": "GUSD", "target_pct": 50},
        ],
        "current_reserves": {
            "USDC": {"amount_usd": 6000, "custodian": "Circle"},
            "GUSD": {"amount_usd": 6000, "custodian": "Gemini"},
        },
        "operating_burn_usd_weekly": 2400,
        "emergency_reserve": {
            "target_ratio": 0.1,
            "current_usd": 1500,
            "multisig_threshold": "3-of-5",
            "vault": "Emergency Safe",
        },
        "yield_programs": [
            {"name": "Circle Yield", "status": "active"},
        ],
    }
    write_json(tmp_path / "state" / "nonprofit_treasury_policy.json", policy)

    metrics = {
        "last_updated": "2025-05-10T00:00:00Z",
        "totals": {
            "families_served": 120,
            "hours_of_childcare": 5400,
            "job_placements": 32,
            "caregiver_wages_paid_usd": 140000,
        },
        "current_cycle": {
            "cycle": 16,
            "families_served": 18,
            "hours_of_childcare": 760,
            "job_placements": 6,
        },
        "history": [
            {"period": "2025-Q1", "families_served": 32, "hours_of_childcare": 1800, "job_placements": 9},
            {"period": "2025-Q2", "families_served": 36, "hours_of_childcare": 1920, "job_placements": 11},
        ],
        "equity_breakdown": {"languages": {"english": 0.6, "spanish": 0.3}},
        "data_sources": ["ledger", "surveys"],
    }
    write_json(tmp_path / "reports" / "data" / "childcare_impact_metrics.json", metrics)

    parent_council = {
        "charter": "Parents co-design childcare services.",
        "meeting_cadence": {"next_session": "2025-06-15T18:00:00Z", "location": "Hybrid"},
    }
    write_json(tmp_path / "state" / "parent_advisory_council.json", parent_council)

    provider_feedback = {
        "office_hours": {"next_session": "2025-05-20T12:00:00-04:00", "host": "Operations"},
    }
    write_json(tmp_path / "state" / "provider_feedback_loop.json", provider_feedback)

    explorer = PublicImpactExplorer(tmp_path)
    dataset = explorer.build()

    treasury = dataset["treasury"]
    ledger = treasury["ledger"]
    assert pytest.approx(ledger["balance_eth"], rel=1e-6) == 1.2
    assert ledger["deposit_count"] == 2
    assert ledger["payout_count"] == 1

    policy_snapshot = treasury["policy"]
    assert policy_snapshot["diversity_score"] == pytest.approx(100.0)
    assert policy_snapshot["emergency_reserve"]["status"] == "meets_target"
    assert policy_snapshot["runway_weeks"] == pytest.approx(5.0)

    impact = dataset["impact_metrics"]
    assert impact["trend"]["families_served"]["change"] == 4
    assert impact["data_sources"] == ["ledger", "surveys"]

    engagements = dataset["upcoming_engagements"]
    assert len(engagements) == 2
    assert engagements[0]["name"] == "Provider Office Hours"
    assert engagements[1]["name"] == "Parent Advisory Council"
