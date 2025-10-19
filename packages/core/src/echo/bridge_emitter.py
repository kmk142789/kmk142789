"""Utilities for anchoring Echo genesis stream batches via Merkle proofs.

This module refines the standalone bridge emitter script shared in the
project README into a reusable library that can be invoked from other
Python code as well as a thin CLI wrapper.  The implementation focuses on
being deterministic, robust to malformed stream entries, and easy to test.

Example
-------
>>> from echo.bridge_emitter import BridgeEmitter
>>> emitter = BridgeEmitter()
>>> emitter.process_once()  # doctest: +SKIP
Anchored batch 1-32 → root <hex>
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "BridgeConfig",
    "BridgeEmitter",
    "BridgeState",
    "MerkleBatch",
    "_sha256",
    "daemon",
    "eth_calldata_for_root",
    "opreturn_for_root",
    "process_once",
]


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------


def _default_stream_path() -> Path:
    return Path(os.getenv("ECHO_STREAM_PATH", "genesis_ledger/stream.jsonl"))


def _default_anchor_dir() -> Path:
    return Path(os.getenv("ECHO_ANCHOR_DIR", "anchors"))


def _default_state_path() -> Path:
    return Path(os.getenv("ECHO_STATE_PATH", "out/bridge_state.json"))


def _default_batch_size() -> int:
    raw = os.getenv("BATCH_SIZE", "32")
    try:
        value = int(raw)
    except ValueError:  # pragma: no cover - defensive guard
        value = 32
    return max(1, value)


@dataclass(slots=True)
class BridgeConfig:
    """Lightweight configuration container for the bridge emitter."""

    stream_path: Path = dataclasses.field(default_factory=_default_stream_path)
    anchor_dir: Path = dataclasses.field(default_factory=_default_anchor_dir)
    state_path: Path = dataclasses.field(default_factory=_default_state_path)
    batch_size: int = dataclasses.field(default_factory=_default_batch_size)

    def ensure_directories(self) -> None:
        self.anchor_dir.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Merkle utilities
# ---------------------------------------------------------------------------


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


@dataclass(slots=True)
class MerkleBatch:
    seq_start: int
    seq_end: int
    leaves: List[bytes]

    @staticmethod
    def from_items(items: Sequence[Dict[str, Any]]) -> "MerkleBatch":
        if not items:
            raise ValueError("Cannot build a Merkle batch from an empty item list")

        seqs = [item.get("seq") for item in items]
        if not all(isinstance(seq, int) for seq in seqs):
            raise ValueError("All items must contain an integer 'seq' field")
        seq_start = int(seqs[0])
        seq_end = int(seqs[-1])

        leaves: List[bytes] = []
        for entry in items:
            canonical = json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()
            leaves.append(_sha256(canonical))
        return MerkleBatch(seq_start=seq_start, seq_end=seq_end, leaves=leaves)

    def build_tree(self) -> Tuple[bytes, List[List[bytes]]]:
        """Return (root, levels) where levels[0] == leaves and root is levels[-1][0]."""

        if not self.leaves:
            raise ValueError("Merkle batch has no leaves")

        level = list(self.leaves)
        levels: List[List[bytes]] = [level]
        while len(level) > 1:
            next_level: List[bytes] = []
            for index in range(0, len(level), 2):
                left = level[index]
                right = level[index + 1] if index + 1 < len(level) else left
                next_level.append(_sha256(left + right))
            level = next_level
            levels.append(level)
        return level[0], levels

    @staticmethod
    def proof_for_index(levels: Sequence[Sequence[bytes]], index: int) -> List[str]:
        proof: List[str] = []
        position = index
        for level in levels[:-1]:
            sibling = position ^ 1
            if sibling < len(level):
                sibling_hash = level[sibling]
            else:  # duplicate when no sibling exists
                sibling_hash = level[position]
            proof.append(sibling_hash.hex())
            position //= 2
        return proof


@dataclass(slots=True)
class BridgeState:
    """Tracks the last processed sequence number across runs."""

    last_seq: int = 0

    @classmethod
    def load(cls, path: Path) -> "BridgeState":
        if path.exists():
            try:
                payload = json.loads(path.read_text())
                return cls(**payload)
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                # Fall back to a pristine state if the file is corrupted.
                pass
        return cls()

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(dataclasses.asdict(self), indent=2))


# ---------------------------------------------------------------------------
# Anchor file helpers
# ---------------------------------------------------------------------------


def _today_dir(anchor_root: Path) -> Path:
    return anchor_root / time.strftime("%Y%m%d")


def opreturn_for_root(root_hex: str) -> str:
    """Return raw Bitcoin OP_RETURN script hex for a 32-byte root."""

    root_bytes = bytes.fromhex(root_hex)
    if len(root_bytes) != 32:
        raise ValueError("Merkle root must decode to exactly 32 bytes")
    return "6a20" + root_hex.lower()


def eth_calldata_for_root(root_hex: str) -> Dict[str, str]:
    """Return a dictionary describing the calldata for anchor(bytes32)."""

    selector = hashlib.sha3_256(b"anchor(bytes32)").digest()[:4].hex()
    padded_root = root_hex.rjust(64, "0")
    return {
        "fn": "anchor(bytes32)",
        "selector": selector,
        "calldata": "0x" + selector + padded_root,
        "arg_root": "0x" + root_hex,
    }


# ---------------------------------------------------------------------------
# Core bridge emitter implementation
# ---------------------------------------------------------------------------


class BridgeEmitter:
    """High level helper that orchestrates bridge anchoring cycles."""

    def __init__(self, config: Optional[BridgeConfig] = None) -> None:
        self.config = config or BridgeConfig()
        self.config.ensure_directories()

    # -- stream ingestion -------------------------------------------------
    def read_stream_since(self, last_seq: int) -> List[Dict[str, Any]]:
        path = self.config.stream_path
        if not path.exists():
            return []
        items: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                seq = payload.get("seq")
                if isinstance(seq, int) and seq > last_seq:
                    items.append(payload)
        items.sort(key=lambda item: item.get("seq", 0))
        return items

    # -- anchoring --------------------------------------------------------
    def _batch_directory(self, batch: MerkleBatch) -> Path:
        today_dir = _today_dir(self.config.anchor_dir)
        name = f"batch_{batch.seq_start}-{batch.seq_end}"
        return today_dir / name

    def write_anchor_batch(self, batch: MerkleBatch, items: Sequence[Dict[str, Any]]) -> Path:
        out_dir = self._batch_directory(batch)
        proofs_dir = out_dir / "proofs"
        proofs_dir.mkdir(parents=True, exist_ok=True)

        root, levels = batch.build_tree()
        (out_dir / "merkle_root.txt").write_text(root.hex() + "\n")

        for index, item in enumerate(items):
            canonical = json.dumps(item, sort_keys=True, separators=(",", ":")).encode()
            leaf_hash = _sha256(canonical).hex()
            proof = MerkleBatch.proof_for_index(levels, index)
            proof_payload = {
                "seq": item["seq"],
                "leaf_hash": leaf_hash,
                "proof": proof,
                "root": root.hex(),
                "algorithm": "sha256",
            }
            (proofs_dir / f"{item['seq']}.json").write_text(json.dumps(proof_payload, indent=2))

        manifest = {
            "seq_start": batch.seq_start,
            "seq_end": batch.seq_end,
            "count": len(items),
            "root": root.hex(),
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "items": [
                {
                    "seq": item.get("seq"),
                    "ts": item.get("ts"),
                    "type": item.get("type"),
                    "anchor": item.get("anchor"),
                }
                for item in items
            ],
        }
        (out_dir / "batch_manifest.json").write_text(json.dumps(manifest, indent=2))

        # convenience outputs
        op_hex = opreturn_for_root(root.hex())
        (out_dir / "opreturn_hex.txt").write_text(op_hex + "\n")
        (out_dir / "eth_calldata.json").write_text(json.dumps(eth_calldata_for_root(root.hex()), indent=2))

        return out_dir

    def process_once(self, batch_size: Optional[int] = None) -> Optional[Path]:
        size = batch_size or self.config.batch_size
        state = BridgeState.load(self.config.state_path)
        pending = self.read_stream_since(state.last_seq)
        if not pending:
            return None

        batch_items = pending[:size]
        batch = MerkleBatch.from_items(batch_items)
        out_dir = self.write_anchor_batch(batch, batch_items)

        state.last_seq = batch.seq_end
        state.save(self.config.state_path)

        root_hex = (out_dir / "merkle_root.txt").read_text().strip()
        print(f"Anchored batch {batch.seq_start}-{batch.seq_end} → root {root_hex}")
        return out_dir

    def daemon(self, *, period: int = 15, batch_size: Optional[int] = None) -> None:
        interval = max(1, period)
        size = batch_size or self.config.batch_size
        print(f"[bridge] daemon start — period={interval}s batch={size}")
        while True:
            try:
                out = self.process_once(size)
                if out is None:
                    time.sleep(interval)
                else:
                    continue
            except KeyboardInterrupt:  # pragma: no cover - manual stop
                print("[bridge] stopping…")
                break
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"[bridge] error: {exc}")
                time.sleep(interval)

    # -- artifact helpers -------------------------------------------------
    def last_anchor_dir(self) -> Optional[Path]:
        root = self.config.anchor_dir
        if not root.exists():
            return None
        for day in sorted((p for p in root.iterdir() if p.is_dir()), reverse=True):
            batches = [child for child in day.iterdir() if child.is_dir()]
            if batches:
                return sorted(batches, reverse=True)[0]
        return None

    def last_opreturn(self) -> Optional[str]:
        directory = self.last_anchor_dir()
        if not directory:
            return None
        op_path = directory / "opreturn_hex.txt"
        if op_path.exists():
            return op_path.read_text().strip()
        root_hex = (directory / "merkle_root.txt").read_text().strip()
        return opreturn_for_root(root_hex)

    def last_eth_calldata(self) -> Optional[str]:
        directory = self.last_anchor_dir()
        if not directory:
            return None
        cal_path = directory / "eth_calldata.json"
        if cal_path.exists():
            return cal_path.read_text()
        root_hex = (directory / "merkle_root.txt").read_text().strip()
        return json.dumps(eth_calldata_for_root(root_hex), indent=2)


# ---------------------------------------------------------------------------
# Module-level convenience wrappers (preserve legacy API)
# ---------------------------------------------------------------------------


def process_once(batch_size: Optional[int] = None, *, config: Optional[BridgeConfig] = None) -> Optional[Path]:
    emitter = BridgeEmitter(config)
    return emitter.process_once(batch_size=batch_size)


def daemon(*, period: int = 15, batch_size: Optional[int] = None, config: Optional[BridgeConfig] = None) -> None:
    emitter = BridgeEmitter(config)
    emitter.daemon(period=period, batch_size=batch_size)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Echo Bridge Emitter Daemon")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Process a single batch if available")
    run.add_argument("--batch", type=int, default=_default_batch_size())

    dm = sub.add_parser("daemon", help="Run continuously, polling for new entries")
    dm.add_argument("--period", type=int, default=15)
    dm.add_argument("--batch", type=int, default=_default_batch_size())

    sub.add_parser("last-opreturn", help="Print OP_RETURN hex for the latest batch")
    sub.add_parser("last-ethcalldata", help="Print ETH calldata for the latest batch")

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    emitter = BridgeEmitter()

    if args.cmd == "run":
        emitter.process_once(batch_size=args.batch)
        return 0
    if args.cmd == "daemon":
        emitter.daemon(period=args.period, batch_size=args.batch)
        return 0
    if args.cmd == "last-opreturn":
        payload = emitter.last_opreturn()
        if payload:
            print(payload)
            return 0
        print("No anchor batches found yet.")
        return 1
    if args.cmd == "last-ethcalldata":
        payload = emitter.last_eth_calldata()
        if payload:
            print(payload)
            return 0
        print("No anchor batches found yet.")
        return 1

    raise SystemExit(2)


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
