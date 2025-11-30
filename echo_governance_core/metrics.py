"""Metrics recording helpers for governance decisions."""

from __future__ import annotations

from .governance_state import load_state, save_state


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


__all__ = ["record_decision", "get_metrics"]
