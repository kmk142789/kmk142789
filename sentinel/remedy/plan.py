from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from dataclasses import asdict

from ..policy import PolicyEngine
from ..utils import Finding, load_registry, read_json, write_json, isoformat
from . import RemedyAction


def _load_findings(reports_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(reports_dir.glob("report-*.json")):
        report = read_json(path)
        for entry in report.get("findings", []):
            findings.append(Finding(**entry))
    return findings


def _action_id(subject: str, message: str) -> str:
    return hashlib.sha256(f"{subject}:{message}".encode("utf-8")).hexdigest()[:16]


def _quarantine_action(subject: str, rationale: dict[str, Any]) -> RemedyAction:
    return RemedyAction(
        id=_action_id(subject, "quarantine"),
        subject=subject,
        description=f"Quarantine {subject} until manual review",
        metadata={"rationale": rationale},
    )


def _drift_action(finding: Finding, registry: dict[str, Any]) -> RemedyAction:
    description = f"Reconcile drift for {finding.subject}"
    fragment = next((frag for frag in registry.get("fragments", []) if frag.get("name") in finding.subject), None)
    metadata = {
        "finding": finding.__dict__,
        "registry_fragment": fragment,
    }
    return RemedyAction(
        id=_action_id(finding.subject, finding.message),
        subject=finding.subject,
        description=description,
        metadata=metadata,
    )


def build_plan(reports_dir: Path, registry_path: Path | None, dry_run: bool) -> dict[str, Any]:
    findings = _load_findings(reports_dir)
    registry = load_registry(registry_path)
    policy_engine = PolicyEngine()
    decisions = policy_engine.evaluate(findings)

    actions: list[RemedyAction] = []
    quarantined_subjects = {decision.rationale["subject"] for decision in decisions if decision.level == "quarantine"}

    for decision in decisions:
        if decision.level == "quarantine":
            actions.append(_quarantine_action(decision.rationale["subject"], decision.rationale))

    for finding in findings:
        if finding.status != "error":
            continue
        if finding.subject in quarantined_subjects:
            continue
        actions.append(_drift_action(finding, registry))

    plan = {
        "generated_at": isoformat(),
        "dry_run": dry_run,
        "actions": [asdict(action) for action in actions],
        "summary": {
            "total_actions": len(actions),
            "quarantined": len(quarantined_subjects),
        },
    }
    return plan


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan Sentinel remediation actions")
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=False)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    options = parse_args(argv)
    plan = build_plan(options.reports, options.registry, options.dry_run)
    out_path = options.out / "remedy-plan.json"
    write_json(out_path, plan)
    print(f"Sentinel remedy plan written to {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

