"""Aggregate verification results for the puzzle proof catalogue."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from verifier.verify_puzzle_signature import iter_signature_segments, verify_segments

DEFAULT_PATTERNS = ("puzzle*.json",)


@dataclass
class ProofResult:
    """Verification outcome for a single proof file."""

    path: Path
    puzzle: int | None
    address: str | None
    target_kind: str
    segments: int
    valid_segments: int
    fully_verified: bool

    @property
    def label(self) -> str:
        return self.path.name

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "path": str(self.path),
            "label": self.label,
            "segments": self.segments,
            "valid_segments": self.valid_segments,
            "fully_verified": self.fully_verified,
            "target_kind": self.target_kind,
        }
        if self.puzzle is not None:
            payload["puzzle"] = self.puzzle
        if self.address is not None:
            payload["address"] = self.address
        return payload


@dataclass
class SkippedProof:
    """Details for a proof that could not be verified automatically."""

    path: Path
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"path": str(self.path), "reason": self.reason}


def _iter_proof_files(root: Path, patterns: Sequence[str]) -> Iterable[Path]:
    if not root.is_dir():
        raise FileNotFoundError(f"Proof directory does not exist: {root}")

    seen: set[str] = set()
    for path in sorted(root.rglob("*.json")):
        rel_name = path.name
        if patterns and not any(fnmatch(rel_name, pattern) for pattern in patterns):
            continue
        if rel_name in seen and path.is_file():
            # Multiple matches with identical filenames may exist in nested
            # folders. Keep the first encounter to avoid double counting.
            continue
        seen.add(rel_name)
        yield path


def _signature_looks_bitcoin(signature: str) -> bool:
    segments = list(iter_signature_segments(signature))
    if not segments:
        return False
    try:
        return all(len(base64.b64decode(segment)) == 65 for segment in segments)
    except (binascii.Error, ValueError):
        return False


def _load_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc


def evaluate_proof(path: Path) -> ProofResult | SkippedProof:
    try:
        payload = _load_json(path)
    except ValueError as exc:
        return SkippedProof(path, str(exc))

    message = payload.get("message")
    signature = payload.get("signature") or payload.get("combinedSignature")
    address = payload.get("address")
    pk_script = payload.get("pkScript") or payload.get("pkscript")

    if not isinstance(message, str) or not message.strip():
        return SkippedProof(path, "missing message")
    if not isinstance(signature, str) or not signature.strip():
        return SkippedProof(path, "missing signature")

    target_kind: str
    verification_address: str | None = None
    verification_script: str | None = None

    if isinstance(address, str) and address.strip():
        verification_address = address.strip()
        target_kind = "address"
    elif isinstance(pk_script, str) and pk_script.strip():
        verification_script = pk_script.strip()
        target_kind = "pkscript"
    else:
        return SkippedProof(path, "no address or pkScript target declared")

    if not _signature_looks_bitcoin(signature):
        return SkippedProof(path, "signature is not a recoverable Bitcoin message signature")

    try:
        results = verify_segments(verification_address, message, signature, verification_script)
    except Exception as exc:  # pragma: no cover - defensive guard
        return SkippedProof(path, f"verification error: {exc}")

    valid_segments = sum(1 for entry in results if entry.valid)
    proof = ProofResult(
        path=path,
        puzzle=payload.get("puzzle") if isinstance(payload.get("puzzle"), int) else None,
        address=verification_address,
        target_kind=target_kind,
        segments=len(results),
        valid_segments=valid_segments,
        fully_verified=valid_segments == len(results) and len(results) > 0,
    )
    return proof


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate verification results for the bundled Satoshi proofs."
    )
    parser.add_argument(
        "--root",
        default=Path(__file__).with_name("puzzle-proofs"),
        type=Path,
        help="Directory containing the JSON proof catalogue",
    )
    parser.add_argument(
        "--glob",
        action="append",
        dest="patterns",
        help="Filename glob(s) to evaluate. Defaults to 'puzzle*.json'",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to persist the JSON report",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON summary",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    patterns = tuple(args.patterns) if args.patterns else DEFAULT_PATTERNS

    proof_files = list(_iter_proof_files(args.root, patterns))
    results: list[ProofResult] = []
    skipped: list[SkippedProof] = []

    for path in proof_files:
        outcome = evaluate_proof(path)
        if isinstance(outcome, ProofResult):
            results.append(outcome)
        else:
            skipped.append(outcome)

    summary = {
        "root": str(args.root),
        "file_total": len(proof_files),
        "verified_proofs": len(results),
        "fully_verified": sum(1 for result in results if result.fully_verified),
        "segments_checked": sum(result.segments for result in results),
        "valid_segments": sum(result.valid_segments for result in results),
        "skipped": [entry.to_dict() for entry in skipped],
        "entries": [result.to_dict() for result in results],
    }

    json_kwargs = {"ensure_ascii": False}
    if args.pretty:
        json_kwargs["indent"] = 2

    output_payload = json.dumps(summary, **json_kwargs)

    if args.output:
        args.output.write_text(output_payload, encoding="utf-8")
    else:
        print(output_payload)

    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
