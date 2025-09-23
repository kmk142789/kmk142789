"""Utility for validating Base58Check-encoded Bitcoin WIF private keys.

This script was created to complement the cryptographic
artifacts stored in this repository.  It accepts one or more
Wallet Import Format (WIF) strings, verifies their Base58Check
checksums, inspects the payload to determine the network and
compression status, and prints a concise report.  The tool does
not derive public keys or addresses—it focuses on proving that
a given WIF is internally consistent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BASE58_INDEX = {char: index for index, char in enumerate(BASE58_ALPHABET)}


class WIFValidationError(ValueError):
    """Raised when a WIF string fails validation."""


@dataclass
class WIFDetails:
    """Structured data describing a decoded WIF payload."""

    wif: str
    network: str
    compressed: bool
    private_key_hex: str
    payload_length: int

    def to_dict(self) -> dict:
        return {
            "wif": self.wif,
            "network": self.network,
            "compressed": self.compressed,
            "private_key_hex": self.private_key_hex,
            "payload_length": self.payload_length,
        }


def _decode_base58(value: str) -> bytes:
    """Decode a Base58 string into raw bytes."""

    value = value.strip()
    if not value:
        raise WIFValidationError("Empty WIF string")

    num = 0
    try:
        for char in value:
            num = num * 58 + BASE58_INDEX[char]
    except KeyError as exc:  # pragma: no cover - defensive branch
        raise WIFValidationError(f"Invalid Base58 character: {exc.args[0]!r}") from None

    # Account for leading zeros encoded as leading '1' characters.
    leading_zeros = len(value) - len(value.lstrip("1"))
    decoded = num.to_bytes((num.bit_length() + 7) // 8, "big")
    return b"\x00" * leading_zeros + decoded


def _double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def validate_wif(wif: str) -> WIFDetails:
    """Validate a single WIF string and return structured details."""

    decoded = _decode_base58(wif)
    if len(decoded) not in (37, 38):
        raise WIFValidationError(
            "Unexpected decoded length. Expected 37 or 38 bytes of data."
        )

    payload, checksum = decoded[:-4], decoded[-4:]
    expected_checksum = _double_sha256(payload)[:4]
    if checksum != expected_checksum:
        raise WIFValidationError("Checksum mismatch (Base58Check validation failed)")

    if payload[0] == 0x80:
        network = "mainnet"
    elif payload[0] == 0xEF:
        network = "testnet"
    else:
        raise WIFValidationError(
            f"Unknown network prefix 0x{payload[0]:02x} (expected 0x80 or 0xEF)"
        )

    if len(payload) == 34 and payload[-1] == 0x01:
        compressed = True
        private_key = payload[1:-1]
    elif len(payload) == 33:
        compressed = False
        private_key = payload[1:]
    else:
        raise WIFValidationError(
            "Unexpected payload structure; could not infer compression state."
        )

    if len(private_key) != 32:
        raise WIFValidationError("Private key length must be exactly 32 bytes")

    private_key_hex = private_key.hex()
    return WIFDetails(
        wif=wif,
        network=network,
        compressed=compressed,
        private_key_hex=private_key_hex,
        payload_length=len(payload),
    )


def _extract_wifs(lines: Iterable[str]) -> List[str]:
    extracted: List[str] = []
    for line in lines:
        stripped = line.split("#", 1)[0].strip()
        if stripped:
            extracted.append(stripped)
    return extracted


def _load_wifs_from_file(path: Path) -> List[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WIFValidationError(f"Could not read {path}: {exc}") from exc
    return _extract_wifs(text.splitlines())


def _collect_wifs(files: Sequence[str], wifs: Sequence[str]) -> List[str]:
    collected: List[str] = []
    for file_path in files:
        collected.extend(_load_wifs_from_file(Path(file_path)))
    collected.extend(wifs)

    if not collected and not sys.stdin.isatty():
        collected.extend(_extract_wifs(sys.stdin.read().splitlines()))

    if not collected:
        raise WIFValidationError("No WIF strings were provided")

    return collected


def _render_text_report(details: Iterable[WIFDetails]) -> str:
    lines = []
    for item in details:
        compression_label = "compressed" if item.compressed else "uncompressed"
        lines.append(
            " - ".join(
                [
                    item.wif,
                    f"network={item.network}",
                    f"{compression_label}",
                    f"payload_length={item.payload_length} bytes",
                    f"private_key=0x{item.private_key_hex}",
                ]
            )
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wifs", nargs="*", help="WIF strings to validate")
    parser.add_argument(
        "-f",
        "--file",
        dest="files",
        action="append",
        default=[],
        help="Path to a file containing WIF strings (one per line).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the validation results as JSON instead of text.",
    )

    args = parser.parse_args(argv)

    try:
        collected_wifs = _collect_wifs(args.files, args.wifs)
    except WIFValidationError as exc:
        parser.error(str(exc))
        return 2  # pragma: no cover - argparse handles exit

    valid_results: List[WIFDetails] = []
    invalid_results: List[tuple[str, str]] = []

    for wif in collected_wifs:
        try:
            valid_results.append(validate_wif(wif))
        except WIFValidationError as exc:
            invalid_results.append((wif, str(exc)))

    exit_code = 0 if not invalid_results else 1

    if args.json:
        payload = [
            {"status": "valid", **item.to_dict()} for item in valid_results
        ]
        payload.extend(
            {"status": "invalid", "wif": wif, "error": error}
            for wif, error in invalid_results
        )
        print(json.dumps(payload, indent=2))
    else:
        if valid_results:
            print("Valid WIFs:")
            print(_render_text_report(valid_results))
        if invalid_results:
            if valid_results:
                print("\nInvalid WIFs:")
            else:
                print("Invalid WIFs:")
            for wif, error in invalid_results:
                print(f" - {wif} :: {error}")

    return exit_code


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
