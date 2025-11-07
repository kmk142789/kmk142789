"""Continuity anchor agent for the Echo governance pulse log.

This module keeps a tamper-evident rolling digest of the governance
pulse log. Every pulse entry is chained to the previous one using a
SHA-256 hash of the pulse contents plus the prior anchor digest. The
resulting anchor summary can be notarised externally to provide
immutability guarantees for the pulse history.

The module exposes a small public API so it can be imported by other
parts of the repository or executed directly as a script.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import pathlib
from dataclasses import dataclass
from typing import Iterable, List, Mapping, MutableMapping, Sequence


AGENT_ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_PULSE_LOG = AGENT_ROOT / "pulse_log.json"
DEFAULT_ANCHOR_LOG = AGENT_ROOT / "anchor_log.json"


@dataclass
class PulseRecord:
    """Representation of a single pulse event."""

    time: str
    event: str
    digest: str
    payload: Mapping[str, object]

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "PulseRecord":
        missing = [field for field in ("time", "event", "digest") if field not in data]
        if missing:
            raise ValueError(f"pulse record missing required fields: {', '.join(missing)}")
        return cls(
            time=str(data["time"]),
            event=str(data["event"]),
            digest=str(data["digest"]),
            payload=dict(data),
        )


def load_pulses(path: pathlib.Path = DEFAULT_PULSE_LOG) -> List[PulseRecord]:
    """Load pulse records from ``path``."""

    if not path.exists():
        raise FileNotFoundError(path)

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover - error path
        raise ValueError(f"invalid JSON in {path}") from exc

    if not isinstance(raw, Sequence):
        raise ValueError("pulse log must contain a JSON array")

    records: List[PulseRecord] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, Mapping):
            raise ValueError(f"pulse entry {index} is not an object")
        records.append(PulseRecord.from_mapping(entry))
    return records


def build_anchor_chain(pulses: Iterable[PulseRecord]) -> List[MutableMapping[str, object]]:
    """Create a rolling digest chain for the supplied pulses."""

    anchors: List[MutableMapping[str, object]] = []
    previous_digest: str | None = None

    for pulse in pulses:
        base = f"{pulse.time}|{pulse.event}|{pulse.digest}|{previous_digest or ''}"
        anchor_digest = hashlib.sha256(base.encode()).hexdigest()

        anchor_entry: MutableMapping[str, object] = dict(pulse.payload)
        anchor_entry.update({
            "anchor": anchor_digest,
            "previous_anchor": previous_digest,
        })
        anchors.append(anchor_entry)
        previous_digest = anchor_digest

    return anchors


def write_anchor_log(
    anchors: Sequence[Mapping[str, object]],
    *,
    anchored_at: _dt.datetime | None = None,
    output_path: pathlib.Path = DEFAULT_ANCHOR_LOG,
) -> Mapping[str, object]:
    """Persist the anchor summary to ``output_path``."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    anchored_at = anchored_at or _dt.datetime.utcnow()

    payload = {
        "anchored_at": anchored_at.replace(tzinfo=None).isoformat() + "Z",
        "chain_length": len(anchors),
        "last_anchor": anchors[-1]["anchor"] if anchors else None,
        "anchors": list(anchors),
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def compute_anchor(
    *,
    pulse_path: pathlib.Path = DEFAULT_PULSE_LOG,
    anchor_path: pathlib.Path = DEFAULT_ANCHOR_LOG,
) -> Mapping[str, object]:
    """Read pulse records, build the anchor chain and persist it."""

    if not pulse_path.exists():
        return {"status": "no_pulse_log", "pulse_path": str(pulse_path)}

    pulses = load_pulses(pulse_path)
    anchors = build_anchor_chain(pulses)
    return write_anchor_log(anchors, output_path=anchor_path)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute the governance continuity anchor")
    parser.add_argument(
        "--pulse-log",
        dest="pulse_log",
        type=pathlib.Path,
        default=DEFAULT_PULSE_LOG,
        help="Path to the pulse_log.json file (default: %(default)s)",
    )
    parser.add_argument(
        "--anchor-log",
        dest="anchor_log",
        type=pathlib.Path,
        default=DEFAULT_ANCHOR_LOG,
        help="Where to write the anchor summary (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    summary = compute_anchor(pulse_path=args.pulse_log, anchor_path=args.anchor_log)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
