"""Factory helpers for Pulse Weaver services."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from .pulse_bus import PulseBus
from .watchdog import RemediationResult, SelfHealingWatchdog

__all__ = [
    "build_watchdog",
    "build_pulse_bus",
]


def _default_dry_run(event: Mapping[str, object]) -> RemediationResult:
    notes = ["simulated dry-run completed", f"keys: {', '.join(sorted(event.keys()))}"]
    return RemediationResult(success=True, notes=notes, details={"checked": sorted(event.keys())})


def _default_real_run(event: Mapping[str, object]) -> RemediationResult:
    proof = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": {k: event[k] for k in sorted(event)},
    }
    notes = ["simulated fix applied", "proof recorded"]
    return RemediationResult(success=True, proof=proof, notes=notes, details={"status": "applied"})


def build_watchdog(state_dir: Path | str = Path("state")) -> SelfHealingWatchdog:
    return SelfHealingWatchdog(
        state_dir=state_dir,
        dry_run_executor=_default_dry_run,
        real_executor=_default_real_run,
    )


def build_pulse_bus(state_dir: Path | str = Path("state")) -> PulseBus:
    return PulseBus(state_dir=state_dir)
