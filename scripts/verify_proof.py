"""Verify puzzle reconstruction proofs and the missing checklist."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from puzzle_data import build_lookup, lineage_links, load_puzzles

USAGE = """\
Echo Expansion — Proof-of-Reconstruction Verifier
=================================================
Validate JSON proofs derived from docs/puzzles/*.md and ensure the checklist
(doc/missing.md) is synchronised.

  python scripts/verify_proof.py --write
  python scripts/verify_proof.py
"""

PROOF_DIR = Path("build/proofs")
MISSING_PATH = Path("docs/missing.md")
SUMMARY_PATH = PROOF_DIR / "verification_summary.json"
DOMAIN_MAP_PATH = Path("build/domains/map.json")
TRANSCRIPTS_DIR = Path("build/repl")

ADDRESS_PATTERN = re.compile(r"[13][A-HJ-NP-Za-km-z1-9]{25,35}")
HASH160_PATTERN = re.compile(r"[0-9a-fA-F]{40}")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_domain_map(path: Path = DOMAIN_MAP_PATH) -> Dict[str, Dict[str, object]]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError:
        return {}
    domains = payload.get("domains")
    return domains if isinstance(domains, dict) else {}


def domain_edges(domain_map: Dict[str, Dict[str, object]], lookup: Dict[int, object]) -> List[Dict[str, object]]:
    edges: List[Dict[str, object]] = []
    address_to_id = {puzzle.address: puzzle.id for puzzle in lookup.values()}
    domain_to_ids: Dict[str, List[int]] = {}
    for address, payload in domain_map.items():
        puzzle_id = address_to_id.get(address)
        if not puzzle_id:
            continue
        domains = payload.get("domains") if isinstance(payload, dict) else None
        if not isinstance(domains, list):
            continue
        for domain in domains:
            domain_to_ids.setdefault(domain, []).append(puzzle_id)
    for domain, ids in domain_to_ids.items():
        unique_ids = sorted(set(ids))
        for i, source in enumerate(unique_ids):
            for target in unique_ids[i + 1 :]:
                edges.append({"source": source, "target": target, "domain": domain, "kind": "domain"})
    return edges


def extract_metadata(text: str) -> Tuple[List[str], List[str]]:
    addresses = sorted({match for match in ADDRESS_PATTERN.findall(text)})
    hashes = sorted({match.lower() for match in HASH160_PATTERN.findall(text)})
    return addresses, hashes


def generate_proof(doc: Path, puzzle_lookup: Dict[int, object], edges: List[Dict[str, object]], domain_map: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    content = doc.read_text(encoding="utf-8")
    addresses, hashes = extract_metadata(content)
    try:
        puzzle_id = int(doc.stem.split("-")[-1])
    except ValueError:
        puzzle_id = None
    puzzle = puzzle_lookup.get(puzzle_id) if puzzle_id else None
    if puzzle:
        addresses = sorted(set(addresses + [puzzle.address]))
        hashes = sorted(set(hashes + [puzzle.hash160]))
    lineage = [edge for edge in edges if puzzle_id and (edge.get("source") == puzzle_id or edge.get("target") == puzzle_id)]
    domains = domain_map.get(puzzle.address) if puzzle else None
    return {
        "puzzle_id": puzzle_id,
        "doc": str(doc),
        "sha256": sha256(content),
        "addresses": addresses,
        "hash160": hashes,
        "script_type": puzzle.script_type if puzzle else None,
        "status": puzzle.status if puzzle else None,
        "lineage": lineage,
        "domains": domains or {},
        "generated": datetime.now(timezone.utc).isoformat(),
    }


def write_proof(path: Path, payload: Dict[str, object]) -> None:
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def read_existing(path: Path) -> Optional[Dict[str, object]]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def compute_missing(puzzles: List[object], proofs: Dict[int, Path], edges: List[Dict[str, object]], domain_map: Dict[str, Dict[str, object]], transcripts_dir: Path = TRANSCRIPTS_DIR) -> Dict[str, List[str]]:
    lineage_ids = {edge["source"] for edge in edges} | {edge["target"] for edge in edges}
    domain_missing: List[str] = []
    lineage_missing: List[str] = []
    proof_missing: List[str] = []
    transcript_missing: List[str] = []

    for puzzle in puzzles:
        pid = puzzle.id
        proof_path = proofs.get(pid)
        if proof_path is None or not proof_path.exists():
            proof_missing.append(f"Puzzle {pid}")
        if pid not in lineage_ids:
            lineage_missing.append(f"Puzzle {pid}")
        domain_info = domain_map.get(puzzle.address, {})
        domains = domain_info.get("domains") if isinstance(domain_info, dict) else None
        if not domains:
            domain_missing.append(f"Puzzle {pid}")
        transcript_path = transcripts_dir / f"puzzle_{pid}.json"
        if not transcript_path.exists():
            transcript_missing.append(f"Puzzle {pid}")
    return {
        "proofs": proof_missing,
        "lineage": lineage_missing,
        "domains": domain_missing,
        "transcripts": transcript_missing,
    }


def format_checklist(missing: Dict[str, List[str]]) -> str:
    lines = ["# Missing Puzzle Checklist", ""]
    for section, items in missing.items():
        title = section.capitalize()
        lines.append(f"## {title}")
        if not items:
            lines.append("- [x] Complete")
        else:
            for item in sorted(items):
                lines.append(f"- [ ] {item}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify proof artifacts and missing checklist.")
    parser.add_argument("--write", action="store_true", help="Rewrite proof JSON and docs/missing.md.")
    args = parser.parse_args()

    print(USAGE)

    puzzles = load_puzzles()
    lookup = build_lookup(puzzles)
    docs_dir = Path("docs/puzzles")
    doc_paths = sorted(docs_dir.glob("puzzle-*.md"))
    domain_map = load_domain_map()
    edges = lineage_links() + domain_edges(domain_map, lookup)

    proofs_index: Dict[int, Path] = {}
    mismatches: List[str] = []

    for doc in doc_paths:
        proof = generate_proof(doc, lookup, edges, domain_map)
        puzzle_id = proof["puzzle_id"]
        proof_path = PROOF_DIR / f"puzzle-{puzzle_id}.proof.json"
        proofs_index[puzzle_id] = proof_path
        existing = read_existing(proof_path)
        if args.write or existing is None:
            write_proof(proof_path, proof)
            print(f"[proof] updated {proof_path}")
        else:
            if existing != {**proof, "generated": existing.get("generated")}:  # ignore timestamp diff
                mismatches.append(str(proof_path))

    missing = compute_missing([p for p in puzzles if p.doc.startswith("docs/puzzles/")], proofs_index, edges, domain_map)
    checklist_body = format_checklist(missing)
    if args.write or not MISSING_PATH.exists():
        MISSING_PATH.write_text(checklist_body, encoding="utf-8")
        print(f"[missing] updated {MISSING_PATH}")
    else:
        current = MISSING_PATH.read_text(encoding="utf-8")
        if current != checklist_body:
            mismatches.append(str(MISSING_PATH))

    summary = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "checked_docs": [str(path) for path in doc_paths],
        "mismatches": mismatches,
        "missing_counts": {key: len(value) for key, value in missing.items()},
    }
    ensure_directory(SUMMARY_PATH.parent)
    with SUMMARY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    print(f"[summary] verification summary written to {SUMMARY_PATH}")

    if mismatches and not args.write:
        print("[verify] mismatches detected:")
        for item in mismatches:
            print(f"  - {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
