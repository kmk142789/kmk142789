"""Utility to capture sanitized metadata for suspicious payloads."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass(slots=True)
class PayloadSummary:
    """Sanitized metadata for a captured payload."""

    label: str
    sha256: str
    size: int
    preview_start: str
    preview_end: str
    format: str
    contains_control: bool
    source: str

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "sha256": self.sha256,
            "size": self.size,
            "preview_start": self.preview_start,
            "preview_end": self.preview_end,
            "format": self.format,
            "contains_control": self.contains_control,
            "source": self.source,
        }


def _read_payload(path: Path | None) -> bytes:
    if path is None:
        raise ValueError("STDIN payload must be provided separately")
    return path.read_bytes()


def _preview(data: bytes, *, head: bool, limit: int = 64) -> str:
    chunk = data[:limit] if head else data[-limit:]
    text = chunk.decode("utf-8", "replace")
    text = text.replace("\n", "\\n").replace("\r", "\\r")
    return text


def _detect_format(data: bytes) -> str:
    stripped = data.strip()
    if not stripped:
        return "empty"
    try:
        text = stripped.decode("utf-8")
    except UnicodeDecodeError:
        return "binary"
    sample = text
    if sample.startswith("0x"):
        sample = sample[2:]
    sample = sample.replace("\n", "").replace("\r", "")
    if sample and all(ch in string.hexdigits for ch in sample):
        return "hex-string"
    if all(ch in string.printable for ch in sample):
        return "text"
    return "mixed"


def _has_control_chars(data: bytes) -> bool:
    return any(ch < 32 and ch not in (9, 10, 13) for ch in data)


def summarise_payload(label: str, data: bytes, source: str) -> PayloadSummary:
    digest = hashlib.sha256(data).hexdigest()
    return PayloadSummary(
        label=label,
        sha256=digest,
        size=len(data),
        preview_start=_preview(data, head=True),
        preview_end=_preview(data, head=False),
        format=_detect_format(data),
        contains_control=_has_control_chars(data),
        source=source,
    )


def _build_label(path: Path | None, idx: int, provided: str | None) -> str:
    if provided:
        return provided
    if path is None:
        return f"stdin-{idx}"
    return path.stem


def _iter_payloads(paths: Sequence[Path], labels: Sequence[str]) -> Iterable[tuple[str, bytes, str]]:
    for idx, path in enumerate(paths):
        label = _build_label(path, idx, labels[idx] if idx < len(labels) else None)
        data = _read_payload(path)
        yield label, data, str(path)


def _write_summary(out_path: Path, entries: List[PayloadSummary], *, timestamp: str | None, note: str | None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": timestamp or _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "note": note,
        "entries": [entry.to_dict() for entry in entries],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record sanitized metadata for suspicious payloads.",
    )
    parser.add_argument("inputs", nargs="*", type=Path, help="Payload files to summarise")
    parser.add_argument("--labels", nargs="*", default=[], help="Optional labels matching each payload")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Path to write the JSON summary")
    parser.add_argument("--note", help="Optional note to include in the summary")
    parser.add_argument("--timestamp", help="Override the generated timestamp (UTC ISO format)")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.inputs:
        raise SystemExit("At least one payload input is required")
    summaries: List[PayloadSummary] = []
    for label, data, source in _iter_payloads(args.inputs, args.labels):
        summaries.append(summarise_payload(label, data, source))
    _write_summary(args.output, summaries, timestamp=args.timestamp, note=args.note)
    print(f"Wrote {len(summaries)} payload summaries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
