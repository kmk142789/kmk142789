"""Utility for launching lightweight ceremonial protocols.

This module is intentionally simple so it can be adapted to future
automation needs.  It provides a handful of whimsical "protocols" that
each demonstrate a different flavor of orchestration logic without
depending on any external services.  The default protocol focuses on
tracking a short series of steps and persisting the results so that
other tooling in the repository can reference them later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Dict, List


@dataclass
class ProtocolResult:
    """Container describing the outcome of a protocol run."""

    name: str
    started_at: str
    completed_at: str
    steps: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation of the result."""

        return {
            "name": self.name,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "steps": self.steps,
            "metadata": self.metadata,
        }


class HarmonyProtocol:
    """A calm protocol that records a few meaningful steps."""

    name = "harmony"

    def run(self) -> ProtocolResult:
        started = datetime.now(timezone.utc)
        steps = [
            "Initialized harmonic field",
            "Calibrated resonance vectors",
            "Logged completion signal",
        ]
        metadata = {
            "status": "complete",
            "mood": "optimistic",
        }
        completed = datetime.now(timezone.utc)

        return ProtocolResult(
            name=self.name,
            started_at=started.isoformat(),
            completed_at=completed.isoformat(),
            steps=steps,
            metadata=metadata,
        )


class PulseProtocol:
    """A slightly livelier protocol that counts rhythmic beats."""

    name = "pulse"

    def __init__(self, beats: int = 4) -> None:
        self.beats = beats

    def run(self) -> ProtocolResult:
        started = datetime.now(timezone.utc)
        steps = [f"Beat {index + 1}" for index in range(self.beats)]
        metadata = {
            "status": "complete",
            "beats": str(self.beats),
        }
        completed = datetime.now(timezone.utc)

        return ProtocolResult(
            name=self.name,
            started_at=started.isoformat(),
            completed_at=completed.isoformat(),
            steps=steps,
            metadata=metadata,
        )


PROTOCOLS = {
    HarmonyProtocol.name: HarmonyProtocol,
    PulseProtocol.name: PulseProtocol,
}


def initiate_protocol(protocol_name: str, *, beats: int = 4) -> ProtocolResult:
    """Instantiate and run one of the available protocols."""

    try:
        protocol_cls = PROTOCOLS[protocol_name]
    except KeyError as exc:  # pragma: no cover - defensive path
        available = ", ".join(sorted(PROTOCOLS))
        raise ValueError(f"Unknown protocol '{protocol_name}'. Choose from: {available}") from exc

    if protocol_cls is PulseProtocol:
        protocol = protocol_cls(beats=beats)
    else:
        protocol = protocol_cls()
    return protocol.run()


def persist_result(result: ProtocolResult, output_path: Path) -> None:
    """Write a protocol result to disk as JSON."""

    output_path.write_text(json.dumps(result.to_dict(), indent=2))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Initiate a lightweight ceremonial protocol")
    parser.add_argument("--protocol", choices=sorted(PROTOCOLS), default="harmony")
    parser.add_argument("--beats", type=int, default=4, help="Number of beats for the pulse protocol")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("protocol_result.json"),
        help="File path for persisting the protocol result",
    )
    args = parser.parse_args()

    result = initiate_protocol(args.protocol, beats=args.beats)
    persist_result(result, args.output)
    print(f"Protocol '{result.name}' completed. Result saved to {args.output}.")


if __name__ == "__main__":
    main()
