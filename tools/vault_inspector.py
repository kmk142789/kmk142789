#!/usr/bin/env python3
"""Inspect encrypted vault payload metadata.

This helper normalises JSON records that contain fields such as ``address``,
``createTime``, ``encryedInfo``, ``kekId``, and ``version``. The script does
not attempt to decrypt the payload. Instead it extracts lightweight metadata
including decoded sizes, hashes, and a human-readable creation timestamp. The
output helps confirm that the payload structure is intact before handing it to
an offline decryption workflow.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class VaultSummary:
    """Container describing decoded vault metadata."""

    address: str
    create_time_ms: int
    create_time_iso: str
    encrypted_b64_length: int
    encrypted_byte_length: int
    encrypted_sha256: str
    kek_id: str
    version: str

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "address": self.address,
            "create_time_ms": self.create_time_ms,
            "create_time_iso": self.create_time_iso,
            "encrypted": {
                "base64_length": self.encrypted_b64_length,
                "byte_length": self.encrypted_byte_length,
                "sha256": self.encrypted_sha256,
            },
            "kek_id": self.kek_id,
            "version": self.version,
        }


def _load_payload(source: str | Path) -> Mapping[str, Any]:
    path = Path(source)
    if str(path) == "-":
        raw_text = Path("/dev/stdin").read_text()
    else:
        raw_text = path.read_text()
    payload = json.loads(raw_text)
    if not isinstance(payload, Mapping):
        raise ValueError("vault payload must be a JSON object")
    return payload


def _normalise_version(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not value.is_integer():
            return f"{value:.6g}"
        return str(int(value))
    raise TypeError("version must be a string or numeric value")


def _decode_encrypted_blob(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:  # noqa: BLE001 - surface decoding issues clearly
        raise ValueError("encryedInfo is not valid base64 data") from exc


def summarise_payload(payload: Mapping[str, Any]) -> VaultSummary:
    try:
        address = str(payload["address"])
    except KeyError as exc:
        raise ValueError("vault payload missing 'address'") from exc

    try:
        create_time_ms = int(payload["createTime"])
    except KeyError as exc:
        raise ValueError("vault payload missing 'createTime'") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("createTime must be an integer timestamp in ms") from exc

    try:
        encoded_blob = str(payload["encryedInfo"])
    except KeyError as exc:
        raise ValueError("vault payload missing 'encryedInfo'") from exc

    decoded_blob = _decode_encrypted_blob(encoded_blob)
    sha256 = hashlib.sha256(decoded_blob).hexdigest()

    try:
        kek_id = str(payload["kekId"])
    except KeyError as exc:
        raise ValueError("vault payload missing 'kekId'") from exc

    try:
        version_value = payload["version"]
    except KeyError as exc:
        raise ValueError("vault payload missing 'version'") from exc

    version = _normalise_version(version_value)

    created_at_iso = datetime.fromtimestamp(
        create_time_ms / 1000, tz=timezone.utc
    ).isoformat()

    return VaultSummary(
        address=address,
        create_time_ms=create_time_ms,
        create_time_iso=created_at_iso,
        encrypted_b64_length=len(encoded_blob),
        encrypted_byte_length=len(decoded_blob),
        encrypted_sha256=sha256,
        kek_id=kek_id,
        version=version,
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect metadata for encrypted vault payloads",
    )
    parser.add_argument(
        "source",
        help="Path to a JSON file (use '-' to read from stdin)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    summary = summarise_payload(_load_payload(args.source))

    if args.json:
        print(json.dumps(summary.to_dict(), indent=2))
    else:
        print(f"Address:          {summary.address}")
        print(
            f"Created:          {summary.create_time_iso} "
            f"({summary.create_time_ms} ms)"
        )
        print(
            "Encrypted blob:   "
            f"{summary.encrypted_byte_length} bytes (base64 len {summary.encrypted_b64_length})"
        )
        print(f"Encrypted SHA256: {summary.encrypted_sha256}")
        print(f"KEK identifier:   {summary.kek_id}")
        print(f"Version:          {summary.version}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
