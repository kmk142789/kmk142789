#!/usr/bin/env python3
"""Echo From Skeleton - derive ETH & BTC keys from a skeleton key (phrase or file)."""
from __future__ import annotations

import argparse
import json
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
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--phrase", help="skeleton key phrase")
    group.add_argument("--file", help="path to skeleton key file (any bytes)")
    parser.add_argument("--ns", default="core", help="namespace (e.g., core, eth, btc, harmonix)")
    parser.add_argument("--index", type=int, default=0, help="derivation index")
    parser.add_argument("--testnet", action="store_true", help="derive a testnet WIF")
    parser.add_argument("--json", action="store_true", help="output JSON")
    return parser


def _derive_payload(args: argparse.Namespace) -> dict[str, object]:
    secret = (
        read_secret_from_phrase(args.phrase)
        if args.phrase is not None
        else read_secret_from_file(args.file)
    )
    derived = derive_from_skeleton(secret, args.ns, args.index, testnet_btc=args.testnet)
    return {
        "namespace": args.ns,
        "index": args.index,
        "eth_priv_hex": derived.priv_hex,
        "eth_address": derived.eth_address,
        "btc_wif": derived.btc_wif,
        "btc_network": "testnet" if args.testnet else "mainnet",
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    payload = _derive_payload(args)

    if args.json:
        print(json.dumps(payload))
    else:
        print(f"Namespace: {payload['namespace']}")
        print(f"Index: {payload['index']}")
        print(f"ETH private key (hex): {payload['eth_priv_hex']}")
        eth_address = payload["eth_address"] or "(install 'ecdsa' to compute)"
        print(f"ETH address: {eth_address}")
        print(f"BTC WIF (compressed): {payload['btc_wif']}")
        if args.testnet:
            print("Network: testnet")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
