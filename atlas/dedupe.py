"""Artifact deduplication across universes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
import hashlib
import json

from .graph import ArtifactNode, FederationGraph
from .types import Entry


@dataclass(slots=True)
class DedupeRecord:
    signature: str
    nodes: List[str]
    universes: List[str]
    latest_timestamp: str | None

    def to_dict(self) -> Dict[str, object]:
        return {
            "signature": self.signature,
            "nodes": list(self.nodes),
            "universes": list(self.universes),
            "latest_timestamp": self.latest_timestamp,
        }


@dataclass
class DedupeIndex:
    records: List[DedupeRecord]

    def to_dict(self) -> Dict[str, object]:
        return {"records": [record.to_dict() for record in self.records]}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, sort_keys=True)

    @classmethod
    def load(cls, path: Path) -> "DedupeIndex":
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        records = [DedupeRecord(**record) for record in payload.get("records", [])]
        return cls(records=records)


def _fingerprint(node: ArtifactNode) -> str:
    payload = {
        "metadata": node.metadata,
        "content": node.content,
    }
    serialised = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def build_dedupe_index(graph: FederationGraph) -> DedupeIndex:
    """Build a :class:`DedupeIndex` from *graph*."""

    buckets: Dict[str, List[ArtifactNode]] = {}
    for node in graph.artifacts:
        signature = _fingerprint(node)
        buckets.setdefault(signature, []).append(node)

    records: List[DedupeRecord] = []
    for signature, nodes in sorted(buckets.items()):
        universes = sorted({node.universe for node in nodes})
        latest_timestamp = max((node.timestamp for node in nodes if node.timestamp), default=None)
        records.append(
            DedupeRecord(
                signature=signature,
                nodes=[node.node_id for node in nodes],
                universes=universes,
                latest_timestamp=latest_timestamp,
            )
        )
    return DedupeIndex(records=records)


def _build_search_index(graph: FederationGraph, index_path: Path) -> None:
    index_path.mkdir(parents=True, exist_ok=True)
    entries = []
    for node in graph.artifacts:
        text_bits: List[str] = []
        for value in node.metadata.values():
            if isinstance(value, str):
                text_bits.append(value)
            else:
                text_bits.append(json.dumps(value, sort_keys=True))
        if node.content:
            text_bits.append(node.content)
        entry = {
            "node_id": node.node_id,
            "universe": node.universe,
            "artifact_id": node.artifact_id,
            "timestamp": node.timestamp,
            "text": " \n".join(text_bits),
        }
        harmonix = node.metadata.get("harmonix")
        if isinstance(harmonix, dict):
            entry["cycle"] = harmonix.get("cycle")
            entry["puzzle_id"] = harmonix.get("puzzle_id")
            entry["address"] = harmonix.get("address")
        entries.append(entry)
    payload = {"version": 1, "entries": entries}
    with index_path.joinpath("index.json").open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)


def normalize_address(addr: str) -> str:
    """Normalize a harmonix-style address for comparisons."""

    return (addr or "").strip().lower()


def dedupe_latest(entries: List[Entry]) -> List[Entry]:
    """Keep only the latest cycle per (puzzle, address) pair."""

    best: Dict[Tuple[int, str], Entry] = {}
    for entry in entries:
        key = (int(entry["puzzle_id"]), normalize_address(entry.get("address", "")))
        previous = best.get(key)
        if previous is None or int(entry["cycle"]) > int(previous["cycle"]):
            best[key] = entry
    return list(best.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dedupe artifacts across the federation")
    parser.add_argument("--graph", type=Path, required=True, help="Path to global graph JSON")
    parser.add_argument("--out", type=Path, required=True, help="Path to write dedupe index JSON")
    parser.add_argument(
        "--search-index",
        type=Path,
        default=None,
        help="Optional path to search index directory (defaults to sibling of output)",
    )
    args = parser.parse_args(argv)

    graph = FederationGraph.load(args.graph)
    index = build_dedupe_index(graph)
    index.save(args.out)

    search_index_path = args.search_index or args.out.parent / "federated_search_index"
    _build_search_index(graph, search_index_path)
    print(
        f"Dedupe index with {len(index.records)} signatures written to {args.out}; "
        f"search index stored in {search_index_path}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
