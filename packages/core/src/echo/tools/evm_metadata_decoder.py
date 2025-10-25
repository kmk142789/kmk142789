"""Decode Solidity metadata appended to deployed EVM bytecode.

This module is intentionally self contained so it can be used both as a small
library from within the repository and as a command line utility.  Solidity
and other EVM tooling append a CBOR map to the end of the bytecode.  The map is
preceded by a two byte, big endian length marker.  Understanding the contents
of the map is helpful when auditing unknown bytecode blobs such as the one
provided in the user prompt for this exercise.

The implementation below includes a very small CBOR decoder that supports the
subset of the specification used by Solidity metadata (maps, arrays, byte
strings, text strings, integers and simple values).  We avoid adding a new
dependency by keeping the decoder lean and providing human friendly rendering
for byte values when possible.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import sys
from typing import Any


class CBORDecodeError(ValueError):
    """Raised when the lightweight CBOR decoder encounters malformed data."""


def _read_uint(data: bytes, index: int, additional: int) -> tuple[int, int]:
    if additional < 24:
        return additional, index
    if additional == 24:
        if index >= len(data):
            raise CBORDecodeError("unexpected end of CBOR data (uint8 length)")
        return data[index], index + 1
    if additional == 25:
        end = index + 2
        if end > len(data):
            raise CBORDecodeError("unexpected end of CBOR data (uint16 length)")
        return int.from_bytes(data[index:end], "big"), end
    if additional == 26:
        end = index + 4
        if end > len(data):
            raise CBORDecodeError("unexpected end of CBOR data (uint32 length)")
        return int.from_bytes(data[index:end], "big"), end
    if additional == 27:
        end = index + 8
        if end > len(data):
            raise CBORDecodeError("unexpected end of CBOR data (uint64 length)")
        return int.from_bytes(data[index:end], "big"), end
    if additional == 31:
        raise CBORDecodeError("indefinite length items are not supported")
    raise CBORDecodeError(f"unsupported additional information value: {additional}")


def _decode_cbor(data: bytes, index: int = 0) -> tuple[Any, int]:
    if index >= len(data):
        raise CBORDecodeError("unexpected end of CBOR data")

    initial = data[index]
    index += 1
    major = initial >> 5
    additional = initial & 0x1F

    if major == 0:  # unsigned integer
        value, index = _read_uint(data, index, additional)
        return value, index
    if major == 1:  # negative integer
        value, index = _read_uint(data, index, additional)
        return -1 - value, index
    if major == 2:  # byte string
        length, index = _read_uint(data, index, additional)
        end = index + length
        if end > len(data):
            raise CBORDecodeError("byte string exceeds available data")
        return data[index:end], end
    if major == 3:  # text string (UTF-8)
        length, index = _read_uint(data, index, additional)
        end = index + length
        if end > len(data):
            raise CBORDecodeError("text string exceeds available data")
        return data[index:end].decode("utf-8", errors="strict"), end
    if major == 4:  # array
        length, index = _read_uint(data, index, additional)
        items = []
        for _ in range(length):
            item, index = _decode_cbor(data, index)
            items.append(item)
        return items, index
    if major == 5:  # map
        length, index = _read_uint(data, index, additional)
        mapping: dict[Any, Any] = {}
        for _ in range(length):
            key, index = _decode_cbor(data, index)
            value, index = _decode_cbor(data, index)
            mapping[key] = value
        return mapping, index
    if major == 6:  # tag
        tag_value, index = _read_uint(data, index, additional)
        tagged, index = _decode_cbor(data, index)
        return {"tag": tag_value, "value": tagged}, index
    if major == 7:
        if additional == 20:
            return False, index
        if additional == 21:
            return True, index
        if additional == 22:
            return None, index
        if additional == 23:
            return None, index
        if additional in (24, 25, 26, 27):
            raise CBORDecodeError("floating point values are not supported in metadata")
        if additional < 20:
            return additional, index
        raise CBORDecodeError(f"unsupported simple value: {additional}")

    raise CBORDecodeError(f"unsupported major type: {major}")


def decode_cbor(data: bytes) -> Any:
    """Decode the supplied CBOR payload.

    The function validates that the entire input is consumed to avoid silently
    ignoring trailing garbage.
    """

    value, index = _decode_cbor(data, 0)
    if index != len(data):
        raise CBORDecodeError("trailing data after CBOR structure")
    return value


def _is_probably_printable(value: bytes) -> bool:
    if not value:
        return True
    return all(32 <= byte <= 126 for byte in value)


def _humanise(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(_humanise(key)): _humanise(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_humanise(item) for item in value]
    if isinstance(value, bytes):
        if _is_probably_printable(value):
            return value.decode("utf-8", errors="ignore")
        return "0x" + value.hex()
    return value


def _clean_hex_string(raw: str) -> str:
    digits = []
    for char in raw:
        if char in "0123456789abcdefABCDEF":
            digits.append(char)
    if len(digits) % 2 != 0:
        raise ValueError("hex string must contain an even number of characters")
    return "".join(digits)


def load_bytecode(source: str) -> bytes:
    if source == "-":
        raw = sys.stdin.read()
    else:
        path = Path(source)
        if path.exists() and path.is_file():
            raw = path.read_text(encoding="utf-8")
        else:
            raw = source
    normalized = raw.replace("0x", "").replace("0X", "")
    cleaned = _clean_hex_string(normalized)
    if not cleaned:
        raise ValueError("no hexadecimal characters found in input")
    return bytes.fromhex(cleaned)


@dataclass(slots=True)
class MetadataResult:
    bytecode_length: int
    metadata_length: int
    metadata_bytes: bytes
    metadata: Any


def extract_metadata(bytecode: bytes) -> MetadataResult:
    if len(bytecode) < 2:
        raise ValueError("bytecode too short to contain metadata")
    metadata_length = int.from_bytes(bytecode[-2:], "big")
    if metadata_length == 0:
        raise ValueError("metadata length marker is zero")
    if metadata_length + 2 > len(bytecode):
        raise ValueError("metadata length exceeds bytecode size")
    metadata_bytes = bytecode[-metadata_length - 2 : -2]
    try:
        decoded = decode_cbor(metadata_bytes)
    except CBORDecodeError:
        decoded = None
    return MetadataResult(
        bytecode_length=len(bytecode),
        metadata_length=metadata_length,
        metadata_bytes=metadata_bytes,
        metadata=_humanise(decoded) if decoded is not None else None,
    )


def describe_metadata(result: MetadataResult) -> str:
    lines = [
        f"Bytecode length : {result.bytecode_length} bytes",
        f"Metadata length : {result.metadata_length} bytes",
        f"Metadata (hex)  : 0x{result.metadata_bytes.hex()}",
    ]
    if isinstance(result.metadata, dict):
        lines.append("Decoded map     :")
        for key, value in sorted(result.metadata.items()):
            formatted = value
            if isinstance(value, (list, dict)):
                formatted = repr(value)
            lines.append(f"  - {key}: {formatted}")
    elif result.metadata is not None:
        lines.append(f"Decoded value   : {result.metadata!r}")
    else:
        lines.append("Decoded value   : <unable to decode>")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Decode Solidity metadata from EVM bytecode")
    parser.add_argument("source", help="Hex bytecode string, '-' for stdin, or path to a file")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit metadata as a JSON-compatible representation",
    )
    args = parser.parse_args(argv)

    try:
        bytecode = load_bytecode(args.source)
        result = extract_metadata(bytecode)
    except (ValueError, CBORDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        import json

        json_payload = {
            "bytecode_length": result.bytecode_length,
            "metadata_length": result.metadata_length,
            "metadata_hex": "0x" + result.metadata_bytes.hex(),
            "metadata": result.metadata,
        }
        print(json.dumps(json_payload, indent=2, sort_keys=True))
    else:
        print(describe_metadata(result))
    return 0


__all__ = [
    "CBORDecodeError",
    "MetadataResult",
    "decode_cbor",
    "describe_metadata",
    "extract_metadata",
    "load_bytecode",
    "main",
]


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
