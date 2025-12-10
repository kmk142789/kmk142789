"""Puzzle solution authorship registry with immutable digests.

This module scans puzzle solution artifacts, computes immutable
hash-linked authorship records, and emits both JSONL ledger lines and
canonical proof bundles. The registry is designed to be run repeatedly;
it automatically skips solutions that are already recorded so new
artifacts can be appended continuously without duplication.

Typical usage::

    python -m ledger.puzzle_authorship_registry --solution-dir puzzle_solutions \
        --author "Echo Puzzle Council" --narrative "Backfill solutions"

Each entry captures:

* sha256 digests for the solution artifact and optional attestation file.
* An authorship label and free-form narrative for context.
* A canonical digest that can be mirrored into other ledgers.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger(__name__)


def _iso_now() -> str:
    return (
        datetime.now(tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha256_hex(payload: bytes) -> str:
    import hashlib

    return hashlib.sha256(payload).hexdigest()


def _canonical_dumps(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


@dataclass(slots=True)
class PuzzleAuthorship:
    """Immutable authorship record for a single puzzle solution."""

    seq: int
    puzzle_id: str
    solution_path: str
    solution_digest: str
    author: str
    timestamp: str
    narrative: str
    attestation_path: Optional[str] = None
    attestation_digest: Optional[str] = None
    ledger_reference: Optional[str] = None

    def payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "seq": self.seq,
            "puzzle_id": self.puzzle_id,
            "solution_path": self.solution_path,
            "solution_digest": self.solution_digest,
            "author": self.author,
            "timestamp": self.timestamp,
            "narrative": self.narrative,
        }
        if self.attestation_path:
            payload["attestation_path"] = self.attestation_path
        if self.attestation_digest:
            payload["attestation_digest"] = self.attestation_digest
        if self.ledger_reference:
            payload["ledger_reference"] = self.ledger_reference
        return payload

    def digest(self) -> str:
        return "sha256:" + _sha256_hex(_canonical_dumps(self.payload()).encode("utf-8"))


class PuzzleAuthorshipRegistry:
    """Append-only registry for puzzle solution authorship."""

    def __init__(self, *, ledger_path: Path, proofs_dir: Path) -> None:
        self.ledger_path = ledger_path
        self.proofs_dir = proofs_dir
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.proofs_dir.mkdir(parents=True, exist_ok=True)
        self._seq = self._load_last_sequence()
        self._seen_digests, self._seen_paths = self._load_existing_solutions()

    def _load_last_sequence(self) -> int:
        if not self.ledger_path.exists():
            return -1
        last_seq = -1
        with self.ledger_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    last_seq = max(last_seq, int(payload.get("seq", -1)))
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed registry line: %s", line)
        return last_seq

    def _load_existing_solutions(self) -> tuple[set[str], set[str]]:
        if not self.ledger_path.exists():
            return set(), set()
        digests: set[str] = set()
        paths: set[str] = set()
        with self.ledger_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                digest = payload.get("solution_digest")
                path = payload.get("solution_path")
                if digest:
                    digests.add(digest)
                if path:
                    paths.add(path)
        return digests, paths

    def register_solution(
        self,
        *,
        solution_path: Path,
        attestation_path: Optional[Path],
        author: str,
        narrative: str,
        ledger_reference: Optional[str] = None,
    ) -> Optional[PuzzleAuthorship]:
        normalized_path = str(solution_path)
        if normalized_path in self._seen_paths:
            logger.info("Skipping %s (already recorded by path)", solution_path)
            return None

        solution_bytes = solution_path.read_bytes()
        solution_digest = _sha256_hex(solution_bytes)
        if solution_digest in self._seen_digests:
            logger.info("Skipping %s (digest already recorded)", solution_path)
            return None

        attestation_digest: Optional[str] = None
        attestation_field: Optional[str] = None
        if attestation_path is not None:
            attestation_field = str(attestation_path)
            attestation_digest = _sha256_hex(attestation_path.read_bytes())

        self._seq += 1
        record = PuzzleAuthorship(
            seq=self._seq,
            puzzle_id=_puzzle_id_from_path(solution_path),
            solution_path=normalized_path,
            solution_digest=solution_digest,
            attestation_path=attestation_field,
            attestation_digest=attestation_digest,
            author=author,
            timestamp=_iso_now(),
            narrative=narrative,
            ledger_reference=ledger_reference,
        )

        digest = record.digest()
        proof_path = self.proofs_dir / f"entry_{record.seq:05d}.json"
        proof_payload = record.payload() | {"digest": digest}
        proof_path.write_text(json.dumps(proof_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        self._append_ledger_line(proof_payload)
        self._seen_digests.add(solution_digest)
        self._seen_paths.add(normalized_path)
        logger.info("Recorded puzzle solution %s (digest %s)", solution_path, digest)
        return record

    def _append_ledger_line(self, payload: Dict[str, Any]) -> None:
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical_dumps(payload) + "\n")


def _puzzle_id_from_path(path: Path) -> str:
    stem = path.stem
    return stem if stem.startswith("puzzle") else f"puzzle:{stem}"


def _default_author() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            check=True,
            capture_output=True,
            text=True,
        )
        candidate = result.stdout.strip()
        if candidate:
            return candidate
    except Exception:
        return "Unknown author"
    return "Unknown author"


def _collect_paths(directory: Path) -> list[Path]:
    return sorted(p for p in directory.glob("*.md") if p.is_file())


def cli(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Register puzzle solution authorship records")
    parser.add_argument("--solution", action="append", type=Path, help="Path to puzzle solution artifact")
    parser.add_argument("--attestation", action="append", type=Path, help="Optional attestation file matching --solution entries")
    parser.add_argument("--solution-dir", type=Path, help="Scan a directory for *.md solutions to record")
    parser.add_argument("--author", default=_default_author(), help="Authorship label to store in the ledger")
    parser.add_argument(
        "--narrative",
        default="Puzzle solution authorship record",
        help="Narrative describing the purpose of the record",
    )
    parser.add_argument(
        "--ledger-reference",
        help="Optional digest or URL of an upstream ledger entry to anchor",
    )
    parser.add_argument(
        "--ledger-path",
        type=Path,
        default=Path("ledger/puzzle_authorship_registry.jsonl"),
        help="Destination JSONL ledger for authorship records",
    )
    parser.add_argument(
        "--proofs-dir",
        type=Path,
        default=Path("proofs/puzzle_authorship"),
        help="Directory for proof bundle JSON artifacts",
    )
    parser.add_argument("--log-level", default="INFO", help="Python logging level")
    args = parser.parse_args(list(argv) if argv is not None else None)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.solution_dir is None and not args.solution:
        parser.error("Provide --solution or --solution-dir")

    solutions: list[Path] = []
    attestations: list[Optional[Path]] = []

    if args.solution_dir is not None:
        if not args.solution_dir.exists():
            parser.error(f"Solution directory does not exist: {args.solution_dir}")
        solutions.extend(_collect_paths(args.solution_dir))
        attestations.extend([None] * len(solutions))

    if args.solution:
        solutions.extend(args.solution)
        if args.attestation and len(args.attestation) not in {0, len(args.solution)}:
            parser.error("When using --attestation multiple times, supply one entry per --solution")
        attestation_iter = args.attestation or []
        attestations.extend(attestation_iter + [None] * (len(args.solution) - len(attestation_iter)))

    registry = PuzzleAuthorshipRegistry(ledger_path=args.ledger_path, proofs_dir=args.proofs_dir)

    for solution_path, attestation_path in zip(solutions, attestations):
        if not solution_path.exists():
            logger.warning("Skipping missing solution: %s", solution_path)
            continue
        registry.register_solution(
            solution_path=solution_path,
            attestation_path=attestation_path,
            author=args.author,
            narrative=args.narrative,
            ledger_reference=args.ledger_reference,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
