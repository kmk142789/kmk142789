from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .utils import isoformat, write_json


@dataclass(frozen=True)
class RequiredAction:
    id: str
    subject: str
    category: str
    severity: str
    status: str
    description: str
    evidence: dict[str, Any]


def write_required_actions(reports: Iterable[Any], output_dir: Path) -> dict[str, Any]:
    actions: list[RequiredAction] = []
    for report in reports:
        for finding in report.findings:
            if finding.status not in {"warning", "error"}:
                continue
            actions.append(
                RequiredAction(
                    id=_action_id(finding.subject, finding.message),
                    subject=finding.subject,
                    category=report.name,
                    severity=_severity_for_status(finding.status),
                    status="required",
                    description=finding.message,
                    evidence={
                        "probe": report.name,
                        "status": finding.status,
                        "data": dict(finding.data),
                    },
                )
            )

    payload = {
        "generated_at": isoformat(),
        "actions": [asdict(action) for action in actions],
        "summary": {
            "total_actions": len(actions),
            "critical": sum(1 for action in actions if action.severity == "critical"),
            "high": sum(1 for action in actions if action.severity == "high"),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "required-actions.json", payload)
    return payload


def _action_id(subject: str, message: str) -> str:
    return hashlib.sha256(f"{subject}:{message}".encode("utf-8")).hexdigest()[:16]


def _severity_for_status(status: str) -> str:
    return {"error": "critical", "warning": "high"}.get(status, "medium")


__all__ = ["RequiredAction", "write_required_actions"]
