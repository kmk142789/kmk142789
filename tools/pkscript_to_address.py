"""Utilities for turning simple Bitcoin scripts into base58 addresses.

This module understands the very common pay-to-public-key-hash (P2PKH)
`pkscript` layout that appears in a lot of wallet export formats:

```
Pkscript
OP_DUP
OP_HASH160
<20 byte hex hash>
OP_EQUALVERIFY
OP_CHECKSIG
```

The helper reads that representation and emits the corresponding base58
address.  The parsing code is intentionally conservative so that we fail
fast on malformed input instead of silently creating the wrong address.

In addition to the classic P2PKH form the helper also understands the
minimal pay-to-script-hash (P2SH) construction:

```
Pkscript
OP_HASH160
<20 byte script hash>
OP_EQUAL
```

Both script variants are widely used in wallet exports.
"""

from __future__ import annotations

import argparse
import hashlib
from typing import Iterable


_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class PkScriptError(ValueError):
    """Raised when a script does not match the expected P2PKH pattern."""


def _base58check_encode(version: int, payload: bytes) -> str:
    """Return a base58check address for ``payload`` with ``version`` byte."""

    if not 0 <= version <= 0xFF:
        raise ValueError("version must fit inside a single byte")

    data = bytes([version]) + payload
    checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    return _base58_encode(data + checksum)


def _base58_encode(data: bytes) -> str:
    number = int.from_bytes(data, "big")

    result = ""
    while number > 0:
        number, mod = divmod(number, 58)
        result = _BASE58_ALPHABET[mod] + result

    leading_zeroes = 0
    for byte in data:
        if byte == 0:
            leading_zeroes += 1
        else:
            break

    return "1" * leading_zeroes + result


def _normalise_lines(lines: Iterable[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def _collapse_op_checksig(sequence: list[str]) -> list[str]:
    """Return ``sequence`` with standalone ``OP_CHECK`` ``SIG`` merged."""

    collapsed: list[str] = []
    idx = 0
    while idx < len(sequence):
        token = sequence[idx]
        upper = token.upper()
        if upper == "OP_CHECK" and idx + 1 < len(sequence):
            next_token = sequence[idx + 1].upper()
            if next_token in {"SIG"}:
                collapsed.append("OP_CHECKSIG")
                idx += 2
                continue
        collapsed.append(token)
        idx += 1
    return collapsed


def _hash160(data: bytes) -> bytes:
    """Return the RIPEMD160(SHA256(data)) digest."""

    sha = hashlib.sha256(data).digest()
    return hashlib.new("ripemd160", sha).digest()


def _pkscript_to_hash(lines: Iterable[str]) -> tuple[str, str]:
    sequence = _collapse_op_checksig(_normalise_lines(lines))

    if sequence and sequence[0].lower() == "pkscript":
        sequence = sequence[1:]

    expected = [
        "OP_DUP",
        "OP_HASH160",
        "OP_EQUALVERIFY",
        "OP_CHECKSIG",
    ]

    if len(sequence) == 5 and sequence[0:2] == expected[:2] and sequence[3:] == expected[2:]:
        hash_candidate = sequence[2]

        if len(hash_candidate) != 40:
            raise PkScriptError("pubkey hash must be 20 bytes of hex")

        try:
            bytes.fromhex(hash_candidate)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise PkScriptError("pubkey hash must be hexadecimal") from exc

        return "p2pkh", hash_candidate

    if len(sequence) == 2 and sequence[1].upper() == "OP_CHECKSIG":
        pubkey_hex = sequence[0]
        try:
            pubkey_bytes = bytes.fromhex(pubkey_hex)
        except ValueError as exc:
            raise PkScriptError("public key must be hexadecimal") from exc

        if len(pubkey_bytes) not in {33, 65}:
            raise PkScriptError("public key must be 33 or 65 bytes long")

        if len(pubkey_bytes) == 33 and pubkey_bytes[0] not in (0x02, 0x03):
            raise PkScriptError("compressed public key must start with 0x02 or 0x03")

        if len(pubkey_bytes) == 65 and pubkey_bytes[0] != 0x04:
            raise PkScriptError("uncompressed public key must start with 0x04")

        return "p2pkh", _hash160(pubkey_bytes).hex()

    if (
        len(sequence) == 3
        and sequence[0].upper() == "OP_HASH160"
        and sequence[2].upper() == "OP_EQUAL"
    ):
        hash_candidate = sequence[1]

        if len(hash_candidate) != 40:
            raise PkScriptError("script hash must be 20 bytes of hex")

        try:
            bytes.fromhex(hash_candidate)
        except ValueError as exc:
            raise PkScriptError("script hash must be hexadecimal") from exc

        return "p2sh", hash_candidate

    raise PkScriptError("unsupported script layout for address conversion")


def pkscript_to_address(lines: Iterable[str], network: str = "mainnet") -> str:
    """Convert a textual script representation to a base58 address."""

    version_map = {
        "mainnet": {"p2pkh": 0x00, "p2sh": 0x05},
        "testnet": {"p2pkh": 0x6F, "p2sh": 0xC4},
        "regtest": {"p2pkh": 0x6F, "p2sh": 0xC4},
    }

    try:
        script_versions = version_map[network.lower()]
    except KeyError as exc:
        raise ValueError(f"unknown network '{network}'") from exc

    script_type, hash_hex = _pkscript_to_hash(lines)

    try:
        version = script_versions[script_type]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise PkScriptError(f"unsupported script type '{script_type}'") from exc

    return _base58check_encode(version, bytes.fromhex(hash_hex))


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        help="file containing the P2PKH script; omit to read from stdin",
    )
    parser.add_argument(
        "--network",
        default="mainnet",
        choices=("mainnet", "testnet", "regtest"),
        help="Bitcoin network to use when selecting the version byte",
    )
    return parser


def main() -> int:
    parser = _build_cli()
    args = parser.parse_args()

    if args.path:
        with open(args.path, "r", encoding="utf8") as handle:
            lines = handle.readlines()
    else:
        import sys

        lines = sys.stdin.readlines()

    address = pkscript_to_address(lines, args.network)
    print(address)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())

