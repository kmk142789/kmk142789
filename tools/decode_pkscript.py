"""Utilities for decoding simple Bitcoin P2PKH scripts to base58 addresses."""
from __future__ import annotations

import argparse
import re
import string
from dataclasses import dataclass
from typing import Iterable, List

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

_NETWORK_PREFIXES = {
    "mainnet": b"\x00",
    "testnet": b"\x6f",
    "regtest": b"\x6f",
}

_KNOWN_OPS = {"OP_DUP", "OP_HASH160", "OP_EQUALVERIFY", "OP_CHECKSIG"}


def _clean_opcode(token: str) -> str:
    """Return ``token`` uppercased with separators removed."""

    return token.upper().replace("_", "").replace("-", "")


_OP_CLEAN_MAP = {_clean_opcode(op): op for op in _KNOWN_OPS}
_OP_PREFIXES = {
    clean[:index]
    for clean in _OP_CLEAN_MAP
    for index in range(1, len(clean))
}


class ScriptDecodeError(ValueError):
    """Raised when the provided script cannot be interpreted as P2PKH."""


@dataclass(frozen=True)
class DecodedScript:
    address: str
    pubkey_hash: str
    network: str


def _base58check_encode(payload: bytes) -> str:
    checksum_full = _sha256(_sha256(payload))
    checksum = checksum_full[:4]
    value = int.from_bytes(payload + checksum, "big")
    encoded = ""
    while value > 0:
        value, remainder = divmod(value, 58)
        encoded = BASE58_ALPHABET[remainder] + encoded
    leading_zeroes = len(payload) - len(payload.lstrip(b"\x00"))
    return "1" * leading_zeroes + encoded or "1"


def _sha256(data: bytes) -> bytes:
    import hashlib

    return hashlib.sha256(data).digest()


def _is_hex_script(script: str) -> bool:
    cleaned = _strip_comments(script).strip().replace(" ", "")
    if not cleaned or len(cleaned) % 2:
        return False
    return all(ch in string.hexdigits for ch in cleaned)


def _tokens_from_hex(script: str) -> List[str]:
    raw = bytes.fromhex(_strip_comments(script).strip().replace(" ", ""))
    if len(raw) < 25:
        raise ScriptDecodeError("hex script too short for P2PKH")
    if raw[0] != 0x76 or raw[1] != 0xa9:
        raise ScriptDecodeError("hex script does not start with OP_DUP OP_HASH160")
    push_len = raw[2]
    if push_len != 20:
        raise ScriptDecodeError("unexpected pushdata length for P2PKH")
    if len(raw) != 25:
        raise ScriptDecodeError("unexpected hex script length for canonical P2PKH")
    pubkey_hash = raw[3:23]
    if raw[23] != 0x88 or raw[24] != 0xac:
        raise ScriptDecodeError("hex script missing OP_EQUALVERIFY OP_CHECKSIG")
    return [
        "OP_DUP",
        "OP_HASH160",
        pubkey_hash.hex(),
        "OP_EQUALVERIFY",
        "OP_CHECKSIG",
    ]


def _strip_comments(script: str) -> str:
    """Return ``script`` with comment fragments removed."""

    lines: List[str] = []
    for raw_line in script.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "#" in stripped:
            stripped = stripped.split("#", 1)[0].strip()
            if not stripped:
                continue
        lines.append(stripped)
    return "\n".join(lines)


def _normalize_tokens(script: str) -> List[str]:
    parts = re.split(r"\s+", _strip_comments(script))
    tokens: List[str] = []
    buffer_clean = ""
    buffer_raw: List[str] = []

    for part in filter(None, parts):
        clean = _clean_opcode(part)

        if buffer_clean:
            candidate_clean = buffer_clean + clean
            candidate_raw = buffer_raw + [part]
        else:
            candidate_clean = clean
            candidate_raw = [part]

        if candidate_clean in _OP_CLEAN_MAP:
            tokens.append(_OP_CLEAN_MAP[candidate_clean])
            buffer_clean = ""
            buffer_raw.clear()
            continue

        if (buffer_clean or clean.startswith("OP")) and candidate_clean in _OP_PREFIXES:
            buffer_clean = candidate_clean
            buffer_raw = candidate_raw
            continue

        if buffer_clean:
            fragments = " ".join(candidate_raw)
            raise ScriptDecodeError(f"unrecognized opcode sequence: {fragments}")

        tokens.append(part)

    if buffer_clean:
        fragments = " ".join(buffer_raw)
        raise ScriptDecodeError(f"dangling opcode fragment: {fragments}")

    return tokens


def _extract_p2pkh_tokens(tokens: Iterable[str]) -> List[str]:
    """Return the canonical five-token P2PKH sequence from ``tokens``."""

    sequence: List[str] = []
    started = False

    for token in tokens:
        if len(sequence) == 5:
            upper = token.upper()
            if upper in _KNOWN_OPS or re.fullmatch(r"[0-9a-fA-F]{40}", token):
                raise ScriptDecodeError("unexpected tokens after canonical P2PKH sequence")
            continue

        upper = token.upper()

        if upper in _KNOWN_OPS:
            sequence.append(upper)
            started = True
            continue

        if re.fullmatch(r"[0-9a-fA-F]{40}", token):
            sequence.append(token.lower())
            started = True
            continue

        if not started:
            continue

        raise ScriptDecodeError(f"unexpected token in script body: {token}")

    if len(sequence) != 5:
        raise ScriptDecodeError("script must contain five elements for P2PKH")

    return sequence


def _ensure_pattern(tokens: Iterable[str]) -> List[str]:
    collected = _extract_p2pkh_tokens(tokens)
    op_dup, op_hash, payload, op_equalverify, op_checksig = collected
    if op_dup != "OP_DUP" or op_hash != "OP_HASH160":
        raise ScriptDecodeError("script must start with OP_DUP OP_HASH160")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", payload):
        raise ScriptDecodeError("script payload must be a 20-byte hex string")
    if op_equalverify != "OP_EQUALVERIFY" or op_checksig != "OP_CHECKSIG":
        raise ScriptDecodeError("script must end with OP_EQUALVERIFY OP_CHECKSIG")
    return [op_dup, op_hash, payload.lower(), op_equalverify, op_checksig]


def decode_p2pkh_script(script: str, network: str = "mainnet") -> DecodedScript:
    """Decode a canonical P2PKH script into a base58 address."""

    if network not in _NETWORK_PREFIXES:
        raise ScriptDecodeError(f"unsupported network: {network}")

    if _is_hex_script(script):
        tokens = _tokens_from_hex(script)
    else:
        tokens = _normalize_tokens(script)

    _, _, payload, _, _ = _ensure_pattern(tokens)
    prefix = _NETWORK_PREFIXES[network]
    payload_bytes = bytes.fromhex(payload)
    address = _base58check_encode(prefix + payload_bytes)
    return DecodedScript(address=address, pubkey_hash=payload, network=network)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", help="P2PKH script in assembly or hex form")
    parser.add_argument(
        "--network",
        default="mainnet",
        choices=sorted(_NETWORK_PREFIXES.keys()),
        help="Bitcoin network to use for decoding",
    )
    parser.add_argument(
        "--expect",
        help="Optional base58 address to compare with the decoded output",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        decoded = decode_p2pkh_script(args.script, network=args.network)
    except ScriptDecodeError as exc:
        print(f"error: {exc}")
        return 1

    print(f"Network: {decoded.network}")
    print(f"Public Key Hash: {decoded.pubkey_hash}")
    print(f"Address: {decoded.address}")

    if args.expect:
        if decoded.address == args.expect:
            print("Match: provided address matches decoded output")
        else:
            print("Mismatch: provided address does not match decoded output")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
