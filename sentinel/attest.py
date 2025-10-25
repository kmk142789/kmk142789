from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .utils import digest_payload, encode_payload, read_json, write_json, to_base64


def build_dsse_envelope(report: dict[str, Any]) -> dict[str, Any]:
    payload_type = "application/vnd.sentinel.probe.report+json"
    payload = encode_payload(report)
    digest = digest_payload(report)
    envelope = {
        "payloadType": payload_type,
        "payload": payload,
        "signatures": [
            {
                "keyid": "sentinel-local",
                "sig": to_base64(digest.encode("utf-8")),
            }
        ],
    }
    return {"dsseEnvelope": envelope}


def attest_reports(reports_dir: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    attestations: list[Path] = []
    for report_path in sorted(reports_dir.glob("report-*.json")):
        report = read_json(report_path)
        envelope = build_dsse_envelope(report)
        out_path = out_dir / f"{report_path.stem}.dsse.json"
        write_json(out_path, envelope)
        attestations.append(out_path)
    return attestations


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit Sentinel DSSE attestations")
    parser.add_argument("--from", dest="reports", type=Path, required=True)
    parser.add_argument("--out", dest="out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    options = parse_args(argv)
    attest_reports(options.reports, options.out)
    print(f"Sentinel attestations written to {options.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

