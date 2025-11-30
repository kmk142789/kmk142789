"""Basic anomaly detection to flag or block actors."""

from __future__ import annotations

from .governance_state import load_state, save_state


def _ensure_structures(state: dict) -> dict:
    actors = state.setdefault("actors", {})
    for _, info in actors.items():
        info.setdefault("flags", [])
    return state


def flag_actor(actor: str, reason: str) -> None:
    """Add an anomaly flag to an actor profile."""

    state = load_state()
    state = _ensure_structures(state)
    info = state["actors"].setdefault(actor, {"roles": [], "flags": []})
    if reason not in info["flags"]:
        info["flags"].append(reason)
    save_state(state)


def is_blocked(actor: str) -> bool:
    """Return True if the actor is blocked or marked suspicious."""

    state = load_state()
    info = state.get("actors", {}).get(actor, {})
    flags = info.get("flags", [])
    return "blocked" in flags or "suspicious" in flags


def evaluate_anomalies() -> None:
    """Evaluate simple anomaly rules and flag actors when thresholds hit."""

    state = load_state()
    metrics = state.get("metrics", {})
    per_actor = metrics.get("per_actor", {})
    actors = state.setdefault("actors", {})

    for actor, counts in per_actor.items():
        denied = counts.get("denied", 0)
        if denied > 50:
            info = actors.setdefault(actor, {"roles": [], "flags": []})
            if "suspicious" not in info["flags"]:
                info["flags"].append("suspicious")

    save_state(state)


__all__ = ["flag_actor", "is_blocked", "evaluate_anomalies"]
