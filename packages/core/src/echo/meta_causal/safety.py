"""Safety and integrity helpers for the meta causal awareness engine."""

from __future__ import annotations

from typing import Any, Dict, List

if False:  # pragma: no cover - used only for type checkers
    from .engine import MetaCausalAwarenessEngine


def audit_integrity(engine: "MetaCausalAwarenessEngine") -> Dict[str, Any]:
    """Return a lightweight integrity report for *engine*."""

    snapshot = engine.snapshot()
    observation_ids = {entry["id"] for entry in snapshot.observations}
    issues: List[Dict[str, Any]] = []
    for link in snapshot.links:
        if link["cause"] not in observation_ids:
            issues.append({
                "type": "dangling_cause",
                "link": link,
            })
        if link["effect"] not in observation_ids:
            issues.append({
                "type": "dangling_effect",
                "link": link,
            })
        if link["cause"] == link["effect"]:
            issues.append({
                "type": "self_loop",
                "link": link,
            })
    status = "ok" if not issues else "attention"
    return {
        "status": status,
        "issue_count": len(issues),
        "issues": issues,
        "observation_count": len(observation_ids),
        "link_count": len(snapshot.links),
    }


__all__ = ["audit_integrity"]

