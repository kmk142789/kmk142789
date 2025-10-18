#!/usr/bin/env python3
"""Sign puzzle proof messages with a provided WIF private key.

This helper complements :mod:`verifier.verify_puzzle_signature` by
producing canonical Bitcoin ``signmessage`` signatures for the JSON
records stored in ``satoshi/puzzle-proofs``. It accepts a WIF key,
validates that it belongs to the target address, signs the embedded
message, and optionally updates the JSON document in-place.
"""

from __future__ import annotations

import argparse
import base64
import json
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code.wif_validator import WIFValidationError, validate_wif
from verifier.verify_puzzle_signature import (
    _SECP256K1_G,
    _SECP256K1_N,
    _scalar_multiply,
    bitcoin_message_hash,
    pubkey_to_p2pkh_address,
)


@dataclass(frozen=True)
class ProofDocument:
    """Structured representation of a puzzle proof file."""

    puzzle: int
    address: str
    message: str
    signature: str
    path: Path

    @classmethod
    def load(cls, path: Path) -> "ProofDocument":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            puzzle=payload["puzzle"],
            address=payload["address"],
            message=payload["message"],
            signature=payload.get("signature", ""),
            path=path,
        )

    def replace_signature(self, signature: str) -> None:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        payload["signature"] = signature
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def _derive_address(private_key_hex: str, compressed: bool) -> str:
    key_int = int(private_key_hex, 16)
    public_point = _scalar_multiply(key_int, _SECP256K1_G)
    if public_point is None:
        raise ValueError("Scalar multiplication returned point at infinity")
    return pubkey_to_p2pkh_address(public_point, compressed)


def _encode_signature(r: int, s: int, recid: int, compressed: bool) -> str:
    header = 27 + recid + (4 if compressed else 0)
    raw = bytes([header]) + r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return base64.b64encode(raw).decode("ascii")


def _compute_signature(private_key_hex: str, message: str, compressed: bool) -> str:
    private_key_int = int(private_key_hex, 16)
    digest = bitcoin_message_hash(message)
    z = int.from_bytes(digest, "big")

    while True:
        k = secrets.randbelow(_SECP256K1_N - 1) + 1
        point = _scalar_multiply(k, _SECP256K1_G)
        if point is None:
            continue
        r = point[0] % _SECP256K1_N
        if r == 0:
            continue
        k_inv = pow(k, -1, _SECP256K1_N)
        s = (k_inv * (z + r * private_key_int)) % _SECP256K1_N
        if s == 0:
            continue
        if s > _SECP256K1_N // 2:
            s = _SECP256K1_N - s
        recid = 0
        if point[0] >= _SECP256K1_N:
            recid |= 2
        if point[1] & 1:
            recid |= 1
        return _encode_signature(r, s, recid, compressed)


def sign_proof(document: ProofDocument, wif: str, update: bool = False) -> str:
    try:
        wif_details = validate_wif(wif)
    except WIFValidationError as exc:
        raise SystemExit(f"Invalid WIF: {exc}") from exc

    derived_address = _derive_address(wif_details.private_key_hex, wif_details.compressed)
    if derived_address != document.address:
        raise SystemExit(
            "The supplied WIF does not correspond to the proof address.\n"
            f"  expected: {document.address}\n"
            f"  derived : {derived_address}"
        )

    signature = _compute_signature(
        wif_details.private_key_hex, document.message, wif_details.compressed
    )

    if update:
        document.replace_signature(signature)

    return signature


def load_wif_from_file(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise SystemExit(f"Could not read WIF file {path}: {exc}") from exc
    if not text:
        raise SystemExit(f"WIF file {path} is empty")
    return text


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proof", type=Path, help="Path to a puzzle proof JSON file")
    parser.add_argument("--wif", dest="wif", help="Inline WIF string to use for signing")
    parser.add_argument("--wif-file", dest="wif_file", type=Path, help="Path to a file containing the WIF")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Rewrite the JSON document with the newly produced signature",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_cli()
    args = parser.parse_args(argv)

    if not args.wif and not args.wif_file:
        parser.error("Either --wif or --wif-file must be provided")

    wif_value = args.wif or load_wif_from_file(args.wif_file)

    document = ProofDocument.load(args.proof)
    signature = sign_proof(document, wif_value, update=args.update)
    print(signature)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
