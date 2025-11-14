#!/usr/bin/env python3
"""Echo From Skeleton - derive ETH & BTC keys from a skeleton key (phrase or file)."""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Iterable, Optional

from skeleton_key_core import (
    derive_from_skeleton,
    read_secret_from_file,
    read_secret_from_phrase,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Echo From Skeleton - derive ETH & BTC keys from a skeleton key",
    )
    secret_group = parser.add_mutually_exclusive_group(required=True)
    secret_group.add_argument("--phrase", help="skeleton key phrase")
    secret_group.add_argument("--file", help="path to skeleton key file (any bytes)")
    secret_group.add_argument(
        "--stdin",
        action="store_true",
        help="read the skeleton key phrase from standard input",
    )
    parser.add_argument("--ns", default="core", help="namespace (e.g., core, eth, btc, harmonix)")
    parser.add_argument("--index", type=int, default=0, help="derivation index")
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="number of sequential derivations to produce (>=1)",
    )
    parser.add_argument("--testnet", action="store_true", help="derive a testnet WIF")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", help="output JSON")
    output_group.add_argument("--csv", action="store_true", help="output CSV")
    parser.add_argument(
        "--output",
        type=Path,
        help="optional path to write the payload (JSON by default)",
    )
    return parser


def _derive_payloads(args: argparse.Namespace) -> list[dict[str, object]]:
    secret = (
        read_secret_from_phrase(args.phrase)
        if args.phrase is not None
        else read_secret_from_file(args.file)
    )
    payloads: list[dict[str, object]] = []
    for offset in range(args.count):
        index = args.index + offset
        derived = derive_from_skeleton(secret, args.ns, index, testnet_btc=args.testnet)
        payloads.append(
            {
                "namespace": args.ns,
                "index": index,
                "eth_priv_hex": derived.priv_hex,
                "eth_address": derived.eth_address,
                "btc_wif": derived.btc_wif,
                "btc_network": "testnet" if args.testnet else "mainnet",
            }
        )
    return payloads


def _print_payloads(payloads: list[dict[str, object]], show_testnet: bool) -> None:
    separator_needed = len(payloads) > 1
    for position, payload in enumerate(payloads, start=1):
        if separator_needed and position > 1:
            print("-" * 32)
        print(f"Namespace: {payload['namespace']}")
        print(f"Index: {payload['index']}")
        print(f"ETH private key (hex): {payload['eth_priv_hex']}")
        eth_address = payload["eth_address"] or "(install 'ecdsa' to compute)"
        print(f"ETH address: {eth_address}")
        print(f"BTC WIF (compressed): {payload['btc_wif']}")
        if show_testnet:
            print("Network: testnet")


def _payloads_to_csv(payloads: list[dict[str, object]]) -> str:
    fieldnames = [
        "namespace",
        "index",
        "eth_priv_hex",
        "eth_address",
        "btc_wif",
        "btc_network",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(payloads)
    return buffer.getvalue().rstrip()


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.stdin:
        phrase = sys.stdin.read().strip()
        if not phrase:
            parser.error("--stdin was provided but no data was read from standard input")
        args.phrase = phrase

    if args.count < 1:
        parser.error("--count must be at least 1")

    payloads = _derive_payloads(args)
    payload_data: dict[str, object] | list[dict[str, object]]
    payload_data = payloads[0] if len(payloads) == 1 else payloads

    file_contents: str
    if args.csv:
        csv_payload = _payloads_to_csv(payloads)
        print(csv_payload)
        file_contents = csv_payload
    elif args.json:
        json_payload = json.dumps(payload_data, indent=2)
        print(json_payload)
        file_contents = json_payload
    else:
        _print_payloads(payloads, args.testnet)
        file_contents = json.dumps(payload_data, indent=2)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(file_contents)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
