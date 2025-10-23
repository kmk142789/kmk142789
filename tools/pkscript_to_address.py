"""Utilities for turning simple scripts into Bitcoin addresses.

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
address.  The parser also recognises raw SegWit witness programs written as
hexadecimal strings (for example ``0014<hash>``) and returns the appropriate
bech32 address.  The parsing code is intentionally conservative so that we
fail fast on malformed input instead of silently creating the wrong address.
"""

from __future__ import annotations

import argparse
import hashlib
from typing import Iterable, Sequence


_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BECH32_ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32_GENERATORS = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]

_NETWORKS = {
    "mainnet": {"p2pkh": 0x00, "bech32_hrp": "bc"},
    "testnet": {"p2pkh": 0x6F, "bech32_hrp": "tb"},
    "regtest": {"p2pkh": 0x6F, "bech32_hrp": "bcrt"},
}


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


def _bech32_polymod(values: Iterable[int]) -> int:
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for i, generator in enumerate(_BECH32_GENERATORS):
            if (top >> i) & 1:
                chk ^= generator
    return chk


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def _convertbits(data: bytes, from_bits: int, to_bits: int, pad: bool = True) -> list[int]:
    acc = 0
    bits = 0
    result: list[int] = []
    max_value = (1 << to_bits) - 1
    max_acc = (1 << (from_bits + to_bits - 1)) - 1

    for value in data:
        if value < 0 or value >> from_bits:
            raise ValueError("invalid value for convertbits")
        acc = ((acc << from_bits) | value) & max_acc
        bits += from_bits

        while bits >= to_bits:
            bits -= to_bits
            result.append((acc >> bits) & max_value)

    if pad:
        if bits:
            result.append((acc << (to_bits - bits)) & max_value)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & max_value):
        raise ValueError("invalid padding in convertbits")

    return result


def _create_bech32_checksum(hrp: str, data: Sequence[int], const: int) -> list[int]:
    values = _bech32_hrp_expand(hrp) + list(data)
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def _encode_segwit_address(hrp: str, witness_version: int, program: bytes) -> str:
    if not (0 <= witness_version <= 16):
        raise PkScriptError("witness version must be between 0 and 16")
    if not (2 <= len(program) <= 40):
        raise PkScriptError("witness program must be 2-40 bytes long")
    if witness_version == 0 and len(program) not in (20, 32):
        raise PkScriptError("version 0 witness program must be 20 or 32 bytes")

    data = [witness_version] + _convertbits(program, 8, 5, pad=True)
    const = 1 if witness_version == 0 else 0x2BC830A3
    checksum = _create_bech32_checksum(hrp, data, const)
    combined = data + checksum
    return hrp + "1" + "".join(_BECH32_ALPHABET[d] for d in combined)


def _pkscript_to_hash(lines: Iterable[str]) -> tuple[str, bytes]:
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

        return "p2pkh", bytes.fromhex(hash_candidate)

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

        return "p2pkh", _hash160(pubkey_bytes)

    if len(sequence) == 1:
        script_hex = sequence[0]
        try:
            script_bytes = bytes.fromhex(script_hex)
        except ValueError as exc:
            raise PkScriptError("script must be hexadecimal") from exc

        if (
            len(script_bytes) >= 4
            and script_bytes[0] in (0x00, *range(0x51, 0x61))
            and script_bytes[1] == len(script_bytes) - 2
        ):
            opcode = script_bytes[0]
            if opcode == 0x00:
                witness_version = 0
            else:
                witness_version = opcode - 0x50

            program = script_bytes[2:]
            return "segwit", bytes([witness_version]) + program

        raise PkScriptError("unsupported script layout for address conversion")

    raise PkScriptError("unsupported script layout for address conversion")


def pkscript_to_address(lines: Iterable[str], network: str = "mainnet") -> str:
    """Convert a textual script representation to a Bitcoin address."""

    network_key = network.lower()

    try:
        network_info = _NETWORKS[network_key]
    except KeyError as exc:
        raise ValueError(f"unknown network '{network}'") from exc

    script_type, payload = _pkscript_to_hash(lines)

    if script_type == "p2pkh":
        return _base58check_encode(int(network_info["p2pkh"]), payload)

    if script_type == "segwit":
        witness_version = payload[0]
        program = payload[1:]
        hrp = str(network_info["bech32_hrp"])
        return _encode_segwit_address(hrp, witness_version, program)

    raise PkScriptError("unsupported script layout for address conversion")


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

