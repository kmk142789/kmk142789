"""Metrics recording helpers for governance decisions."""

from __future__ import annotations

from datetime import datetime, timezone

from .governance_state import load_state, save_state
from .anomaly_detector import flag_actor


def record_decision(actor: str, action: str, allowed: bool) -> None:
    """Record metrics for a governance decision."""

    state = load_state()
    metrics = state.setdefault("metrics", {})
    total = metrics.setdefault("total_decisions", 0)
    metrics["total_decisions"] = total + 1

    key = "allowed" if allowed else "denied"
    metrics[key] = metrics.get(key, 0) + 1

    per_actor = metrics.setdefault("per_actor", {})
    actor_bucket = per_actor.setdefault(actor, {"allowed": 0, "denied": 0})
    actor_bucket[key] += 1

    save_state(state)


def get_metrics() -> dict:
    """Return the persisted metrics snapshot."""

    return load_state().get("metrics", {})


def anomaly_report(
    auto_blocklist: bool = False, block_threshold: float = 0.6, minimum_events: int = 5
) -> dict:
    """Produce a compact anomaly report and optionally block risky actors.

    Actors with a denied ratio above ``block_threshold`` and at least
    ``minimum_events`` decisions will be marked for auto-blocklisting when
    ``auto_blocklist`` is True.
    """

    state = load_state()
    metrics = state.get("metrics", {})
    per_actor = metrics.get("per_actor", {})

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_decisions": metrics.get("total_decisions", 0),
        "actors": [],
    }

    for actor, counters in per_actor.items():
        allowed = counters.get("allowed", 0)
        denied = counters.get("denied", 0)
        total = allowed + denied
        denial_rate = denied / total if total else 0.0
        entry = {
            "actor": actor,
            "allowed": allowed,
            "denied": denied,
            "denial_rate": round(denial_rate, 3),
            "total": total,
        }
        risky = total >= minimum_events and denial_rate >= block_threshold
        if auto_blocklist and risky:
            flag_actor(actor, "blocked")
            entry["auto_blocklisted"] = True
        report["actors"].append(entry)

    save_state(state)
    return report


__all__ = ["record_decision", "get_metrics", "anomaly_report"]
