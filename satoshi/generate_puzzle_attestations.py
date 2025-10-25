"""Generate Bitcoin puzzle authorship attestations from the known solutions."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Iterable


import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils

from satoshi.puzzle_dataset import iter_puzzle_solutions
from verifier.verify_puzzle_signature import (
    _SECP256K1_N,
    _recover_public_key,
    bitcoin_message_hash,
    pubkey_to_p2pkh_address,
)

DEFAULT_MESSAGE = (
    "PuzzleNN authorship by kmk142789 — attestation sha256 "
    "d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679"
)


class _SafeFormatDict(dict):
    """Dictionary that leaves unknown keys untouched when formatting."""

    def __missing__(self, key: str) -> str:  # pragma: no cover - defensive
        return "{" + key + "}"


def _render_message(template: str, puzzle: int) -> str:
    """Render the attestation message for a puzzle.

    The function supports multiple placeholder styles so that existing scripts can either
    provide an explicit format string (``{puzzle}``, ``{puzzle03}``, ``{puzzle02}``), or rely on
    the historic ``PuzzleNN`` token that appears in earlier datasets.
    """

    substituted = template.replace("PuzzleNN", f"Puzzle{puzzle}")
    mapping = _SafeFormatDict(
        puzzle=puzzle,
        puzzle02=f"{puzzle:02d}",
        puzzle03=f"{puzzle:03d}",
    )
    try:
        return substituted.format_map(mapping)
    except ValueError:
        # ``str.format`` raises ``ValueError`` when encountering a single ``'{'`` or ``'}'``.
        # Preserve the caller-provided template in this edge case.
        return substituted


class AttestationError(RuntimeError):
    """Raised when generating an attestation fails."""


def _normalise_private_key(value: str) -> int:
    stripped = value.strip()
    if not stripped:
        raise AttestationError("Private key is empty")
    try:
        return int(stripped, 16)
    except ValueError as exc:
        raise AttestationError(f"Invalid private key value: {value!r}") from exc


def _derive_public_point(priv: ec.EllipticCurvePrivateKey) -> tuple[int, int]:
    numbers = priv.public_key().public_numbers()
    return numbers.x, numbers.y


def _create_recoverable_signature(private_key_hex: str, message: str) -> tuple[str, tuple[int, int]]:
    secret = _normalise_private_key(private_key_hex)
    if not (1 <= secret < _SECP256K1_N):
        raise AttestationError("Private key out of range for secp256k1")

    private_key = ec.derive_private_key(secret, ec.SECP256K1(), default_backend())
    digest = bitcoin_message_hash(message)

    signature_der = private_key.sign(digest, ec.ECDSA(utils.Prehashed(hashes.SHA256())))
    r, s = utils.decode_dss_signature(signature_der)

    if r == 0 or s == 0:
        raise AttestationError("Invalid signature components produced")

    if s > _SECP256K1_N // 2:
        s = _SECP256K1_N - s

    public_point = _derive_public_point(private_key)

    recid: int | None = None
    for candidate in range(4):
        recovered = _recover_public_key(candidate, digest, r, s)
        if recovered == public_point:
            recid = candidate
            break

    if recid is None:
        raise AttestationError("Unable to recover public key from signature")

    header = 27 + recid + 4  # Flag compressed public key
    raw = bytes([header]) + r.to_bytes(32, "big") + s.to_bytes(32, "big")
    signature = base64.b64encode(raw).decode("ascii")
    return signature, public_point


def iter_attestable_puzzles() -> Iterable[tuple[int, str, str]]:
    for entry in iter_puzzle_solutions():
        if not entry.private_key:
            continue
        yield entry.bits, entry.address, entry.private_key


def build_attestation(puzzle: int, address: str, signature: str, message: str) -> dict[str, object]:
    return {
        "puzzle": puzzle,
        "address": address,
        "message": message,
        "signature": signature,
    }


def generate_attestations(
    output_dir: Path, *, message: str, overwrite: bool, puzzles: set[int] | None
) -> list[Path]:
    written: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for puzzle, address, private_key in iter_attestable_puzzles():
        if puzzles is not None and puzzle not in puzzles:
            continue

        target = output_dir / f"puzzle{puzzle:03d}.json"
        if target.exists() and not overwrite:
            continue

        rendered_message = _render_message(message, puzzle)
        signature, public_point = _create_recoverable_signature(private_key, rendered_message)

        derived_address = pubkey_to_p2pkh_address(public_point, compressed=True)
        if derived_address != address:
            raise AttestationError(
                f"Derived address {derived_address} does not match recorded address {address}"
            )

        payload = build_attestation(puzzle, address, signature, rendered_message)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(target)

    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate message-signature attestations for solved Bitcoin puzzles.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "puzzle-proofs",
        help="Directory to write attestation JSON files (default: satoshi/puzzle-proofs)",
    )
    parser.add_argument(
        "--message",
        default=DEFAULT_MESSAGE,
        help=(
            "Message template to sign. Use 'PuzzleNN', '{puzzle}', '{puzzle02}', or '{puzzle03}' "
            "placeholders to insert the puzzle number (default: standard attestation message)."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate attestations even if the JSON file already exists.",
    )
    parser.add_argument(
        "--puzzle",
        type=int,
        nargs="*",
        help="Optional list of specific puzzle numbers to regenerate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    puzzles = set(args.puzzle) if args.puzzle else None
    written = generate_attestations(
        args.output_dir,
        message=args.message,
        overwrite=args.overwrite,
        puzzles=puzzles,
    )
    for path in written:
        print(f"Wrote {path.relative_to(args.output_dir.parent)}")


if __name__ == "__main__":
    main()
