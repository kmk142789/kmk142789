from datetime import datetime, timezone
import json
from pathlib import Path

from pulse_dashboard.financial_verifier import FinancialIntegrationVerifier


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_verifier_reports_connections_and_integrations(tmp_path: Path) -> None:
    data_dir = tmp_path / "data" / "impact"
    now = datetime(2024, 6, 10, tzinfo=timezone.utc)

    events = [
        {
            "id": "donation-1",
            "timestamp": (now.replace(day=3)).isoformat(),
            "type": "donation",
            "amount_usd": 2000,
            "asset": "USDC",
            "source": "Stripe autopay",
            "memo": "Recurring Stripe channel",
        },
        {
            "id": "donation-2",
            "timestamp": (now.replace(day=4)).isoformat(),
            "type": "donation",
            "amount_usd": 1500,
            "asset": "USDC",
            "source": "Plaid supporter",
            "memo": "Plaid-linked contribution",
        },
        {
            "id": "disbursement-1",
            "timestamp": (now.replace(day=5)).isoformat(),
            "type": "disbursement",
            "amount_usd": 500,
            "asset": "USDC",
            "source": "Lil Footsteps Ops",
        },
    ]
    operations = {
        "sustainability": {
            "recurring_donation_integrations": [
                "Stripe",
                "Plaid",
                "Direct smart contract allowances",
            ]
        }
    }

    _write_json(data_dir / "financial_events.json", events)
    _write_json(data_dir / "operations.json", operations)

    report = FinancialIntegrationVerifier(project_root=tmp_path).verify()

    assert any(conn["source"] == "Stripe autopay" for conn in report["connections"])
    stripe_entry = next(conn for conn in report["connections"] if conn["source"] == "Stripe autopay")
    assert stripe_entry["donations"] == 2000.0
    assert stripe_entry["donation_share"] == 0.5714

    integrations = {entry["name"]: entry["status"] for entry in report["integrations"]}
    assert integrations["Stripe"] == "observed"
    assert integrations["Plaid"] == "observed"
    assert integrations["Direct smart contract allowances"] == "declared"
    assert report["issues"] == []


def test_verifier_handles_missing_data(tmp_path: Path) -> None:
    report = FinancialIntegrationVerifier(project_root=tmp_path).verify()

    assert report["connections"] == []
    assert report["integrations"] == []
    assert "No financial event sources" in report["issues"][0]
    assert "No recurring donation integration" in report["issues"][1]
