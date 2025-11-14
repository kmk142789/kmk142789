"""Verify JSON claim files that bundle canonical statements and signatures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

SUPPORTED_ALGOS = {"ecdsa-secp256k1", "hmac-sha256"}


class ClaimVerificationError(Exception):
    """Raised when a claim file is malformed or cannot be verified."""


def _load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise ClaimVerificationError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ClaimVerificationError(f"invalid JSON: {exc}") from exc


def _public_key_from_hex(pub_hex: str) -> ec.EllipticCurvePublicKey:
    if len(pub_hex) != 128:
        raise ClaimVerificationError(
            "expected 128 hex characters for uncompressed secp256k1 public key"
        )
    try:
        x = int(pub_hex[:64], 16)
        y = int(pub_hex[64:], 16)
    except ValueError as exc:
        raise ClaimVerificationError("public key contains non-hex characters") from exc
    numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
    return numbers.public_key()


def _verify_ecdsa_claim(canonical: bytes, signature: dict) -> bool:
    try:
        pub_hex = signature["pub"]
        sig_hex = signature["sig"]
    except KeyError as exc:
        raise ClaimVerificationError(f"missing signature field: {exc.args[0]}") from exc

    public_key = _public_key_from_hex(pub_hex)
    try:
        signature_bytes = bytes.fromhex(sig_hex)
    except ValueError as exc:
        raise ClaimVerificationError("signature contains non-hex characters") from exc

    try:
        public_key.verify(signature_bytes, canonical, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        print("FAIL: signature mismatch")
        return False
    return True


def verify_claim(path: Path) -> bool:
    """Verify a claim file and print a summary for CLI usage."""

    data = _load_json(path)
    try:
        canonical_text = data["canonical"]
        signature_block = data["signature"]
    except KeyError as exc:
        raise ClaimVerificationError(f"claim missing required field: {exc.args[0]}") from exc

    if not isinstance(canonical_text, str):
        raise ClaimVerificationError("canonical text must be a string")
    if not isinstance(signature_block, dict):
        raise ClaimVerificationError("signature block must be an object")

    algo = signature_block.get("algo")
    if algo not in SUPPORTED_ALGOS:
        raise ClaimVerificationError(f"unsupported signature algorithm: {algo}")

    canonical_bytes = canonical_text.encode("utf-8")

    if algo == "hmac-sha256":
        print(f"{path}: HMAC claim cannot be independently verified without the secret key.")
        return True

    ok = _verify_ecdsa_claim(canonical_bytes, signature_block)
    if ok:
        print(f"{path}: OK (ecdsa-secp256k1)")
    else:
        print(f"{path}: FAIL (ecdsa-secp256k1)")
    return ok


def verify_many(paths: Sequence[Path]) -> bool:
    result = True
    for path in paths:
        try:
            result = verify_claim(path) and result
        except ClaimVerificationError as exc:
            print(f"{path}: {exc}")
            result = False
    return result


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify canonical claim files.")
    parser.add_argument("files", nargs="+", type=Path, help="Claim files to verify")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    ok = verify_many(args.files)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
