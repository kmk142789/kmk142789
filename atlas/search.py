"""Federated search utilities and structured filtering helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse
import json
import shlex

# Structured data surfaced for downstream renderers.
presence_harmonics: List[Dict[str, Any]] = [
    dict(
        cycle=1,
        expansion="Lumen Spiral",
        thread="presence",
        resonance=0.93,
        harmonics=["listen", "echo", "uplift"],
        notes="Bridge glyphs amplify direct community presence across mirrors.",
    ),
    dict(
        cycle=2,
        expansion="Prism Bloom",
        thread="relay",
        resonance=0.92,
        harmonics=["bridge", "pulse", "spiral"],
        notes="Relay harmonics stabilize cross-orbit routing for live collaborations.",
    ),
    dict(
        cycle=3,
        expansion="Aurora Mesh",
        thread="signal",
        resonance=0.9,
        harmonics=["tune", "phase", "amplify"],
        notes="Signal caretakers maintain balanced throughput during surge windows.",
    ),
]

safety_notices: List[Dict[str, Any]] = [
    dict(
        id="non_custodial_artifacts",
        title="Artifacts remain non-custodial",
        severity="info",
        summary="Federated index entries link to public data only; no keys or credentials are stored.",
        guidance="Verify hashes before distributing artifacts to downstream mirrors.",
        flags=["non_custodial", "checksum_required"],
        flagged=False,
    ),
    dict(
        id="attestation_only_signing",
        title="Attestation-only signing flow",
        severity="warning",
        summary="Signing infrastructure operates in attest-only mode; financial transactions are blocked by policy.",
        guidance="Escalate to governance if a transaction request is observed in the queue.",
        flags=["attestation_only", "manual_review"],
        flagged=True,
    ),
    dict(
        id="supply_chain_integrity",
        title="Supply chain integrity checks",
        severity="info",
        summary="Dependency locks are monitored; unexpected hashes require investigation before deployment.",
        guidance="Run the integrity verifier prior to federation pushes.",
        flags=["integrity_monitor"],
        flagged=False,
    ),
]

from .dedupe import dedupe_latest, normalize_address
from .types import Entry


def _load_index(path: Path) -> List[dict]:
    if path.is_dir():
        path = path / "index.json"
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return list(payload.get("entries", []))


def _score_entry(entry: dict, query_terms: List[str]) -> int:
    haystack = entry.get("text", "").lower()
    score = 0
    for term in query_terms:
        if term in haystack:
            score += haystack.count(term)
    return score


def _matches_filters(entry: dict, *, cycle: int | None, puzzle: int | None, address: str | None) -> bool:
    if cycle is not None:
        entry_cycle = entry.get("cycle")
        try:
            if int(entry_cycle) != cycle:
                return False
        except (TypeError, ValueError):
            return False
    if puzzle is not None:
        entry_puzzle = entry.get("puzzle_id")
        try:
            if int(entry_puzzle) != puzzle:
                return False
        except (TypeError, ValueError):
            return False
    if address is not None:
        entry_address = entry.get("address")
        if not isinstance(entry_address, str) or normalize_address(entry_address) != normalize_address(address):
            return False
    return True


def search(
    index_path: Path,
    query: str,
    limit: int = 10,
    *,
    cycle: int | None = None,
    puzzle: int | None = None,
    address: str | None = None,
) -> List[dict]:
    entries = [
        entry
        for entry in _load_index(index_path)
        if _matches_filters(entry, cycle=cycle, puzzle=puzzle, address=address)
    ]
    query_terms = [term.lower() for term in query.split() if term.strip()]
    if not query_terms:
        return []
    ranked = [
        (entry, _score_entry(entry, query_terms))
        for entry in entries
    ]
    ranked = [item for item in ranked if item[1] > 0]
    ranked.sort(key=lambda pair: pair[1], reverse=True)
    return [item[0] | {"score": item[1]} for item in ranked[:limit]]


def filter_entries(
    entries: List[Entry],
    cycle: Optional[int] = None,
    puzzle_id: Optional[int] = None,
    address: Optional[str] = None,
) -> List[Entry]:
    """Filter raw entries by harmonix metadata fields."""

    if address:
        address = normalize_address(address)
    filtered: List[Entry] = []
    for entry in entries:
        if cycle is not None and int(entry["cycle"]) != int(cycle):
            continue
        if puzzle_id is not None and int(entry["puzzle_id"]) != int(puzzle_id):
            continue
        if address is not None and normalize_address(entry.get("address", "")) != address:
            continue
        filtered.append(entry)
    return filtered


# Grammar: key:value pairs separated by space. Supported keys: cycle, puzzle, addr
# Examples: "cycle:12", "puzzle:131 addr:1A1zP1...", "cycle:7 puzzle:125"
def parse_structured(query: str) -> Dict[str, Any]:
    cycle = puzzle = addr = None
    for token in shlex.split(query or ""):
        if ":" not in token:
            continue
        key, value = token.split(":", 1)
        key = key.lower().strip()
        value = value.strip()
        if key in ("cycle", "c"):
            cycle = int(value)
        elif key in ("puzzle", "p", "puzzle_id"):
            puzzle = int(value)
        elif key in ("addr", "address", "a"):
            addr = value
    return dict(cycle=cycle, puzzle_id=puzzle, address=addr)


def _read(path: str) -> List[Entry]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data["entries"] if isinstance(data, dict) and "entries" in data else data


def _write(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Federated Colossus search with structured filters."
    )
    parser.add_argument("--in", dest="inputs", nargs="+", required=True, help="Input JSON files")
    parser.add_argument("--out", help="Optional filtered JSON output path")
    parser.add_argument("--cycle", type=int)
    parser.add_argument("--puzzle", type=int, dest="puzzle_id")
    parser.add_argument("--addr", dest="address")
    parser.add_argument("--q", dest="query", help='Structured query, e.g. "cycle:12 puzzle:125"')
    parser.add_argument(
        "--dedupe-latest",
        action="store_true",
        help="Keep only latest entry per (puzzle,address)",
    )
    args = parser.parse_args(argv)

    entries: List[Entry] = []
    for path in args.inputs:
        entries.extend(_read(path))

    if args.dedupe_latest:
        entries = dedupe_latest(entries)

    query_bits = parse_structured(args.query or "")
    cycle = args.cycle if args.cycle is not None else query_bits["cycle"]
    puzzle_id = args.puzzle_id if args.puzzle_id is not None else query_bits["puzzle_id"]
    address = args.address if args.address is not None else query_bits["address"]

    filtered = filter_entries(entries, cycle=cycle, puzzle_id=puzzle_id, address=address)

    payload = {"entries": filtered}
    if args.out:
        _write(args.out, payload)
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
