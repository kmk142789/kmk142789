"""Bulk signing helper with optional Echo Vault integration."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from getpass import getpass
from typing import Any, Dict, Iterable, List, Optional

from ..vault import VaultPolicy, decode_private_key, open_vault, sign_payload
from ..vault.crypto import zeroize

__all__ = ["bulk_signer_cli"]


@dataclass
class SigningEntry:
    label: str
    fmt: str
    key: str
    payloads: List[str]
    tags: List[str]
    policy: Optional[Dict[str, Any]] = None


def _load_manifest(path: str) -> List[SigningEntry]:
    if path == "-":
        data = json.load(sys.stdin)
    else:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    if isinstance(data, dict) and "entries" in data:
        data = data["entries"]
    if not isinstance(data, list):
        raise ValueError("manifest must be a list of entries")
    entries: List[SigningEntry] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("manifest entries must be objects")
        label = item.get("label")
        key = item.get("key")
        payloads = item.get("payloads")
        if not isinstance(label, str) or not isinstance(key, str):
            raise ValueError("manifest entries require 'label' and 'key' fields")
        if not isinstance(payloads, list) or not all(isinstance(p, str) for p in payloads):
            raise ValueError("manifest entries require 'payloads' as a list of hex strings")
        fmt = item.get("fmt", "hex")
        tags = item.get("tags", [])
        if not isinstance(tags, list):
            raise ValueError("tags must be a list")
        policy = item.get("policy")
        entries.append(
            SigningEntry(
                label=label,
                fmt=fmt,
                key=key,
                payloads=payloads,
                tags=[str(tag) for tag in tags],
                policy=policy if isinstance(policy, dict) else None,
            )
        )
    return entries


def _sign_with_vault(
    entries: Iterable[SigningEntry],
    *,
    vault_path: str,
    label_prefix: str,
    deterministic: bool,
) -> List[Dict[str, Any]]:
    passphrase = getpass("Vault passphrase: ")
    vault = open_vault(vault_path, passphrase)
    results: List[Dict[str, Any]] = []
    try:
        for entry in entries:
            record = vault.import_key(
                label=f"{label_prefix}{entry.label}",
                key=entry.key,
                fmt=entry.fmt,
                tags=entry.tags,
                policy=VaultPolicy(**entry.policy) if entry.policy else None,
            )
            signatures: List[Dict[str, Any]] = []
            for payload_hex in entry.payloads:
                payload = bytes.fromhex(payload_hex)
                result = vault.sign(
                    record.id,
                    payload,
                    rand_nonce=not deterministic,
                )
                signatures.append(
                    {
                        "payload": payload_hex,
                        "signature": result["sig"],
                        "ts": result["ts"],
                        "record_id": record.id,
                        "algo": result["algo"],
                    }
                )
            results.append(
                {
                    "label": record.label,
                    "record_id": record.id,
                    "signatures": signatures,
                }
            )
    finally:
        vault.close()
    return results


def _sign_locally(
    entries: Iterable[SigningEntry],
    *,
    label_prefix: str,
    deterministic: bool,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for entry in entries:
        key_buffer = bytearray(decode_private_key(entry.fmt, entry.key))
        try:
            signatures: List[Dict[str, Any]] = []
            for payload_hex in entry.payloads:
                payload = bytes.fromhex(payload_hex)
                signature = sign_payload(
                    bytes(key_buffer),
                    payload,
                    rand_nonce=not deterministic,
                )
                signatures.append(
                    {
                        "payload": payload_hex,
                        "signature": signature.hex(),
                        "algo": "secp256k1+sha256",
                    }
                )
        finally:
            zeroize(key_buffer)
        results.append(
            {
                "label": f"{label_prefix}{entry.label}",
                "signatures": signatures,
            }
        )
    return results


def bulk_signer_cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Bulk signer for Echo payloads")
    parser.add_argument("manifest", help="Path to JSON manifest (use - for stdin)")
    parser.add_argument("--vault", help="Optional vault path for persistent storage")
    parser.add_argument("--label-prefix", default="", help="Prefix applied to imported labels")
    parser.add_argument("--deterministic", action="store_true", help="Use deterministic nonces")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    args = parser.parse_args(argv)
    entries = _load_manifest(args.manifest)

    if args.vault:
        results = _sign_with_vault(
            entries,
            vault_path=args.vault,
            label_prefix=args.label_prefix,
            deterministic=args.deterministic,
        )
    else:
        results = _sign_locally(
            entries,
            label_prefix=args.label_prefix,
            deterministic=args.deterministic,
        )

    if args.pretty:
        print(json.dumps(results, indent=2))
    else:
        print(json.dumps(results))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(bulk_signer_cli())
