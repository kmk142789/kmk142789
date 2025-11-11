"""High-volume OP_RETURN fixture generator for integration tests."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.opreturn.claims import parse_claim_records, validate_claim_windows

RAW_HEX_TRANSACTION: Mapping[str, object] = {
    "txid": "1111111111111111111111111111111111111111111111111111111111111111",
    "block_time": "2025-03-15T12:30:00Z",
    "hex": (
        "01000000010000000000000000000000000000000000000000000000000000000000000000"
        "ffffffff00ffffffff010000000000000000376a354f505f52455455524e3a20436c61696d"
        "2066726f6d20536f6c6f6d6f6e2062726f73202f2f206f776e6572206f662077616c6c6574"
        "00000000"
    ),
}

DECODED_REFERENCE_TRANSACTION: Mapping[str, object] = {
    "txid": "2222222222222222222222222222222222222222222222222222222222222222",
    "block_time": "2025-04-01T05:00:00+00:00",
    "vout": [
        {
            "n": 0,
            "script_hex": "6a267061796c6f6164203d3e204f776e6572206f662077616c6c6574206174746573746174696f6e",
        }
    ],
}

BASE_TIME = datetime(2025, 5, 1, tzinfo=timezone.utc)


def _encode_op_return_script(payload: str) -> str:
    data = payload.encode("utf-8")
    prefix = bytearray([0x6A])
    length = len(data)

    if length <= 75:
        prefix.append(length)
    elif length < 0x100:
        prefix.extend((0x4C, length))
    elif length < 0x10000:
        prefix.append(0x4D)
        prefix.extend(length.to_bytes(2, "little"))
    else:  # pragma: no cover - defensive upper bound
        raise ValueError("Payload too large for fixture generation")

    return (bytes(prefix) + data).hex()


def _synth_transaction(index: int) -> Dict[str, object]:
    if index == 0:
        return dict(RAW_HEX_TRANSACTION)
    if index == 1:
        return dict(DECODED_REFERENCE_TRANSACTION)

    sequence = index - 2
    block_time = BASE_TIME + timedelta(minutes=sequence)
    txid = f"{index + 1:064x}"

    variant = sequence % 4
    if variant == 0:
        payload = f"payload => Claim from Solomon bros batch {sequence + 1:04d}"
    elif variant == 1:
        payload = f"payload => Legal representative attestation {sequence + 1:04d}"
    elif variant == 2:
        payload = f"payload => Owner of wallet attestation {sequence + 1:04d}"
    else:
        payload = f"payload => Claim window review {sequence + 1:04d}"

    return {
        "txid": txid,
        "block_time": block_time.isoformat(),
        "vout": [
            {
                "n": 0,
                "script_hex": _encode_op_return_script(payload),
            }
        ],
    }


def _iter_transactions(total: int) -> Iterator[Dict[str, object]]:
    for idx in range(total):
        yield _synth_transaction(idx)


def _write_json_array(path: Path, records: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("[\n")
        first = True
        for record in records:
            if not first:
                handle.write(",\n")
            else:
                first = False
            blob = json.dumps(record, indent=2)
            indented = "\n".join(f"  {line}" for line in blob.splitlines())
            handle.write(indented)
        if not first:
            handle.write("\n")
        handle.write("]\n")


def generate(root: Path, *, total_records: int = 1_200) -> None:
    if total_records < 2:
        raise ValueError("total_records must be at least 2")

    transactions_path = root / "tests" / "data" / "opreturn" / "sample_transactions.json"
    parsed_path = root / "tests" / "data" / "opreturn" / "expected_parsed_records.json"

    _write_json_array(transactions_path, _iter_transactions(total_records))

    parsed_records = parse_claim_records(_iter_transactions(total_records))
    parsed_dicts = [record.as_dict() for record in parsed_records]
    _write_json_array(parsed_path, parsed_dicts)

    validate_claim_windows(parsed_records, as_of=BASE_TIME + timedelta(days=120))


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate OP_RETURN fixtures")
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root (defaults to two levels up)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1_200,
        help="Total number of transactions to emit",
    )
    args = parser.parse_args()

    generate(args.root, total_records=args.count)


if __name__ == "__main__":
    main()
