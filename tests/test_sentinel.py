from __future__ import annotations

import json
from pathlib import Path

from sentinel import inventory
from sentinel.attest import build_dsse_envelope
from sentinel.policy import PolicyEngine
from sentinel.probe.fs import FileSystemProbe
from sentinel.remedy.apply import apply_plan
from sentinel.remedy.plan import build_plan
from sentinel.utils import Finding


def test_inventory_collects_receipts(tmp_path: Path) -> None:
    lineage_path = tmp_path / "lineage.json"
    lineage_path.write_text(json.dumps({"build": {"http_source": "https://example.com"}}))

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    receipt_path = receipts_dir / "artifact.json"
    receipt_path.write_text(json.dumps({"name": "artifact"}))

    data = inventory.build_inventory(lineage_path, receipts_dir)
    assert data["signals"]["total_receipts"] == 1
    assert "https://example.com" in data["signals"]["http_endpoints"]


def test_filesystem_probe_detects_hash_drift(tmp_path: Path) -> None:
    file_path = tmp_path / "artifact.txt"
    file_path.write_text("alpha")
    data = {
        "receipts": [
            {
                "path": str(file_path),
                "sha256": "deadbeef",
                "mode": "file",
            }
        ]
    }
    probe = FileSystemProbe()
    findings = probe.run(data)
    statuses = {finding.status for finding in findings}
    assert "error" in statuses


def test_attestation_envelope_contains_digest() -> None:
    report = {"name": "probe", "findings": []}
    envelope = build_dsse_envelope(report)
    assert envelope["dsseEnvelope"]["payloadType"].startswith("application/vnd.sentinel")
    assert envelope["dsseEnvelope"]["signatures"][0]["sig"]


def test_remedy_apply_idempotent(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    report_path = reports_dir / "report-filesystem.json"
    report_path.write_text(json.dumps({
        "findings": [
            {
                "probe": "filesystem",
                "subject": "missing.txt",
                "status": "error",
                "message": "missing",
                "data": {},
            }
        ]
    }))
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    plan = build_plan(reports_dir, None, True)
    plan_path = plan_dir / "remedy-plan.json"
    plan_path.write_text(json.dumps(plan))

    assert apply_plan(plan_path, force=True)
    assert not apply_plan(plan_path, force=True)


def test_policy_quarantine_triggers() -> None:
    engine = PolicyEngine(quarantine_threshold=1)
    findings = [
        Finding(
            probe="filesystem",
            subject="danger.txt",
            status="error",
            message="compromised",
            data={},
        )
    ]
    decisions = engine.evaluate(findings)
    assert decisions
    assert decisions[0].level == "quarantine"

