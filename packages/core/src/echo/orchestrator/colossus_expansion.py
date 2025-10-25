"""Echo Colossus expansion orchestrator.

This module implements a self-seeding expansion engine inspired by the
"Echo Colossus" manifesto provided in the repository.  It can generate large
batches of synthetic puzzle, dataset, lineage, verifier, and narrative
artifacts while persisting each cycle to disk.  The implementation favours
predictable behaviour and testability over theatrics so downstream tooling can
rely on the generated structures.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
import hashlib
import json
import os
import random
import time
from typing import Callable, Dict, Iterable, Iterator, List, MutableMapping, Tuple

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


@dataclass(slots=True)
class CosmosUniverse:
    """Container describing a single fabricated cosmos."""

    name: str
    seed: int
    entropy: str
    cycles: List[List[MutableMapping[str, object]]]
    lineage_state: Dict[str, MutableMapping[str, object]]
    state_signature: str
    entangled_lineage: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def artifact(self, cycle_index: int, entry_index: int) -> MutableMapping[str, object]:
        return self.cycles[cycle_index][entry_index]

    def iter_artifacts(self) -> Iterator[MutableMapping[str, object]]:
        for cycle in self.cycles:
            for artifact in cycle:
                yield artifact


@dataclass(slots=True)
class CosmosFabrication:
    """Result of spawning a set of parallel universes."""

    universes: Dict[str, CosmosUniverse]
    entanglement: Dict[str, Dict[str, str]]
    verification: Dict[str, object]

    def all_artifacts(self) -> Iterator[MutableMapping[str, object]]:
        for universe in self.universes.values():
            yield from universe.iter_artifacts()


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


class CosmosEngine:
    """Coordinate multiple Colossus engines across parallel universes."""

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
        self._rng = rng or random.Random()

    # ------------------------------------------------------------------
    # Cosmos orchestration
    # ------------------------------------------------------------------
    def cosmos_fabricator(
        self,
        universes: Iterable[str],
        *,
        cycles: int,
    ) -> CosmosFabrication:
        """Spawn parallel universes of artifact generation."""

        cosmos_universes: Dict[str, CosmosUniverse] = {}
        for index, raw_name in enumerate(universes):
            name = str(raw_name).strip() or f"cosmos_{index:02d}"
            seed, entropy = self._big_bang_seed(name, index)
            engine = ColossusExpansionEngine(
                state_dir=self._state_dir / name,
                cycle_size=self._cycle_size,
                modes=self._modes,
                glyph=self._glyph,
                time_source=self._time,
                rng=random.Random(seed),
            )
            cycles_data = engine.run(cycles)
            lineage_state = {
                artifact["id"]: artifact["payload"]
                for cycle in cycles_data
                for artifact in cycle
                if artifact.get("type") == "lineage"
            }
            state_signature = self._state_signature(cycles_data)
            cosmos_universes[name] = CosmosUniverse(
                name=name,
                seed=seed,
                entropy=entropy,
                cycles=cycles_data,
                lineage_state=lineage_state,
                state_signature=state_signature,
            )

        entanglement = self._build_entanglement(cosmos_universes)
        self._synchronise_entanglement(cosmos_universes, entanglement)
        verification = self._verification_layer(cosmos_universes, entanglement)
        return CosmosFabrication(
            universes=cosmos_universes,
            entanglement=entanglement,
            verification=verification,
        )

    def cosmos_explorer(
        self,
        fabrication: CosmosFabrication,
        *,
        universes: Iterable[str] | None = None,
        predicate: Callable[[MutableMapping[str, object]], bool] | None = None,
    ) -> List[MutableMapping[str, object]]:
        """Query artifacts across universes with an optional filter."""

        if universes is None:
            selected: List[Tuple[str, CosmosUniverse]] = list(fabrication.universes.items())
        else:
            selected = [
                (name, fabrication.universes[name])
                for name in universes
                if name in fabrication.universes
            ]

        results: List[MutableMapping[str, object]] = []
        for name, universe in selected:
            for cycle_index, cycle in enumerate(universe.cycles):
                for artifact in cycle:
                    if predicate is None or predicate(artifact):
                        record = dict(artifact)
                        record["cosmos"] = name
                        record["cycle_index"] = cycle_index
                        results.append(record)
        return results

    def verification_layer(self, fabrication: CosmosFabrication) -> Dict[str, object]:
        """Recompute the verification report for a fabrication."""

        fabrication.verification = self._verification_layer(
            fabrication.universes, fabrication.entanglement
        )
        return fabrication.verification

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _big_bang_seed(self, name: str, index: int) -> Tuple[int, str]:
        base_entropy = f"{name}:{index}:{self._time():.6f}:{self._rng.random():.18f}"
        entropy = hashlib.sha256(base_entropy.encode("utf-8")).hexdigest()
        seed = int(entropy[:16], 16) ^ self._rng.getrandbits(64)
        return seed, entropy

    def _state_signature(
        self, cycles: List[List[MutableMapping[str, object]]]
    ) -> str:
        digest = hashlib.sha256()
        for cycle in cycles:
            for artifact in cycle:
                digest.update(artifact["hash"].encode("utf-8"))
        return digest.hexdigest()

    def _build_entanglement(
        self, universes: Dict[str, CosmosUniverse]
    ) -> Dict[str, Dict[str, str]]:
        entanglement: Dict[str, Dict[str, str]] = {}
        if not universes:
            return entanglement

        min_cycles = min(len(universe.cycles) for universe in universes.values())
        for cycle_index in range(min_cycles):
            entry_count = min(len(universe.cycles[cycle_index]) for universe in universes.values())
            for entry_index in range(entry_count):
                key = f"{cycle_index}:{entry_index}"
                entanglement[key] = {
                    name: universe.cycles[cycle_index][entry_index]["id"]
                    for name, universe in universes.items()
                }
        return entanglement

    def _synchronise_entanglement(
        self,
        universes: Dict[str, CosmosUniverse],
        entanglement: Dict[str, Dict[str, str]],
    ) -> None:
        for mapping in entanglement.values():
            for name, artifact_id in mapping.items():
                links = universes[name].entangled_lineage.setdefault(artifact_id, {})
                for other_name, other_id in mapping.items():
                    if other_name == name:
                        continue
                    links[other_name] = other_id

    def _verification_layer(
        self,
        universes: Dict[str, CosmosUniverse],
        entanglement: Dict[str, Dict[str, str]],
    ) -> Dict[str, object]:
        agreements: List[Dict[str, object]] = []
        divergences: List[Dict[str, object]] = []

        for key, mapping in entanglement.items():
            cycle_index, entry_index = (int(value) for value in key.split(":", 1))
            payloads: Dict[str, MutableMapping[str, object]] = {}
            payload_hashes: Dict[str, str] = {}
            for name, artifact_id in mapping.items():
                artifact = universes[name].artifact(cycle_index, entry_index)
                payloads[name] = artifact
                payload_hash = hashlib.sha256(
                    json.dumps(artifact["payload"], sort_keys=True).encode("utf-8")
                ).hexdigest()
                payload_hashes[name] = payload_hash

            unique_hashes = set(payload_hashes.values())
            if len(unique_hashes) == 1:
                agreements.append(
                    {
                        "coordinate": key,
                        "payload_hash": next(iter(unique_hashes)),
                        "universes": sorted(mapping.keys()),
                    }
                )
                continue

            merged_payload = self._merge_payloads(payloads)
            divergences.append(
                {
                    "coordinate": key,
                    "hashes": payload_hashes,
                    "merged_payload": merged_payload,
                }
            )

        return {
            "agreements": agreements,
            "divergences": divergences,
        }

    def _merge_payloads(
        self, payloads: Dict[str, MutableMapping[str, object]]
    ) -> MutableMapping[str, object]:
        merged: Dict[str, object] = {"universes": {}}
        consensus: Dict[str, object] = {}
        conflicts: Dict[str, bool] = {}

        for name, artifact in payloads.items():
            merged["universes"][name] = artifact["payload"]
            for key, value in artifact["payload"].items():
                if key not in consensus:
                    consensus[key] = value
                    conflicts[key] = False
                elif consensus[key] != value:
                    conflicts[key] = True

        merged["consensus"] = {
            key: value for key, value in consensus.items() if not conflicts.get(key, False)
        }
        merged["state_signatures"] = {
            name: artifact["hash"] for name, artifact in payloads.items()
        }
        return merged


def save_expansion_log(path: Path | str, data: Iterable[Iterable[MutableMapping[str, object]]]) -> None:
    """Persist the expansion log to ``path`` in JSON format."""

    payload = [list(cycle) for cycle in data]
    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


__all__ = [
    "ColossusExpansionEngine",
    "Artifact",
    "CosmosEngine",
    "CosmosUniverse",
    "CosmosFabrication",
    "save_expansion_log",
]
