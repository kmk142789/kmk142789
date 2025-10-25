"""Utilities for decoding common Bitcoin locking scripts into addresses.

The helper was originally written to support the canonical pay-to-public-key
hash (P2PKH) format that appears throughout the Satoshi treasure puzzle data
set.  Many of those puzzle walkthroughs now also contain native segwit scripts
(``OP_0 <20-byte hash>``) so the decoder has been extended to recognise the
minimal pay-to-witness-public-key-hash (P2WPKH) layout.  When a segwit script
is detected the Bech32-encoded address is emitted instead of a legacy base58
string.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import string
from dataclasses import dataclass
from typing import Iterable, List, Optional

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

_NETWORK_PARAMS = {
    "mainnet": {"p2pkh_prefix": b"\x00", "bech32_hrp": "bc"},
    "testnet": {"p2pkh_prefix": b"\x6f", "bech32_hrp": "tb"},
    "regtest": {"p2pkh_prefix": b"\x6f", "bech32_hrp": "bcrt"},
}

_KNOWN_OPS = {"OP_DUP", "OP_HASH160", "OP_EQUALVERIFY", "OP_CHECKSIG", "OP_0"}


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
    """Raised when the provided script cannot be interpreted as a known form."""


@dataclass(frozen=True)
class DecodedScript:
    address: str
    pubkey_hash: str
    network: str
    script_type: str = "p2pkh"
    witness_version: int | None = None
    public_key: Optional[str] = None


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


def _bech32_polymod(values: Iterable[int]) -> int:
    generator = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for i in range(5):
            if (top >> i) & 1:
                chk ^= generator[i]
    return chk


def _bech32_hrp_expand(hrp: str) -> List[int]:
    return [ord(char) >> 5 for char in hrp] + [0] + [ord(char) & 31 for char in hrp]


def _convertbits(data: bytes, from_bits: int, to_bits: int, *, pad: bool = True) -> List[int]:
    acc = 0
    bits = 0
    ret: List[int] = []
    max_v = (1 << to_bits) - 1
    max_acc = (1 << (from_bits + to_bits - 1)) - 1
    for value in data:
        if value < 0 or value >> from_bits:
            raise ValueError("invalid value for convertbits")
        acc = ((acc << from_bits) | value) & max_acc
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            ret.append((acc >> bits) & max_v)
    if pad:
        if bits:
            ret.append((acc << (to_bits - bits)) & max_v)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & max_v):
        raise ValueError("invalid padding in convertbits")
    return ret


def _encode_segwit_address(hrp: str, witness_version: int, program: bytes) -> str:
    if not (0 <= witness_version <= 16):
        raise ScriptDecodeError("invalid witness version")

    if witness_version == 0 and len(program) not in {20, 32}:
        raise ScriptDecodeError("unsupported witness program length")

    try:
        data = [witness_version] + _convertbits(program, 8, 5)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ScriptDecodeError("failed to encode witness program") from exc

    const = 0x2BC830A3 if witness_version else 1
    checksum = _bech32_polymod(_bech32_hrp_expand(hrp) + data + [0, 0, 0, 0, 0, 0]) ^ const
    combined = data + [(checksum >> 5 * (5 - i)) & 31 for i in range(6)]
    alphabet = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
    encoded = hrp + "1" + "".join(alphabet[d] for d in combined)
    if witness_version:
        return encoded.lower()
    return encoded


def _is_hex_script(script: str) -> bool:
    cleaned = _strip_comments(script).strip().replace(" ", "")
    if not cleaned or len(cleaned) % 2:
        return False
    return all(ch in string.hexdigits for ch in cleaned)


def _tokens_from_hex(script: str) -> List[str]:
    raw = bytes.fromhex(_strip_comments(script).strip().replace(" ", ""))
    if len(raw) < 4:
        raise ScriptDecodeError("hex script too short to decode")

    # Legacy P2PKH: OP_DUP OP_HASH160 <20-byte hash> OP_EQUALVERIFY OP_CHECKSIG
    if raw[0] == 0x76 and raw[1] == 0xA9:
        if len(raw) != 25:
            raise ScriptDecodeError("unexpected hex script length for canonical P2PKH")
        push_len = raw[2]
        if push_len != 20:
            raise ScriptDecodeError("unexpected pushdata length for P2PKH")
        pubkey_hash = raw[3:23]
        if raw[23] != 0x88 or raw[24] != 0xAC:
            raise ScriptDecodeError("hex script missing OP_EQUALVERIFY OP_CHECKSIG")
        return [
            "OP_DUP",
            "OP_HASH160",
            pubkey_hash.hex(),
            "OP_EQUALVERIFY",
            "OP_CHECKSIG",
        ]

    # Pay-to-public-key: <pushdata len> <pubkey> OP_CHECKSIG
    push_len = raw[0]
    if raw[-1] == 0xAC and push_len in {33, 65}:
        if len(raw) != push_len + 2:
            raise ScriptDecodeError("hex script length does not match P2PK layout")
        pubkey = raw[1 : 1 + push_len]
        if push_len == 33 and pubkey[0] not in {0x02, 0x03}:
            raise ScriptDecodeError("compressed public key must start with 02 or 03")
        if push_len == 65 and pubkey[0] != 0x04:
            raise ScriptDecodeError("uncompressed public key must start with 04")
        return [pubkey.hex(), "OP_CHECKSIG"]

    # Segwit P2WPKH/P2WSH witness programs use OP_0 (0x00) followed by push.
    if raw[0] == 0x00:
        program_length = raw[1]
        if program_length not in {20, 32}:
            raise ScriptDecodeError("unsupported witness program length")
        if len(raw) != 2 + program_length:
            raise ScriptDecodeError("hex script length does not match witness program")
        program = raw[2:]
        return ["OP_0", program.hex()]

    raise ScriptDecodeError("unrecognized hex script layout")


_ESCAPE_MAP = {"n": "\n", "r": "\r", "t": "\t"}


def _expand_escape_sequences(script: str) -> str:
    """Replace common escaped whitespace sequences with their literals."""

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return _ESCAPE_MAP.get(key, match.group(0))

    # Only translate recognised escapes so that hex payloads remain untouched.
    return re.sub(r"\\(n|r|t)", _replace, script)


def _strip_comments(script: str) -> str:
    """Return ``script`` with comment fragments removed."""

    expanded = _expand_escape_sequences(script)
    lines: List[str] = []
    for raw_line in expanded.splitlines():
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


def _extract_p2pk_pubkey(tokens: List[str]) -> Optional[str]:
    if not tokens or tokens[-1].upper() != "OP_CHECKSIG":
        return None

    body = tokens[:-1]
    if not body:
        raise ScriptDecodeError("script missing public key before OP_CHECKSIG")

    if any(part.upper() in _KNOWN_OPS - {"OP_CHECKSIG"} for part in body):
        return None

    cleaned = [part.strip() for part in body]

    # Handle assemblies that include a push opcode length literal (e.g. "41").
    if (
        len(cleaned) == 2
        and re.fullmatch(r"[0-9a-fA-F]{2}", cleaned[0])
        and re.fullmatch(r"[0-9a-fA-F]+", cleaned[1])
    ):
        push_len = int(cleaned[0], 16)
        pubkey_hex = cleaned[1]
        if len(pubkey_hex) != push_len * 2:
            raise ScriptDecodeError("pushdata length does not match public key size")
    else:
        if not all(re.fullmatch(r"[0-9a-fA-F]+", part) for part in cleaned):
            return None
        pubkey_hex = "".join(cleaned)

    if len(pubkey_hex) not in {66, 130}:
        raise ScriptDecodeError("public key must be 33 or 65 bytes long")
    if len(pubkey_hex) == 66 and pubkey_hex[:2] not in {"02", "03"}:
        raise ScriptDecodeError("compressed public key must start with 02 or 03")
    if len(pubkey_hex) == 130 and not pubkey_hex.startswith("04"):
        raise ScriptDecodeError("uncompressed public key must start with 04")

    return pubkey_hex.lower()


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
    """Decode a recognised Bitcoin script into an address.

    The function name is kept for historical reasons; it now handles both
    classic P2PKH scripts and the minimal P2WPKH witness program layout.
    """

    params = _NETWORK_PARAMS.get(network)
    if params is None:
        raise ScriptDecodeError(f"unsupported network: {network}")

    if _is_hex_script(script):
        tokens = _tokens_from_hex(script)
    else:
        tokens = _normalize_tokens(script)

    upper_tokens = [token.upper() for token in tokens]
    if upper_tokens and upper_tokens[0] in {"OP_0", "0"}:
        if len(tokens) < 2:
            raise ScriptDecodeError("witness program must follow OP_0")
        program_hex = "".join(token.strip().lower() for token in tokens[1:])
        if not program_hex:
            raise ScriptDecodeError("witness program must contain hexadecimal data")
        if any(ch not in string.hexdigits for ch in program_hex):
            raise ScriptDecodeError("witness program must be hexadecimal")
        if len(program_hex) not in {40, 64}:
            raise ScriptDecodeError("unsupported witness program length")
        program = bytes.fromhex(program_hex)
        witness_version = 0
        script_type = "p2wpkh" if len(program) == 20 else "p2wsh"
        address = _encode_segwit_address(params["bech32_hrp"], witness_version, program)
        return DecodedScript(
            address=address,
            pubkey_hash=program_hex,
            network=network,
            script_type=script_type,
            witness_version=witness_version,
        )

    pubkey_hex = _extract_p2pk_pubkey(tokens)
    if pubkey_hex:
        pubkey_bytes = bytes.fromhex(pubkey_hex)
        sha = hashlib.sha256(pubkey_bytes).digest()
        ripe = hashlib.new("ripemd160", sha).digest()
        payload = params["p2pkh_prefix"] + ripe
        address = _base58check_encode(payload)
        return DecodedScript(
            address=address,
            pubkey_hash=ripe.hex(),
            network=network,
            script_type="p2pk",
            public_key=pubkey_hex,
        )

    _, _, payload, _, _ = _ensure_pattern(tokens)
    prefix = params["p2pkh_prefix"]
    payload_bytes = bytes.fromhex(payload)
    address = _base58check_encode(prefix + payload_bytes)
    return DecodedScript(address=address, pubkey_hash=payload, network=network)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", help="Bitcoin script in assembly or hex form")
    parser.add_argument(
        "--network",
        default="mainnet",
        choices=sorted(_NETWORK_PARAMS.keys()),
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

    print(f"Network       : {decoded.network}")
    print(f"Script type   : {decoded.script_type}")
    if decoded.witness_version is not None:
        print(f"Witness ver   : {decoded.witness_version}")
    if decoded.public_key:
        print(f"Public key    : {decoded.public_key}")
    if decoded.script_type in {"p2pkh", "p2pk"}:
        label = "Public Key Hash"
    else:
        label = "Witness Program"
    print(f"{label:<14}: {decoded.pubkey_hash}")
    print(f"Address       : {decoded.address}")

    if args.expect:
        if decoded.address == args.expect:
            print("Match: provided address matches decoded output")
        else:
            print("Mismatch: provided address does not match decoded output")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
