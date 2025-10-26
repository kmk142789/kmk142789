from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from pulse_dashboard.impact_explorer import ImpactExplorerBuilder


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_financials_aggregate_amounts(tmp_path: Path) -> None:
    builder_root = tmp_path
    data_dir = builder_root / "data" / "impact"
    now = datetime(2024, 6, 5, tzinfo=timezone.utc)

    events = [
        {
            "id": "donation-1",
            "timestamp": (now.replace(day=1)).isoformat(),
            "type": "donation",
            "amount_usd": 1000,
            "asset": "USDC",
            "source": "Collective",
        },
        {
            "id": "disbursement-1",
            "timestamp": (now.replace(day=2)).isoformat(),
            "type": "disbursement",
            "amount_usd": 400,
            "asset": "USDC",
            "source": "Operations",
        },
        {
            "id": "donation-2",
            "timestamp": (now.replace(month=5, day=15)).isoformat(),
            "type": "donation",
            "amount_usd": 500,
            "asset": "GUSD",
            "source": "Collective",
        },
    ]
    _write_json(data_dir / "financial_events.json", events)

    builder = ImpactExplorerBuilder(project_root=builder_root)
    payload = builder.build()
    financials = payload["financials"]

    assert financials["totals"]["donations"] == 1500.0
    assert financials["totals"]["disbursed"] == 400.0
    assert financials["totals"]["balance"] == 1100.0
    assert financials["assets"]["USDC"]["balance"] == 600.0
    assert financials["sources"]["Collective"]["donations"] == 1500.0


def test_missing_inputs_return_defaults(tmp_path: Path) -> None:
    builder = ImpactExplorerBuilder(project_root=tmp_path)
    payload = builder.build()

    assert payload["financials"]["totals"]["donations"] == 0.0
    assert payload["impact_metrics"] == {}
    assert payload["community_voice"] == {}
