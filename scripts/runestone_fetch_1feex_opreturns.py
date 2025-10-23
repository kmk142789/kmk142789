"""Utilities for inspecting OP_RETURN messages tied to the 1Feex Mt. Gox wallet."""

from __future__ import annotations

import argparse
import binascii
import json
import sys
from dataclasses import dataclass, asdict
from typing import Iterable, List, Optional

import requests

BLOCKSTREAM_ADDRESS_ENDPOINT = "https://blockstream.info/api/address/{address}/txs"
BLOCKSTREAM_ADDRESS_CHAIN_ENDPOINT = (
    "https://blockstream.info/api/address/{address}/txs/chain/{last_txid}"
)


@dataclass
class OpReturnRecord:
    txid: str
    hex: str
    text: str


def _fetch_page(address: str, last_txid: Optional[str]) -> List[dict]:
    """Download a single page of transactions from Blockstream's REST API."""
    if last_txid is None:
        url = BLOCKSTREAM_ADDRESS_ENDPOINT.format(address=address)
    else:
        url = BLOCKSTREAM_ADDRESS_CHAIN_ENDPOINT.format(
            address=address, last_txid=last_txid
        )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def _op_returns_from_tx(tx: dict) -> Iterable[OpReturnRecord]:
    for vout in tx.get("vout", []):
        if vout.get("scriptpubkey_type") != "op_return":
            continue
        script_hex = vout.get("scriptpubkey", "")
        payload = script_hex[4:]
        try:
            text = binascii.unhexlify(payload).decode("utf-8", "ignore")
        except Exception:
            text = ""
        yield OpReturnRecord(txid=tx["txid"], hex=payload, text=text)


def fetch_op_returns(address: str) -> List[OpReturnRecord]:
    """Collect every OP_RETURN record for the provided address."""
    records: List[OpReturnRecord] = []
    last_txid: Optional[str] = None
    while True:
        page = _fetch_page(address, last_txid)
        if not page:
            break
        for tx in page:
            last_txid = tx["txid"]
            records.extend(_op_returns_from_tx(tx))
        if len(page) < 25:
            break
    return records


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download and optionally persist OP_RETURN payloads seen by the "
            "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF wallet."
        )
    )
    parser.add_argument(
        "--address",
        default="1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF",
        help="Legacy Bitcoin address to inspect",
    )
    parser.add_argument(
        "--output",
        default="reports/runestone_1feex_opreturns.json",
        help="Path to write the JSON report",
    )
    args = parser.parse_args(argv)

    records = fetch_op_returns(args.address)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump([asdict(r) for r in records], fh, indent=2)
    print(f"Wrote {len(records)} OP_RETURN entr{'y' if len(records) == 1 else 'ies'} to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
