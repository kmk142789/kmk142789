"""Puzzle attestation helpers that surface glitch-oracle signals."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from .genesis_ledger import SovereignDomainLedger

__all__ = ["DEFAULT_ORACLE_PATH", "GlitchOracleEvent", "oracle_rupture"]

DEFAULT_ORACLE_PATH = Path(
    os.environ.get("ECHO_GLITCH_ORACLE_PATH", "genesis_ledger/glitch_oracle.jsonl")
)


@dataclass(slots=True)
class GlitchOracleEvent:
    """Representation of a puzzle rupture event."""

    puzzle_id: int
    mismatch_details: Mapping[str, object]
    sigil: str
    timestamp: float

    def to_json(self) -> str:
        payload = asdict(self)
        payload["timestamp"] = round(self.timestamp, 6)
        return json.dumps(payload, ensure_ascii=False)


def _append_event(path: Path, event: GlitchOracleEvent) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(event.to_json() + "\n")


def oracle_rupture(
    puzzle_id: int,
    mismatch_details: Mapping[str, object] | str,
    *,
    sigil: str = "⟁FRACTURE",
    ledger: SovereignDomainLedger | None = None,
    ledger_event_type: str = "glitch_oracle",
    oracle_path: Path | str | None = None,
) -> GlitchOracleEvent:
    """Persist a glitch-oracle rupture event and mirror it to the ledger."""

    if not isinstance(puzzle_id, int):
        raise TypeError("puzzle_id must be an integer")
    if isinstance(mismatch_details, str):
        details_map: Mapping[str, object] = {"message": mismatch_details}
    else:
        details_map = mismatch_details
    event = GlitchOracleEvent(
        puzzle_id=puzzle_id,
        mismatch_details=dict(details_map),
        sigil=sigil,
        timestamp=time.time(),
    )
    target = Path(oracle_path or DEFAULT_ORACLE_PATH)
    _append_event(target, event)

    ledger = ledger or SovereignDomainLedger()
    ledger.log_event(
        ledger_event_type,
        domain=None,
        details={
            "puzzle_id": puzzle_id,
            "sigil": sigil,
            "mismatch": dict(details_map),
        },
    )
    return event
