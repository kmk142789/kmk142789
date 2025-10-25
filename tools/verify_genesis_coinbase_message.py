"""Verify the genesis block coinbase message from a raw transaction dump."""
from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_RAW_PATH = Path(__file__).resolve().parents[1] / "proofs" / "genesis_coinbase_raw.hex"
EXPECTED_MESSAGE = "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"


def read_varint(data: bytes, offset: int) -> tuple[int, int]:
    """Return the decoded varint and the next offset."""
    prefix = data[offset]
    if prefix < 0xFD:
        return prefix, offset + 1
    if prefix == 0xFD:
        return int.from_bytes(data[offset + 1 : offset + 3], "little"), offset + 3
    if prefix == 0xFE:
        return int.from_bytes(data[offset + 1 : offset + 5], "little"), offset + 5
    return int.from_bytes(data[offset + 1 : offset + 9], "little"), offset + 9


def extract_coinbase_message(raw_tx: bytes) -> str:
    """Parse the genesis coinbase transaction and return the embedded newspaper headline."""
    offset = 0
    # version (4 bytes)
    offset += 4

    # input count
    input_count, offset = read_varint(raw_tx, offset)
    if input_count != 1:
        raise ValueError("Genesis coinbase must have exactly one input")

    # previous output (32-byte hash + 4-byte index)
    offset += 36

    script_len, offset = read_varint(raw_tx, offset)
    script_sig = raw_tx[offset : offset + script_len]
    offset += script_len

    # sequence
    offset += 4

    # The ASCII headline starts after the pushdata prefix: 0x04ffff001d0104
    headline_start = script_sig.find(b"The Times")
    if headline_start == -1:
        raise ValueError("Unable to locate The Times headline in scriptSig")

    message_bytes = script_sig[headline_start:]
    message = message_bytes.decode("ascii", errors="strict")
    return message


def verify_coinbase(path: Path, expected: str) -> str:
    raw_hex = path.read_text().strip()
    try:
        raw_tx = bytes.fromhex(raw_hex)
    except ValueError as exc:
        raise ValueError(f"Invalid hex data in {path}") from exc

    message = extract_coinbase_message(raw_tx)
    if message != expected:
        raise ValueError(
            "Genesis headline mismatch:\n"
            f"  expected: {expected!r}\n"
            f"  observed: {message!r}"
        )
    return message


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw",
        type=Path,
        default=DEFAULT_RAW_PATH,
        help="Path to the hex-encoded genesis coinbase transaction",
    )
    parser.add_argument(
        "--expected",
        default=EXPECTED_MESSAGE,
        help="Expected ASCII headline embedded in the coinbase script",
    )
    args = parser.parse_args(argv)

    message = verify_coinbase(args.raw, args.expected)
    print("Genesis coinbase headline confirmed:")
    print(f"  {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
