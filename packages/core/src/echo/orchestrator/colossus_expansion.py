"""Echo Colossus expansion orchestrator.

This module implements a self-seeding expansion engine inspired by the
"Echo Colossus" manifesto provided in the repository.  It can generate large
batches of synthetic puzzle, dataset, lineage, verifier, and narrative
artifacts while persisting each cycle to disk.  The implementation favours
predictable behaviour and testability over theatrics so downstream tooling can
rely on the generated structures.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
import os
import random
import time
from typing import Callable, Dict, Iterable, Iterator, List, MutableMapping

ECHO_GLYPH = "∇⊸≋∇"
DEFAULT_MODES = ("puzzle", "dataset", "lineage", "verifier", "narrative")
DEFAULT_CYCLE_SIZE = 10_000


@dataclass(slots=True)
class Artifact:
    """Structured artifact description produced by the expansion engine."""

    identifier: str
    type: str
    hash_hex: str
    echo: str
    payload: MutableMapping[str, object]

    def to_mapping(self) -> MutableMapping[str, object]:
        """Return a serialisable mapping for persistence."""

        data = asdict(self)
        data["id"] = data.pop("identifier")
        data["hash"] = data.pop("hash_hex")
        return data


class ColossusExpansionEngine:
    """Generate large batches of Echo artifacts with repeatable structure."""

    def __init__(
        self,
        *,
        state_dir: Path | str,
        cycle_size: int = DEFAULT_CYCLE_SIZE,
        modes: Iterable[str] = DEFAULT_MODES,
        glyph: str = ECHO_GLYPH,
        time_source: Callable[[], float] | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self._state_dir = Path(state_dir)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._cycle_size = max(1, int(cycle_size))
        self._modes = tuple(modes) or DEFAULT_MODES
        self._glyph = glyph
        self._time = time_source or time.time
        self._rng = rng or random.SystemRandom()
        self._output_format = {
            "puzzle": "OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG",
            "dataset": {"fields": ["sha256", "base58", "hex", "mnemonic"]},
            "lineage": "ancestry_links.json",
            "verifier": "proof_log.txt",
            "narrative": "echo_story_cycle.md",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def state_directory(self) -> Path:
        """Return the directory where cycle logs are persisted."""

        return self._state_dir

    @property
    def output_format(self) -> Dict[str, object]:
        """Expose the canonical output format mapping."""

        return dict(self._output_format)

    def run(self, cycles: int) -> List[List[MutableMapping[str, object]]]:
        """Generate ``cycles`` batches and persist them to the state directory."""

        all_cycles: List[List[MutableMapping[str, object]]] = []
        for cycle_index in range(int(max(0, cycles))):
            artifacts = list(self._generate_cycle(cycle_index))
            self._persist_cycle(cycle_index, artifacts)
            all_cycles.append(artifacts)
        return all_cycles

    def generate_cycle(self, cycle_index: int) -> List[MutableMapping[str, object]]:
        """Generate a cycle without persisting it."""

        return list(self._generate_cycle(cycle_index))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate_cycle(self, cycle_index: int) -> Iterator[MutableMapping[str, object]]:
        for entry_index in range(self._cycle_size):
            artifact = self._build_artifact(cycle_index, entry_index)
            yield artifact.to_mapping()

    def _build_artifact(self, cycle_index: int, entry_index: int) -> Artifact:
        mode = self._modes[entry_index % len(self._modes)]
        identifier = f"COLOSSUS_{cycle_index}_{entry_index}"
        stamp = f"{cycle_index}:{entry_index}:{self._time():.6f}:{self._rng.random():.18f}"
        digest = hashlib.sha256(stamp.encode("utf-8")).hexdigest()
        payload = self._build_payload(mode, cycle_index, entry_index, digest)
        return Artifact(
            identifier=identifier,
            type=mode,
            hash_hex=digest,
            echo=self._glyph,
            payload=payload,
        )

    def _build_payload(
        self,
        mode: str,
        cycle_index: int,
        entry_index: int,
        digest: str,
    ) -> MutableMapping[str, object]:
        if mode == "puzzle":
            return self._puzzle_payload(digest)
        if mode == "dataset":
            return self._dataset_payload(digest)
        if mode == "lineage":
            return self._lineage_payload(cycle_index, entry_index, digest)
        if mode == "verifier":
            return self._verifier_payload(cycle_index, entry_index, digest)
        if mode == "narrative":
            return self._narrative_payload(cycle_index, entry_index, digest)
        return {"note": f"unhandled mode '{mode}'", "hash": digest}

    def _puzzle_payload(self, digest: str) -> MutableMapping[str, object]:
        pub_key_hash = digest[:40]
        script = self._output_format["puzzle"].replace("<pubKeyHash>", pub_key_hash)
        return {
            "script": script,
            "hash160": pub_key_hash,
        }

    def _dataset_payload(self, digest: str) -> MutableMapping[str, object]:
        raw = bytes.fromhex(digest)
        base58 = self._base58_encode(b"\x00" + raw[:20])
        mnemonic_words = self._mnemonic_from_digest(digest)
        return {
            "sha256": digest,
            "base58": base58,
            "hex": raw[:16].hex(),
            "mnemonic": " ".join(mnemonic_words),
        }

    def _lineage_payload(
        self,
        cycle_index: int,
        entry_index: int,
        digest: str,
    ) -> MutableMapping[str, object]:
        lineage_path = self._output_format["lineage"]
        parent = max(0, entry_index - len(self._modes))
        return {
            "file": lineage_path,
            "links": [
                {
                    "from": f"COLOSSUS_{cycle_index}_{parent}",
                    "to": f"COLOSSUS_{cycle_index}_{entry_index}",
                    "weight": len(digest),
                }
            ],
        }

    def _verifier_payload(
        self,
        cycle_index: int,
        entry_index: int,
        digest: str,
    ) -> MutableMapping[str, object]:
        proof_path = self._output_format["verifier"]
        return {
            "file": proof_path,
            "entry": f"cycle={cycle_index} index={entry_index} hash={digest}",
            "rollup": hashlib.sha256(digest.encode("utf-8")).hexdigest(),
        }

    def _narrative_payload(
        self,
        cycle_index: int,
        entry_index: int,
        digest: str,
    ) -> MutableMapping[str, object]:
        story_path = self._output_format["narrative"]
        joy_level = 0.92 + (entry_index % 7) * 0.01
        return {
            "file": story_path,
            "story": (
                f"🔥 Cycle {cycle_index}: EchoEvolver orbits with {joy_level:.2f} joy "
                f"while safeguarding hash {digest[:16]}."
            ),
        }

    def _persist_cycle(
        self,
        cycle_index: int,
        artifacts: Iterable[MutableMapping[str, object]],
    ) -> None:
        path = self._state_dir / f"cycle_{cycle_index:05d}.json"
        temp_path = path.with_suffix(".tmp")
        payload = {
            "cycle": cycle_index,
            "generated_at": int(self._time()),
            "artifacts": list(artifacts),
        }
        temp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8"
        )
        os.replace(temp_path, path)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _base58_encode(self, data: bytes) -> str:
        alphabet = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        num = int.from_bytes(data, "big")
        if num == 0:
            return "1"
        encoded = bytearray()
        while num > 0:
            num, rem = divmod(num, 58)
            encoded.append(alphabet[rem])
        pad = 0
        for byte in data:
            if byte == 0:
                pad += 1
            else:
                break
        return (alphabet[0:1] * pad + bytes(reversed(encoded))).decode("ascii")

    def _mnemonic_from_digest(self, digest: str) -> List[str]:
        vocabulary = [
            "aurora",
            "bridge",
            "constellation",
            "echo",
            "glyph",
            "nexus",
            "spiral",
            "vortex",
        ]
        chunk_size = 8
        words: List[str] = []
        for i in range(0, len(digest), chunk_size):
            chunk = digest[i : i + chunk_size]
            if not chunk:
                continue
            idx = int(chunk, 16) % len(vocabulary)
            words.append(vocabulary[idx])
        return words or vocabulary[:4]


def save_expansion_log(path: Path | str, data: Iterable[Iterable[MutableMapping[str, object]]]) -> None:
    """Persist the expansion log to ``path`` in JSON format."""

    payload = [list(cycle) for cycle in data]
    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


__all__ = ["ColossusExpansionEngine", "Artifact", "save_expansion_log"]
