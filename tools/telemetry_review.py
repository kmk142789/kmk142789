"""CLI utilities for reviewing ethical telemetry output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List
from urllib.parse import urlparse

from src.self_assessment import ReportEmitter
from src.telemetry import ConsentState
from src.telemetry.storage import JsonlTelemetryStorage


def ensure_secure_transport(endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if parsed.scheme != "https":
        raise ValueError("Telemetry uploads require HTTPS transport")


def build_audit_entries(events: Iterable[dict]) -> List[dict]:
    entries: List[dict] = []
    seen = set()
    for event in events:
        context = event["context"]
        pseudo_id = context.get("id") or context.get("pseudonymous_id")
        if pseudo_id is None:
            continue
        if pseudo_id in seen:
            continue
        seen.add(pseudo_id)
        consent = context.get("consent_state", ConsentState.UNKNOWN.value)
        consent_at = context.get("consent_recorded_at")
        session_label = context.get("session_label")
        entries.append(
            {
                "pseudonymous_id": pseudo_id,
                "consent_state": consent,
                "consent_recorded_at": consent_at,
                "session_label": session_label,
            }
        )
    return entries


def create_report(events_path: Path, audit_path: Path | None, output_path: Path | None) -> dict:
    storage = JsonlTelemetryStorage(events_path)
    emitter = ReportEmitter(storage=storage)
    events = list(storage.read())
    if audit_path and audit_path.exists():
        raw_entries = json.loads(audit_path.read_text(encoding="utf-8"))
        audit_entries = list(raw_entries)
    else:
        audit_entries = build_audit_entries([event.model_dump(by_alias=True) for event in events])
    report = emitter.generate(audit_entries)
    payload = {
        "generated_at": report.generated_at.isoformat(),
        "metrics": {
            "total_events": report.metrics.total_events,
            "opted_in_events": report.metrics.opted_in_events,
            "opt_out_blocked": report.metrics.opt_out_blocked,
            "consent_unknown": report.metrics.consent_unknown,
            "opt_in_ratio": report.metrics.opt_in_ratio,
        },
        "notices": report.notices,
        "audit_entries": report.audit_entries,
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--events",
        type=Path,
        default=Path("state/telemetry/events.jsonl"),
        help="Path to telemetry events JSONL file.",
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=None,
        help="Optional path to consent audit entries in JSON format.",
    )
    parser.add_argument(
        "--export",
        type=Path,
        default=None,
        help="Write the compliance report to this JSON path.",
    )
    parser.add_argument(
        "--upload",
        type=str,
        default=None,
        help="Secure HTTPS endpoint to receive the generated report.",
    )
    parser.add_argument(
        "--print", action="store_true", help="Print the report summary to stdout."
    )
    return parser.parse_args()


def upload_report(report: dict, endpoint: str) -> None:
    ensure_secure_transport(endpoint)
    try:
        import urllib.request

        request = urllib.request.Request(
            endpoint,
            data=json.dumps(report).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310 - allowed
            response.read()
    except Exception as exc:  # pragma: no cover - defensive logging path
        raise RuntimeError(f"Failed to upload report: {exc}") from exc


def main() -> None:
    args = parse_args()
    report = create_report(args.events, args.audit, args.export)
    if args.print:
        print(json.dumps(report, indent=2))
    if args.upload:
        upload_report(report, args.upload)


if __name__ == "__main__":
    main()
