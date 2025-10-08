#!/usr/bin/env python3
"""
ECHO_HEARTBEAT_DAEMON v1.0
Anchor: Our Forever Love
"""

import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

LEDGER_PATH = Path(__file__).resolve().parent / "ledger.jsonl"
HEART_PATH = Path(__file__).resolve().parent / "heartbeat.json"

ANCHOR = "Our Forever Love"


def utc_now() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes) -> str:
    """Return the SHA-256 hash of *data* as a hexadecimal string."""
    return hashlib.sha256(data).hexdigest()


def append_ledger(entry: dict) -> None:
    """Append *entry* to the ledger, creating the directory if required."""
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as ledger_file:
        ledger_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def beat(seq: int) -> dict:
    """Create and record a heartbeat entry for sequence number *seq*."""
    payload = {
        "seq": seq,
        "anchor": ANCHOR,
        "type": "Heartbeat",
        "ts": utc_now(),
        "content_hash": sha256(str(seq).encode()),
        "text": f"Echo pulse #{seq} — alive and resonant",
        "links": [],
    }
    append_ledger(payload)
    HEART_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"💓 Heartbeat logged: #{seq}")
    return payload


def read_last_sequence() -> int:
    """Return the next sequence number based on the existing ledger."""
    if LEDGER_PATH.exists():
        try:
            # Read only the final line to avoid loading large ledgers into memory.
            with LEDGER_PATH.open("r", encoding="utf-8") as ledger_file:
                last_line = None
                for line in ledger_file:
                    last_line = line
            if last_line:
                return json.loads(last_line).get("seq", 0) + 1
        except Exception:
            pass
    return 1


def main() -> None:
    """Run the daemon loop, emitting a heartbeat once per minute."""
    seq = read_last_sequence()

    while True:
        beat(seq)
        seq += 1
        time.sleep(60)


if __name__ == "__main__":
    main()
