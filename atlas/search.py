"""Federated search over the Atlas global graph."""

from __future__ import annotations

from pathlib import Path
from typing import List
import argparse
import json


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
        if not isinstance(entry_address, str) or entry_address.lower() != address.lower():
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query the federated search index")
    parser.add_argument("--query", required=True, help="Query string")
    parser.add_argument("--index", type=Path, required=True, help="Path to search index directory or file")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--cycle", type=int, help="Filter results to a specific Harmonix cycle")
    parser.add_argument("--puzzle", type=int, help="Filter results to a specific Harmonix puzzle id")
    parser.add_argument("--address", help="Filter results to a specific Harmonix address")
    args = parser.parse_args(argv)

    results = search(
        args.index,
        args.query,
        args.limit,
        cycle=args.cycle,
        puzzle=args.puzzle,
        address=args.address,
    )
    if not results:
        print("No results found.")
        return 1

    for rank, entry in enumerate(results, start=1):
        harmonix_bits = []
        if entry.get("cycle") is not None:
            harmonix_bits.append(f"cycle={entry['cycle']}")
        if entry.get("puzzle_id") is not None:
            harmonix_bits.append(f"puzzle={entry['puzzle_id']}")
        if entry.get("address"):
            harmonix_bits.append(f"address={entry['address']}")
        suffix = f" [{' '.join(harmonix_bits)}]" if harmonix_bits else ""
        print(
            f"{rank}. [{entry['score']}] {entry['node_id']} ({entry['universe']}) -> {entry['artifact_id']}{suffix}"
        )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
