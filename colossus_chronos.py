"""Chronos Lattice utilities for Echo Colossus.

This module centralises the time-pulse lattice bookkeeping shared by the
generator and the explorer API.  It is intentionally stdlib-only so the
existing lightweight tooling keeps working in minimal environments.
"""

from __future__ import annotations

import json
import pathlib
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


def _sha256_hex(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def _now_unix() -> int:
    return int(time.time())


@dataclass
class ChronosArtifact:
    """In-memory representation of a single lattice artifact."""

    ordinal: int
    record_id: int
    artifact_id: str
    file: str
    payload_sha256: str
    timestamp_unix_ns: int
    time_pulse_signature: str
    previous_signature: Optional[str]
    chain_anchor: str

    def serialise(self) -> Dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "record_id": self.record_id,
            "artifact_id": self.artifact_id,
            "file": self.file,
            "payload_sha256": self.payload_sha256,
            "timestamp_unix_ns": self.timestamp_unix_ns,
            "time_pulse_signature": self.time_pulse_signature,
            "previous_signature": self.previous_signature,
            "chain_anchor": self.chain_anchor,
        }


class ChronosLattice:
    """Manages cycle state and time-pulse signatures for Echo Colossus."""

    VERSION = 1

    def __init__(self, root: pathlib.Path):
        self.root = root
        self.lattice_dir = self.root / "build" / "chronos"
        self.lattice_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.lattice_dir / "lattice_state.json"
        self._state = self._load_state()
        self._current_cycle: Optional[Dict[str, object]] = None
        self._previous_signature: Optional[str] = self._state.get("latest_signature")
        self._last_timestamp_ns: int = 0

    # ------------------------------------------------------------------
    # Static helpers
    @staticmethod
    def compute_signature(
        *,
        cycle_seed: str,
        ordinal: int,
        record_id: int,
        rel_path: str,
        payload_sha256: str,
        timestamp_unix_ns: int,
        previous_signature: Optional[str],
    ) -> Tuple[str, str]:
        """Derive the time-pulse signature and chain anchor."""

        material = (
            f"{cycle_seed}|{ordinal}|{record_id}|{rel_path}|{payload_sha256}|"
            f"{timestamp_unix_ns}"
        )
        if previous_signature:
            material += f"|prev:{previous_signature}"
        signature = _sha256_hex(material.encode())
        chain_anchor = _sha256_hex(
            f"{signature}|{cycle_seed}|{ordinal}".encode()
        )[:48]
        return signature, chain_anchor

    # ------------------------------------------------------------------
    # State lifecycle
    def _load_state(self) -> Dict[str, object]:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return {"version": self.VERSION, "cycles": [], "latest_signature": None}

    def start_cycle(self, artifact_total: int) -> Dict[str, object]:
        """Initialise a new cycle using the persisted state."""

        cycles: List[Dict[str, object]] = self._state.get("cycles", [])  # type: ignore[assignment]
        cycle_index = (cycles[-1]["cycle_index"] + 1) if cycles else 1  # type: ignore[index]
        seed_material = f"{cycle_index}|{time.time_ns()}|{artifact_total}".encode()
        cycle_seed = _sha256_hex(seed_material)
        cycle = {
            "cycle_index": cycle_index,
            "cycle_seed": cycle_seed,
            "artifact_total": artifact_total,
            "started_at_unix": _now_unix(),
            "previous_cycle_signature": self._previous_signature,
            "artifacts": [],
            "future_anchors": [],
        }
        self._current_cycle = cycle
        self._last_timestamp_ns = 0
        return cycle

    def register_artifact(
        self,
        *,
        ordinal: int,
        record_id: int,
        rel_path: str,
        payload_sha256: str,
    ) -> Dict[str, object]:
        """Record an artifact for the active cycle and compute signatures."""

        if self._current_cycle is None:
            raise RuntimeError("start_cycle() must be called before registering artifacts")

        timestamp_ns = time.time_ns()
        if timestamp_ns <= self._last_timestamp_ns:
            timestamp_ns = self._last_timestamp_ns + 1
        self._last_timestamp_ns = timestamp_ns

        previous_signature = None
        artifacts: List[Dict[str, object]] = self._current_cycle["artifacts"]  # type: ignore[assignment]
        if artifacts:
            previous_signature = artifacts[-1]["time_pulse_signature"]  # type: ignore[index]
        elif self._previous_signature:
            previous_signature = self._previous_signature

        cycle_seed = self._current_cycle["cycle_seed"]  # type: ignore[index]
        signature, chain_anchor = self.compute_signature(
            cycle_seed=cycle_seed,
            ordinal=ordinal,
            record_id=record_id,
            rel_path=rel_path,
            payload_sha256=payload_sha256,
            timestamp_unix_ns=timestamp_ns,
            previous_signature=previous_signature,
        )

        artifact_id = f"cycle_{self._current_cycle['cycle_index']:05d}#artifact_{ordinal:05d}"
        artifact = ChronosArtifact(
            ordinal=ordinal,
            record_id=record_id,
            artifact_id=artifact_id,
            file=rel_path,
            payload_sha256=payload_sha256,
            timestamp_unix_ns=timestamp_ns,
            time_pulse_signature=signature,
            previous_signature=previous_signature,
            chain_anchor=chain_anchor,
        )
        artifacts.append(artifact.serialise())

        return {
            "cycle": self._current_cycle["cycle_index"],
            "ordinal": ordinal,
            "artifact_id": artifact_id,
            "signature": signature,
            "previous_signature": previous_signature,
            "timestamp_unix_ns": timestamp_ns,
            "chain_anchor": chain_anchor,
        }

    def finalize_cycle(self) -> Dict[str, object]:
        """Persist the active cycle and update lattice state."""

        if self._current_cycle is None:
            raise RuntimeError("start_cycle() must be called before finalize_cycle()")

        self._current_cycle["completed_at_unix"] = _now_unix()
        next_cycle_index = self._current_cycle["cycle_index"] + 1  # type: ignore[operator]
        future_anchors = self._generate_future_anchors(next_cycle_index)
        self._current_cycle["future_anchors"] = future_anchors

        cycles: List[Dict[str, object]] = self._state.setdefault("cycles", [])  # type: ignore[assignment]
        cycles.append(self._current_cycle)

        artifacts: List[Dict[str, object]] = self._current_cycle["artifacts"]  # type: ignore[assignment]
        if artifacts:
            self._state["latest_signature"] = artifacts[-1]["time_pulse_signature"]
        else:
            self._state["latest_signature"] = self._previous_signature

        self._write_state()

        cycle_path = self.lattice_dir / f"cycle_{self._current_cycle['cycle_index']:05d}.json"
        cycle_path.write_text(
            json.dumps(self._current_cycle, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        anchors_path = self.lattice_dir / "future_anchors.json"
        anchors_path.write_text(
            json.dumps(future_anchors, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        finalized = self._current_cycle
        self._current_cycle = None
        self._previous_signature = self._state.get("latest_signature")
        return finalized

    # ------------------------------------------------------------------
    def _generate_future_anchors(self, next_cycle_index: int, *, count: int = 5) -> List[Dict[str, object]]:
        cycle_seed = self._current_cycle["cycle_seed"]  # type: ignore[index]
        anchors: List[Dict[str, object]] = []
        for slot in range(1, count + 1):
            anchor_seed = _sha256_hex(f"{cycle_seed}|future|{slot}".encode())
            anchors.append(
                {
                    "id": f"cycle_{next_cycle_index:05d}#artifact_{slot:05d}",
                    "predicted_slot": slot,
                    "seed_fragment": anchor_seed[:24],
                    "ready": False,
                }
            )
        return anchors

    def _write_state(self) -> None:
        self.state_path.write_text(
            json.dumps(self._state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


class ChronosLatticeExplorer:
    """Read-only utilities for serving Chronos lattice data."""

    def __init__(self, root: pathlib.Path):
        self.root = root
        self.lattice_dir = self.root / "build" / "chronos"
        self.state_path = self.lattice_dir / "lattice_state.json"

    # ------------------------------------------------------------------
    def _load_state(self) -> Dict[str, object]:
        if not self.state_path.exists():
            raise FileNotFoundError("Chronos lattice state not found")
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def cycle_summaries(self) -> List[Dict[str, object]]:
        state = self._load_state()
        cycles: Iterable[Dict[str, object]] = state.get("cycles", [])  # type: ignore[assignment]
        summaries: List[Dict[str, object]] = []
        for cycle in cycles:
            artifacts: List[Dict[str, object]] = cycle.get("artifacts", [])  # type: ignore[assignment]
            summaries.append(
                {
                    "cycle_index": cycle.get("cycle_index"),
                    "artifact_total": cycle.get("artifact_total"),
                    "started_at_unix": cycle.get("started_at_unix"),
                    "completed_at_unix": cycle.get("completed_at_unix"),
                    "first_signature": artifacts[0]["time_pulse_signature"] if artifacts else None,
                    "last_signature": artifacts[-1]["time_pulse_signature"] if artifacts else None,
                    "future_anchor_count": len(cycle.get("future_anchors", [])),
                }
            )
        return summaries

    def cycle_detail(self, cycle_index: int) -> Dict[str, object]:
        state = self._load_state()
        for cycle in state.get("cycles", []):  # type: ignore[assignment]
            if cycle.get("cycle_index") == cycle_index:
                return cycle
        raise KeyError(f"cycle {cycle_index} not found")

    def artifact_lookup(self, key: str) -> Tuple[Dict[str, object], Dict[str, object]]:
        state = self._load_state()
        for cycle in state.get("cycles", []):  # type: ignore[assignment]
            for artifact in cycle.get("artifacts", []):  # type: ignore[assignment]
                if (
                    key == str(artifact.get("record_id"))
                    or key == artifact.get("artifact_id")
                    or key == artifact.get("time_pulse_signature")
                ):
                    return artifact, cycle
        raise KeyError(f"artifact {key} not found")

    def lineage(self) -> List[Dict[str, object]]:
        state = self._load_state()
        lineage: List[Dict[str, object]] = []
        for cycle in state.get("cycles", []):  # type: ignore[assignment]
            for artifact in cycle.get("artifacts", []):  # type: ignore[assignment]
                lineage.append(
                    {
                        "cycle": cycle.get("cycle_index"),
                        "ordinal": artifact.get("ordinal"),
                        "artifact_id": artifact.get("artifact_id"),
                        "signature": artifact.get("time_pulse_signature"),
                        "previous_signature": artifact.get("previous_signature"),
                        "timestamp_unix_ns": artifact.get("timestamp_unix_ns"),
                    }
                )
        return lineage

    def reconstruct(self, key: str) -> Dict[str, object]:
        artifact, cycle = self.artifact_lookup(key)
        rel_path = artifact.get("file")
        if not isinstance(rel_path, str):
            raise KeyError(f"artifact {key} missing file reference")
        record_path = self.root / rel_path
        if not record_path.exists():
            raise FileNotFoundError(f"artifact file {rel_path} missing")
        record = json.loads(record_path.read_text(encoding="utf-8"))

        payload_match = False
        checksum = record.get("checksum")
        if isinstance(checksum, str):
            payload_match = checksum == artifact.get("payload_sha256")

        cycle_seed = cycle.get("cycle_seed")
        previous_signature = artifact.get("previous_signature")
        ordinal = int(artifact.get("ordinal"))
        record_id = int(artifact.get("record_id"))
        timestamp_ns = int(artifact.get("timestamp_unix_ns"))
        if not isinstance(cycle_seed, str):
            raise KeyError("cycle seed missing from lattice state")

        expected_signature, expected_anchor = ChronosLattice.compute_signature(
            cycle_seed=cycle_seed,
            ordinal=ordinal,
            record_id=record_id,
            rel_path=rel_path,
            payload_sha256=str(artifact.get("payload_sha256")),
            timestamp_unix_ns=timestamp_ns,
            previous_signature=previous_signature if isinstance(previous_signature, str) else None,
        )

        signature_match = expected_signature == artifact.get("time_pulse_signature")
        anchor_match = expected_anchor == artifact.get("chain_anchor")

        return {
            "artifact": artifact,
            "cycle": cycle,
            "record": record,
            "verification": {
                "payload_sha256_matches": payload_match,
                "signature_matches": signature_match,
                "chain_anchor_matches": anchor_match,
                "recomputed_signature": expected_signature,
                "recomputed_anchor": expected_anchor,
            },
        }

