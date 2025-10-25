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


def search(index_path: Path, query: str, limit: int = 10) -> List[dict]:
    entries = _load_index(index_path)
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
    args = parser.parse_args(argv)

    results = search(args.index, args.query, args.limit)
    if not results:
        print("No results found.")
        return 1

    for rank, entry in enumerate(results, start=1):
        print(f"{rank}. [{entry['score']}] {entry['node_id']} ({entry['universe']}) -> {entry['artifact_id']}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
