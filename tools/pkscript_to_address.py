"""Utilities for turning simple Bitcoin scripts into Bitcoin addresses.

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

Some wallet exports express native segwit scripts in a similarly compact
form.  The helper recognises the common witness program layouts and emits
the matching Bech32 (or Bech32m) encoded address:

```
Pkscript
OP_0
<20/32 byte witness program>
```

The witness program hex may be wrapped across multiple lines by upstream
tools; we merge adjacent hexadecimal fragments so that inputs pasted from
ledger dumps continue to work.
"""

from __future__ import annotations

import argparse
import hashlib
import string
from typing import Iterable

from verifier.pkscript_registry import canonicalise_tokens


_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BECH32_ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32_GENERATORS = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]


def _looks_like_base58(value: str) -> bool:
    """Return ``True`` when ``value`` resembles a Base58 string."""

    if not value:
        return False

    cleaned = value.replace("-", "")

    if not cleaned:
        return False

    try:
        candidate = cleaned.encode("ascii")
    except UnicodeEncodeError:
        return False

    return all(chr(byte) in _BASE58_ALPHABET for byte in candidate)


class PkScriptError(ValueError):
    """Raised when a script does not match the expected formats."""


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



def _hash160(data: bytes) -> bytes:
    """Return the RIPEMD160(SHA256(data)) digest."""

    sha = hashlib.sha256(data).digest()
    return hashlib.new("ripemd160", sha).digest()


def _convertbits(data: bytes, from_bits: int, to_bits: int, *, pad: bool = True) -> list[int]:
    """Convert ``data`` from ``from_bits`` to ``to_bits`` per BIP 173."""

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


def _bech32_polymod(values: Iterable[int]) -> int:
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for idx, generator in enumerate(_BECH32_GENERATORS):
            if (top >> idx) & 1:
                chk ^= generator
    return chk


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(ch) >> 5 for ch in hrp] + [0] + [ord(ch) & 31 for ch in hrp]


def _create_bech32_checksum(hrp: str, data: Iterable[int], const: int) -> list[int]:
    values = _bech32_hrp_expand(hrp) + list(data)
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    return [(polymod >> 5 * (5 - idx)) & 31 for idx in range(6)]


def _bech32_encode(hrp: str, data: Iterable[int], *, spec: str = "bech32") -> str:
    const = 1 if spec == "bech32" else 0x2BC830A3
    combined = list(data) + _create_bech32_checksum(hrp, data, const)
    return hrp + "1" + "".join(_BECH32_ALPHABET[d] for d in combined)


def _encode_segwit_address(hrp: str, witness_version: int, program: bytes) -> str:
    if not (0 <= witness_version <= 16):
        raise PkScriptError("unsupported witness version")

    if not (2 <= len(program) <= 40):
        raise PkScriptError("witness program must be between 2 and 40 bytes")

    try:
        words = _convertbits(program, 8, 5, pad=True)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise PkScriptError("invalid witness program") from exc

    spec = "bech32" if witness_version == 0 else "bech32m"
    return _bech32_encode(hrp, [witness_version] + words, spec=spec)


def _is_hex_string(value: str) -> bool:
    return bool(value) and all(char in string.hexdigits for char in value)


def _collect_hex_tokens(tokens: list[str]) -> tuple[str, int]:
    collected: list[str] = []
    for token in tokens:
        if _is_hex_string(token):
            collected.append(token)
        else:
            break
    return "".join(collected), len(collected)


def _pkscript_to_hash(lines: Iterable[str]) -> tuple[str, str, int | None]:
    sequence = canonicalise_tokens(_normalise_lines(lines))

    if sequence and _looks_like_base58(sequence[0]):
        sequence = sequence[1:]

    if sequence and sequence[0].lower() == "pkscript":
        sequence = sequence[1:]

    expected = [
        "OP_DUP",
        "OP_HASH160",
        "OP_EQUALVERIFY",
        "OP_CHECKSIG",
    ]

    if (
        len(sequence) >= 5
        and sequence[0:2] == expected[:2]
        and sequence[-2:] == expected[2:]
    ):
        hash_tokens = sequence[2:-2]
        if not hash_tokens:
            raise PkScriptError("pubkey hash must follow OP_HASH160")

        hash_candidate, consumed = _collect_hex_tokens(hash_tokens)

        if consumed != len(hash_tokens):
            raise PkScriptError("pubkey hash must be hexadecimal")

        if len(hash_candidate) != 40:
            raise PkScriptError("pubkey hash must be 20 bytes of hex")

        return "p2pkh", hash_candidate, None

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

        return "p2pkh", _hash160(pubkey_bytes).hex(), None

    if (
        len(sequence) >= 3
        and sequence[0].upper() == "OP_HASH160"
        and sequence[-1].upper() == "OP_EQUAL"
    ):
        hash_tokens = sequence[1:-1]
        if not hash_tokens:
            raise PkScriptError("script hash must follow OP_HASH160")

        hash_candidate, consumed = _collect_hex_tokens(hash_tokens)

        if consumed != len(hash_tokens):
            raise PkScriptError("script hash must be hexadecimal")

        if len(hash_candidate) != 40:
            raise PkScriptError("script hash must be 20 bytes of hex")

        return "p2sh", hash_candidate, None

    if sequence:
        version_token = sequence[0].upper()
        witness_version: int | None
        if version_token in {"OP_0", "0"}:
            witness_version = 0
        elif version_token.startswith("OP_") and version_token[3:].isdigit():
            witness_version = int(version_token[3:])
            if not (1 <= witness_version <= 16):
                witness_version = None
        else:
            witness_version = None

        if witness_version is not None:
            program_hex, consumed = _collect_hex_tokens(sequence[1:])

            if not program_hex:
                raise PkScriptError("witness program must follow the version opcode")

            if consumed != len(sequence) - 1:
                raise PkScriptError("unexpected tokens after witness program")

            if len(program_hex) % 2 != 0:
                raise PkScriptError("witness program must be an even number of hex digits")

            try:
                program = bytes.fromhex(program_hex)
            except ValueError as exc:
                raise PkScriptError("witness program must be hexadecimal") from exc

            if len(program) == 20:
                return "p2wpkh", program_hex, witness_version
            if len(program) == 32:
                return "p2wsh", program_hex, witness_version

            raise PkScriptError("unsupported witness program length for address conversion")

    raise PkScriptError("unsupported script layout for address conversion")


def pkscript_to_address(lines: Iterable[str], network: str = "mainnet") -> str:
    """Convert a textual script representation to a Bitcoin address."""

    version_map = {
        "mainnet": {"p2pkh": 0x00, "p2sh": 0x05, "bech32_hrp": "bc"},
        "testnet": {"p2pkh": 0x6F, "p2sh": 0xC4, "bech32_hrp": "tb"},
        "regtest": {"p2pkh": 0x6F, "p2sh": 0xC4, "bech32_hrp": "bcrt"},
    }

    try:
        script_versions = version_map[network.lower()]
    except KeyError as exc:
        raise ValueError(f"unknown network '{network}'") from exc

    script_type, hash_hex, witness_version = _pkscript_to_hash(lines)

    if script_type in {"p2pkh", "p2sh"}:
        try:
            version = script_versions[script_type]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise PkScriptError(f"unsupported script type '{script_type}'") from exc
        return _base58check_encode(version, bytes.fromhex(hash_hex))

    if script_type in {"p2wpkh", "p2wsh"}:
        hrp = script_versions.get("bech32_hrp")
        if not isinstance(hrp, str):  # pragma: no cover - defensive guard
            raise PkScriptError("network does not define a bech32 HRP")

        if witness_version is None:  # pragma: no cover - defensive guard
            raise PkScriptError("missing witness version for segwit script")

        return _encode_segwit_address(hrp, witness_version, bytes.fromhex(hash_hex))

    raise PkScriptError(f"unsupported script type '{script_type}'")


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

