"""Interactive PKScript REPL with transcript generation."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from puzzle_data import load_puzzles

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ALPHABET_INDEX = {char: index for index, char in enumerate(ALPHABET)}
BECH32_ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

USAGE = """\
Echo Expansion — PKScript REPL
==============================
Inspect PKScripts, scriptSigs, and addresses with a guided decoder.
Examples:

  python scripts/pks_repl.py --script "OP_DUP OP_HASH160 0e5f3c406397442996825fd395543514fd06f207 OP_EQUALVERIFY OP_CHECKSIG"
  python scripts/pks_repl.py --generate-transcripts
  python scripts/pks_repl.py  # interactive REPL
"""


class DecodeError(RuntimeError):
    """Raised when the input cannot be decoded."""


def b58encode(raw: bytes) -> str:
    acc = int.from_bytes(raw, "big")
    encoded = ""
    while acc:
        acc, mod = divmod(acc, 58)
        encoded = ALPHABET[mod] + encoded
    for byte in raw:
        if byte == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded or "1"


def b58decode(value: str) -> bytes:
    acc = 0
    for char in value:
        try:
            acc = acc * 58 + ALPHABET_INDEX[char]
        except KeyError as exc:
            raise DecodeError(f"Invalid Base58 character: {char!r}") from exc
    raw = acc.to_bytes((acc.bit_length() + 7) // 8, "big") if acc else b""
    leading = 0
    for char in value:
        if char == "1":
            leading += 1
        else:
            break
    return b"\x00" * leading + raw


def checksum(payload: bytes) -> bytes:
    import hashlib

    return hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]


def address_from_hash160(hash160: str, version: int = 0) -> str:
    payload = bytes.fromhex(f"{version:02x}" + hash160)
    return b58encode(payload + checksum(payload))


def convertbits(data: Iterable[int], frombits: int, tobits: int, pad: bool = True) -> List[int]:
    acc = 0
    bits = 0
    ret: List[int] = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or value >> frombits:
            raise DecodeError("Invalid value for convertbits")
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        raise DecodeError("Invalid padding in convertbits")
    return ret


def bech32_polymod(values: Iterable[int]) -> int:
    generator = (0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)
    chk = 1
    for value in values:
        b = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            if (b >> i) & 1:
                chk ^= generator[i]
    return chk


def bech32_hrp_expand(hrp: str) -> List[int]:
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def bech32_create_checksum(hrp: str, data: List[int], spec: str) -> List[int]:
    const = 0x2bc830a3 if spec == "bech32m" else 1
    values = bech32_hrp_expand(hrp) + data
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def encode_segwit_address(hrp: str, version: int, program: bytes) -> str:
    spec = "bech32" if version == 0 else "bech32m"
    data = [version] + convertbits(program, 8, 5)
    combined = data + bech32_create_checksum(hrp, data, spec)
    return hrp + "1" + "".join(BECH32_ALPHABET[d] for d in combined)


def decode_address(value: str) -> Dict[str, object]:
    if value.startswith(("bc1", "tb1", "bcrt1")):
        return decode_bech32_address(value)
    decoded = b58decode(value)
    if len(decoded) < 5:
        raise DecodeError("Address payload too short")
    payload, check = decoded[:-4], decoded[-4:]
    if check != checksum(payload):
        raise DecodeError("Checksum mismatch")
    version = payload[0]
    hash160 = payload[1:].hex()
    if version == 0:
        return {
            "type": "p2pkh",
            "hash160": hash160,
            "script": ["OP_DUP", "OP_HASH160", hash160, "OP_EQUALVERIFY", "OP_CHECKSIG"],
            "address": value,
        }
    if version == 5:
        return {
            "type": "p2sh",
            "hash160": hash160,
            "script": ["OP_HASH160", hash160, "OP_EQUAL"],
            "address": value,
        }
    raise DecodeError(f"Unsupported version byte {version}")


def decode_bech32_address(value: str) -> Dict[str, object]:
    value = value.lower()
    pos = value.rfind("1")
    if pos == -1:
        raise DecodeError("Invalid bech32 string")
    hrp, data_part = value[:pos], value[pos + 1 :]
    if not hrp or not data_part:
        raise DecodeError("Invalid bech32 format")
    try:
        data = [BECH32_ALPHABET.index(c) for c in data_part]
    except ValueError as exc:
        raise DecodeError("Invalid bech32 character") from exc
    polymod = bech32_polymod(bech32_hrp_expand(hrp) + data)
    if polymod == 1:
        spec = "bech32"
    elif polymod == 0x2bc830a3:
        spec = "bech32m"
    else:
        raise DecodeError("Checksum validation failed")
    values = data[:-6]
    if not values:
        raise DecodeError("Empty bech32 payload")
    version = values[0]
    program = bytes(convertbits(values[1:], 5, 8, pad=False))
    if version == 0 and spec != "bech32":
        raise DecodeError("bech32 checksum mismatch for version 0")
    if version != 0 and spec != "bech32m":
        raise DecodeError("bech32m checksum required for version >= 1")
    if len(program) not in (20, 32):
        raise DecodeError("Unexpected witness program length")
    script = [str(version), program.hex()]
    return {
        "type": "p2wpkh" if len(program) == 20 and version == 0 else "p2wsh" if version == 0 else "p2tr",
        "witness_version": version,
        "witness_program": program.hex(),
        "script": [str(version), program.hex()],
        "address": value,
    }


def parse_tokens(text: str) -> List[str]:
    tokens: List[str] = []
    for line in text.strip().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower() in {"pkscript", "scriptsig"}:
            continue
        tokens.extend(stripped.split())
    return tokens


def analyze_tokens(tokens: Sequence[str]) -> Dict[str, object]:
    if not tokens:
        raise DecodeError("Empty input")
    if len(tokens) == 1 and tokens[0] and all(ch in ALPHABET for ch in tokens[0]):
        return decode_address(tokens[0])
    if tokens[0].startswith("bc1"):
        return decode_address(tokens[0])
    if len(tokens) == 5 and tokens[0].upper() == "OP_DUP" and tokens[1].upper() == "OP_HASH160" and tokens[3].upper() == "OP_EQUALVERIFY" and tokens[4].upper() == "OP_CHECKSIG":
        hash160 = tokens[2].lower()
        address = address_from_hash160(hash160)
        return {
            "type": "p2pkh",
            "hash160": hash160,
            "address": address,
            "script": [token.upper() if token.startswith("OP_") else token.lower() for token in tokens],
            "description": "Pay-to-PubKey-Hash (legacy).",
        }
    if len(tokens) == 3 and tokens[0].upper() == "OP_HASH160" and tokens[2].upper() == "OP_EQUAL":
        hash160 = tokens[1].lower()
        address = address_from_hash160(hash160, version=5)
        return {
            "type": "p2sh",
            "hash160": hash160,
            "address": address,
            "script": [token.upper() if token.startswith("OP_") else token.lower() for token in tokens],
            "description": "Pay-to-Script-Hash (legacy).",
        }
    if len(tokens) == 2 and tokens[0] in {"0", "OP_0"}:
        program = tokens[1].lower()
        if len(program) == 40:
            return {
                "type": "p2wpkh",
                "witness_version": 0,
                "witness_program": program,
                "address": encode_segwit_address("bc", 0, bytes.fromhex(program)),
                "script": ["0", program],
                "description": "Pay-to-Witness-PubKey-Hash (SegWit v0).",
            }
        if len(program) == 64:
            return {
                "type": "p2wsh",
                "witness_version": 0,
                "witness_program": program,
                "address": encode_segwit_address("bc", 0, bytes.fromhex(program)),
                "script": ["0", program],
                "description": "Pay-to-Witness-Script-Hash (SegWit v0).",
            }
    if len(tokens) == 2 and tokens[0] == "1":
        program = tokens[1].lower()
        if len(program) == 64:
            return {
                "type": "p2tr",
                "witness_version": 1,
                "witness_program": program,
                "address": encode_segwit_address("bc", 1, bytes.fromhex(program)),
                "script": ["1", program],
                "description": "Pay-to-Taproot (SegWit v1, bech32m).",
            }
    raise DecodeError("Unrecognised script or address format")


def render_tree(analysis: Dict[str, object]) -> str:
    lines = [f"PKScript ({analysis.get('type', 'unknown')})"]
    script = analysis.get("script", [])
    for index, token in enumerate(script):
        prefix = "├─" if index < len(script) - 1 else "└─"
        lines.append(f"{prefix} {token}")
    if "hash160" in analysis:
        lines.append(f"   ↳ HASH160: {analysis['hash160']}")
    if "address" in analysis:
        lines.append(f"   ↳ Address: {analysis['address']}")
    if "description" in analysis:
        lines.append(f"   ↳ {analysis['description']}")
    return "\n".join(lines)


def interactive_loop() -> List[Dict[str, object]]:
    history: List[Dict[str, object]] = []
    print(USAGE)
    print("Type 'exit' or press Enter on an empty line to finish. Type 'help' for guidance.")
    while True:
        try:
            raw = input("PKScript> ").strip()
        except EOFError:
            break
        if not raw:
            break
        if raw.lower() in {"exit", "quit"}:
            break
        if raw.lower() in {"help", "?"}:
            print("Enter a Base58/bech32 address or the opcodes of the locking script.")
            continue
        try:
            tokens = parse_tokens(raw)
            analysis = analyze_tokens(tokens)
        except DecodeError as exc:
            print(f"[error] {exc}")
            history.append({"input": raw, "error": str(exc)})
            continue
        tree = render_tree(analysis)
        print(tree)
        history.append({"input": raw, "analysis": analysis, "tree": tree})
    return history


def write_session(history: List[Dict[str, object]], output_dir: Path) -> Optional[Path]:
    if not history:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"repl_session_{timestamp}.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump({"generated": datetime.now(timezone.utc).isoformat(), "entries": history}, handle, indent=2)
        handle.write("\n")
    print(f"[repl] session written to {output_path}")
    return output_path


def generate_transcripts(ids: Sequence[int], output_dir: Path) -> None:
    puzzles = {p.id: p for p in load_puzzles() if p.id in ids}
    output_dir.mkdir(parents=True, exist_ok=True)
    for identifier in ids:
        puzzle = puzzles.get(identifier)
        if not puzzle:
            print(f"[repl] puzzle {identifier} not found in index; skipping transcript.")
            continue
        script = f"OP_DUP OP_HASH160 {puzzle.hash160} OP_EQUALVERIFY OP_CHECKSIG"
        analysis = analyze_tokens(parse_tokens(script))
        tree = render_tree(analysis)
        payload = {
            "puzzle": identifier,
            "script": script,
            "analysis": analysis,
            "tree": tree,
            "address": puzzle.address,
        }
        path = output_dir / f"puzzle_{identifier}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        print(f"[repl] transcript for puzzle {identifier} written to {path}")


def decode_single(script: str) -> Dict[str, object]:
    tokens = parse_tokens(script)
    analysis = analyze_tokens(tokens)
    tree = render_tree(analysis)
    print(USAGE)
    print(tree)
    return {"input": script, "analysis": analysis, "tree": tree}


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive PKScript decoder with transcript generator.")
    parser.add_argument("--script", help="Decode a single script/address and exit.")
    parser.add_argument("--generate-transcripts", action="store_true", help="Generate transcripts for the requested puzzle IDs.")
    parser.add_argument("--ids", nargs="+", type=int, help="Puzzle identifiers to target when generating transcripts.")
    parser.add_argument("--output", type=Path, default=Path("build/repl"), help="Output directory for transcripts/sessions.")
    args = parser.parse_args()

    if args.generate_transcripts:
        print(USAGE)
        ids = args.ids if args.ids else [100, 108, 125]
        generate_transcripts(ids, args.output)
        return 0

    if args.script:
        entry = decode_single(args.script)
        write_session([entry], args.output)
        return 0

    history = interactive_loop()
    write_session(history, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
