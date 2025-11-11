"""Utility for aggregating satoshi puzzle proofs into a Merkle attestations document."""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Iterable, List, Sequence


def _load_proof_files(root: Path) -> List[dict]:
    proofs: List[dict] = []
    for path in sorted(root.glob("puzzle*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
            raise SystemExit(f"Failed to parse {path}: {exc}") from exc

        if not all(key in data for key in ("puzzle", "address", "message", "signature")):
            # Skip bundle metadata or alternate proof formats that do not expose the canonical quartet.
            continue

        puzzle_value = data["puzzle"]
        proofs.append(
            {
                "file": path.name,
                "puzzle": int(puzzle_value),
                "address": data["address"],
                "message": data["message"],
                "signature": data["signature"],
            }
        )
    proofs.sort(key=lambda entry: (entry["puzzle"], entry["file"]))
    return proofs


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _leaf_digest(entry: dict) -> str:
    payload = "|".join(
        [
            str(entry["puzzle"]),
            entry["address"],
            entry["message"],
            entry["signature"],
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _merkle_layer(nodes: Sequence[str]) -> List[str]:
    if not nodes:
        return []
    paired: List[str] = []
    # Duplicate the final node when the layer count is odd to retain full pairing.
    items: List[str] = list(nodes)
    if len(items) % 2 == 1:
        items.append(items[-1])
    for left, right in zip(items[0::2], items[1::2]):
        digest = hashlib.sha256(bytes.fromhex(left) + bytes.fromhex(right)).hexdigest()
        paired.append(digest)
    return paired


def _build_merkle_tree(leaves: Sequence[str]) -> List[List[str]]:
    if not leaves:
        return []
    tree: List[List[str]] = [list(leaves)]
    current = leaves
    while len(current) > 1:
        current = _merkle_layer(current)
        tree.append(current)
    return tree


def _build_attestation(root: Path) -> dict:
    proofs = _load_proof_files(root)
    leaf_hashes = [_leaf_digest(entry) for entry in proofs]
    tree = _build_merkle_tree(leaf_hashes)

    leaves_output = []
    for entry, content_hash in zip(proofs, leaf_hashes):
        leaves_output.append(
            {
                "file": entry["file"],
                "puzzle": entry["puzzle"],
                "address": entry["address"],
                "contentSha256": content_hash,
                "messageSha256": _sha256(entry["message"]),
                "signatureSha256": _sha256(entry["signature"]),
            }
        )

    merkle_root = tree[-1][0] if tree else None
    return {
        "generatedAt": _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": str(root),
        "count": len(leaves_output),
        "merkleRoot": merkle_root,
        "levels": tree,
        "leaves": leaves_output,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("satoshi/puzzle-proofs"),
        help="Directory containing canonical puzzle proof JSON documents.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("satoshi/puzzle-proofs/master_attestation.json"),
        help="Destination file for the aggregated attestation report.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Format the output with indentation for human review.",
    )
    args = parser.parse_args(argv)

    attestation = _build_attestation(args.root)
    if args.pretty:
        args.output.write_text(json.dumps(attestation, indent=2) + "\n", encoding="utf-8")
    else:
        args.output.write_text(json.dumps(attestation, separators=(",", ":")) + "\n", encoding="utf-8")

    print(f"Wrote aggregated attestation for {attestation['count']} proofs -> {args.output}")
    if attestation["merkleRoot"]:
        print(f"Merkle root: {attestation['merkleRoot']}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
