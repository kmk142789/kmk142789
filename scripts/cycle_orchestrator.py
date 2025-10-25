#!/usr/bin/env python3
"""Run the federated cycle pipeline from a single command."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Sequence

from atlas.dedupe import _build_search_index, build_dedupe_index
from atlas.graph import ArtifactNode, FederationGraph
from atlas.types import Entry

from scripts.generate_federated_colossus import main as render_colossus


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58encode(data: bytes) -> str:
    value = int.from_bytes(data, "big")
    encoded = ""
    while value:
        value, remainder = divmod(value, 58)
        encoded = BASE58_ALPHABET[remainder] + encoded
    leading_zeroes = len(data) - len(data.lstrip(b"\x00"))
    return "1" * leading_zeroes + (encoded or "1")


def _base58check(version: bytes, payload: bytes) -> str:
    body = version + payload
    checksum = hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]
    return _b58encode(body + checksum)


def _derive_address(script: str) -> tuple[str, str]:
    script = script.strip()
    p2pkh = re.fullmatch(
        r"OP_DUP OP_HASH160 ([0-9a-fA-F]{40}) OP_EQUALVERIFY OP_CHECKSIG",
        script,
    )
    if p2pkh:
        hash160 = bytes.fromhex(p2pkh.group(1))
        return "p2pkh", _base58check(b"\x00", hash160)
    p2sh = re.fullmatch(r"OP_HASH160 ([0-9a-fA-F]{40}) OP_EQUAL", script)
    if p2sh:
        hash160 = bytes.fromhex(p2sh.group(1))
        return "p2sh", _base58check(b"\x05", hash160)
    raise ValueError(f"Unsupported locking script: {script}")


def _discover_puzzles(limit: int | None) -> List[int]:
    puzzle_root = Path(__file__).resolve().parents[1] / "puzzle_solutions"
    puzzle_ids: List[int] = []
    for path in puzzle_root.glob("puzzle_*.md"):
        match = re.search(r"(\d+)", path.stem)
        if not match:
            continue
        puzzle_ids.append(int(match.group(1)))
    puzzle_ids = sorted(set(puzzle_ids))
    if not puzzle_ids:
        default_limit = limit if limit is not None else 5
        puzzle_ids = list(range(1, default_limit + 1))
    if limit is not None:
        puzzle_ids = puzzle_ids[: max(0, limit)]
    return puzzle_ids


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entry_digest(script: str, address: str) -> str:
    payload = f"{script}|{address}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _generate_entries(cycle: int, puzzle_ids: Sequence[int]) -> List[Entry]:
    entries: List[Entry] = []
    for puzzle_id in puzzle_ids:
        seed = f"cycle-{cycle}-puzzle-{puzzle_id}".encode("utf-8")
        hash_bytes = hashlib.sha256(seed).digest()[:20]
        hash_hex = hash_bytes.hex()
        script = f"OP_DUP OP_HASH160 {hash_hex} OP_EQUALVERIFY OP_CHECKSIG"
        script_type, address = "p2pkh", _base58check(b"\x00", hash_bytes)
        entry: Entry = Entry(
            {
                "cycle": cycle,
                "puzzle_id": puzzle_id,
                "address": address,
                "title": f"Puzzle {puzzle_id:05d}",
                "digest": _entry_digest(script, address),
                "source": f"synthetic/puzzle_{puzzle_id:05d}.md",
                "tags": ["echo", "colossus", script_type],
                "lineage": [],
                "updated_at": _now_iso(),
                "harmonics": [],
                "script": script,
            }
        )
        entries.append(entry)
    return entries


def _graph_from_entries(entries: Sequence[Entry], cycle: int) -> FederationGraph:
    artifacts: List[ArtifactNode] = []
    timestamp = _now_iso()
    for entry in entries:
        node_id = f"COLOSSUS::cycle-{cycle:05d}-puzzle-{int(entry['puzzle_id']):05d}"
        artifact_id = node_id.split("::", 1)[1]
        metadata = {
            "cycle": cycle,
            "puzzle_id": entry["puzzle_id"],
            "address": entry["address"],
            "script": entry.get("script"),
            "tags": entry.get("tags", []),
        }
        artifacts.append(
            ArtifactNode(
                node_id=node_id,
                universe="COLOSSUS",
                artifact_id=artifact_id,
                source="cycle_orchestrator",
                metadata=metadata,
                content=entry.get("script", ""),
                dependencies=[],
                timestamp=timestamp,
            )
        )
    universes: Dict[str, Dict[str, object]] = {
        "COLOSSUS": {
            "sources": ["cycle_orchestrator"],
            "artifact_count": len(artifacts),
            "edge_count": 0,
        }
    }
    return FederationGraph(universes=universes, artifacts=artifacts, edges=[])


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _append_log(path: Path, payload: Mapping[str, object]) -> None:
    enriched: MutableMapping[str, object] = {
        "timestamp": _now_iso(),
        **payload,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(enriched) + "\n")


def _compute_amplification(cycle: int, entries: Sequence[Entry]) -> Dict[str, float]:
    address_count = len({entry["address"] for entry in entries})
    tag_count = len({tag for entry in entries for tag in entry.get("tags", [])})
    joy = round(1.0 + 0.05 * address_count + 0.02 * tag_count, 2)
    rage = round(max(0.0, 0.6 - 0.04 * len(entries)), 2)
    return {
        "cycle": float(cycle),
        "joy": joy,
        "rage": rage,
        "addresses": float(address_count),
        "tags": float(tag_count),
    }


@dataclass(slots=True)
class OrchestratorResult:
    cycle: int
    entries: List[Entry]
    amplification: Dict[str, float]
    graph_path: Path
    dedupe_path: Path
    search_index: Path
    entries_path: Path
    markdown_path: Path
    json_path: Path
    voyage_markdown: Path
    voyage_json: Path
    logs: Dict[str, Path]
    federated: Dict[str, List[Path]]


def orchestrate_cycle(
    cycle: int,
    *,
    output_root: Path,
    puzzle_limit: int | None = None,
    federate: bool = True,
) -> OrchestratorResult:
    cycle_root = output_root / f"cycle_{cycle:05d}"
    atlas_root = cycle_root / "atlas"
    logs_root = cycle_root / "logs"
    atlas_root.mkdir(parents=True, exist_ok=True)

    puzzle_ids = _discover_puzzles(puzzle_limit)
    entries = _generate_entries(cycle, puzzle_ids)

    graph = _graph_from_entries(entries, cycle)
    graph_path = atlas_root / "global_graph.json"
    graph.save(graph_path)

    dedupe_path = atlas_root / "dedupe_index.json"
    index = build_dedupe_index(graph)
    index.save(dedupe_path)

    search_index = atlas_root / "search_index"
    _build_search_index(graph, search_index)

    amplification = _compute_amplification(cycle, entries)

    logs: Dict[str, Path] = {}
    voyage_log = logs_root / "voyage_log.jsonl"
    growth_log = logs_root / "growth_log.jsonl"
    _append_log(voyage_log, {"cycle": cycle, "amplification": amplification})
    _append_log(growth_log, {"cycle": cycle, "entries": len(entries)})
    logs["voyage"] = voyage_log
    logs["growth"] = growth_log

    entries_path = cycle_root / "entries.json"
    _write_json(entries_path, {"entries": entries})

    markdown_path = cycle_root / "federated_colossus_index.md"
    json_path = cycle_root / "federated_colossus_index.json"
    voyage_base = cycle_root / "voyage_report"

    render_colossus(
        [
            "--in",
            str(entries_path),
            "--md-out",
            str(markdown_path),
            "--json-out",
            str(json_path),
            "--voyage-report",
            str(voyage_base),
        ]
    )

    voyage_markdown = voyage_base.with_suffix(".md")
    voyage_json = voyage_base.with_suffix(".json")

    federated_paths: Dict[str, List[Path]] = {}
    if federate:
        canonical_md = Path("federated_colossus_index.md")
        canonical_json = Path("federated_colossus_index.json")
        docs_md = Path("docs/federated_colossus_index.md")
        build_json = Path("build/index/federated_colossus_index.json")
        for dest in (canonical_md, docs_md):
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(markdown_path, dest)
            federated_paths.setdefault("markdown", []).append(dest)
        for dest in (canonical_json, build_json):
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(json_path, dest)
            federated_paths.setdefault("json", []).append(dest)

    return OrchestratorResult(
        cycle=cycle,
        entries=entries,
        amplification=amplification,
        graph_path=graph_path,
        dedupe_path=dedupe_path,
        search_index=search_index,
        entries_path=entries_path,
        markdown_path=markdown_path,
        json_path=json_path,
        voyage_markdown=voyage_markdown,
        voyage_json=voyage_json,
        logs=logs,
        federated=federated_paths,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Synthesize, amplify, and federate a Colossus cycle packet."
    )
    parser.add_argument("--cycle", type=int, required=True, help="Cycle identifier")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("build/cycles"),
        help="Directory where orchestrated artifacts are written",
    )
    parser.add_argument(
        "--puzzle-limit",
        type=int,
        default=8,
        help="Maximum number of puzzles to ingest from puzzle_solutions",
    )
    parser.add_argument(
        "--no-federate",
        action="store_true",
        help="Skip copying outputs into the canonical federated index",
    )
    args = parser.parse_args(argv)

    result = orchestrate_cycle(
        args.cycle,
        output_root=args.output_root,
        puzzle_limit=args.puzzle_limit,
        federate=not args.no_federate,
    )

    print(
        "[cycle {cycle}] entries={entries} joy={joy:.2f} rage={rage:.2f}".format(
            cycle=result.cycle,
            entries=len(result.entries),
            joy=result.amplification["joy"],
            rage=result.amplification["rage"],
        )
    )
    print(f"Markdown → {result.markdown_path}")
    print(f"Dashboard JSON → {result.json_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
