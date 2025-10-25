#!/usr/bin/env python3
"""Echo Colossus generator (stdlib-only)
Creates N synthetic Bitcoin-like entries with additional tooling:
- pseudo HASH160 (sha256(...)[:20]),
- Base58Check (version 0x00),
- standard P2PKH-looking script,
- file checksums + global verification summary,
- lineage DOT graph chaining all nodes,
- lightweight CLI queries for generated data,
- viewer index for the bundled static HTML explorer.

Usage:
  python generate_colossus.py --count 10000 --root ./echo_colossus
  python generate_colossus.py --root ./echo_colossus --query-id 42
  python generate_colossus.py --root ./echo_colossus --query-address 1abc...
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
import time
import hashlib
import pathlib
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from colossus_chronos import ChronosLattice, ChronosLatticeExplorer

# Tools module import is intentionally deferred in ``update_federated_index`` to
# avoid an eager dependency during query-only invocations.

ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(b: bytes) -> bytes:
    """Encode bytes using Base58."""
    n = int.from_bytes(b, "big")
    out = bytearray()
    while n > 0:
        n, r = divmod(n, 58)
        out.append(ALPHABET[r])

    pad = 0
    for c in b:
        if c == 0:
            pad += 1
        else:
            break
    return b"1" * pad + bytes(reversed(out or b"\x00"))


def base58check(version: int, payload: bytes) -> str:
    assert 0 <= version <= 255
    raw = bytes([version]) + payload
    chk = hashlib.sha256(hashlib.sha256(raw).digest()).digest()[:4]
    return b58encode(raw + chk).decode()


def pseudo_hash160(data: bytes) -> bytes:
    """Portable surrogate for HASH160 using stdlib only."""
    return hashlib.sha256(data).digest()[:20]


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def ensure_dirs(root: pathlib.Path) -> Dict[str, pathlib.Path]:
    paths = {
        "root": root,
        "data": root / "data" / "puzzles",
        "proofs": root / "build" / "proofs",
        "lineage": root / "build" / "lineage",
        "viewer": root / "build" / "viewer",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def write_json(path: pathlib.Path, obj: dict) -> str:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    path.write_text(s + "\n", encoding="utf-8")
    return sha256_hex(s.encode())


def generate_records(
    count: int,
    root: pathlib.Path,
    chronos: ChronosLattice | None = None,
) -> Tuple[List[Tuple[int, str]], Dict[str, str], List[dict]]:
    paths = ensure_dirs(root)
    edges: List[Tuple[int, str]] = []
    proofs: Dict[str, str] = {}
    viewer_index: List[dict] = []

    for i in range(1, count + 1):
        seed = f"PUZZLE-{i:05d}".encode()
        pubkey_like = hashlib.sha256(seed).digest()
        h160 = pseudo_hash160(pubkey_like)
        addr = base58check(0x00, h160)
        h160_hex = h160.hex()
        script = f"OP_DUP OP_HASH160 {h160_hex} OP_EQUALVERIFY OP_CHECKSIG"

        record = {
            "id": i,
            "name": f"Echo Puzzle {i:05d}",
            "hash160": h160_hex,
            "address_base58": addr,
            "script": script,
            "checksum": "",
        }

        tmp = record.copy()
        tmp.pop("checksum")
        payload = json.dumps(tmp, sort_keys=True, separators=(",", ":")).encode()
        record["checksum"] = sha256_hex(payload)

        fpath = paths["data"] / f"puzzle_{i:05d}.json"
        chronos_meta = None
        if chronos is not None:
            rel_path = str(fpath.relative_to(root))
            chronos_meta = chronos.register_artifact(
                ordinal=i,
                record_id=record["id"],
                rel_path=rel_path,
                payload_sha256=record["checksum"],
            )
            record["chronos"] = {
                "cycle": chronos_meta["cycle"],
                "ordinal": chronos_meta["ordinal"],
                "artifact_id": chronos_meta["artifact_id"],
                "time_pulse": {
                    "signature": chronos_meta["signature"],
                    "previous_signature": chronos_meta["previous_signature"],
                    "timestamp_unix_ns": chronos_meta["timestamp_unix_ns"],
                    "chain_anchor": chronos_meta["chain_anchor"],
                },
            }

        proofs[str(fpath.relative_to(root))] = write_json(fpath, record)
        edges.append((i, addr))
        viewer_entry = {
            "id": i,
            "name": record["name"],
            "hash160": record["hash160"],
            "address_base58": record["address_base58"],
            "file": str(fpath.relative_to(root)),
        }
        if chronos_meta is not None:
            viewer_entry.update(
                {
                    "chronos_cycle": chronos_meta["cycle"],
                    "chronos_signature": chronos_meta["signature"],
                    "chronos_anchor": chronos_meta["chain_anchor"],
                }
            )
        viewer_index.append(viewer_entry)

        if i % 1000 == 0:
            print(f"[+] {i} records", file=sys.stderr)

    return edges, proofs, viewer_index


def write_lineage(edges: List[Tuple[int, str]], out_dir: pathlib.Path) -> None:
    lines = ["digraph EchoLineage {", '  rankdir=LR; node [shape=point,width=0.1,label=""];']
    for i, addr in edges:
        label = addr[:6]
        lines.append(f'  n{i} [shape=circle,label="{label}"];')
    for i in range(1, len(edges)):
        lines.append(f"  n{i} -> n{i+1};")
    lines.append("}")
    (out_dir / "lineage.dot").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_verification_summary(
    proofs: Dict[str, str],
    out_dir: pathlib.Path,
    total: int,
    chronos_tail_signature: Optional[str] = None,
    chronos_cycle_index: Optional[int] = None,
) -> None:
    rollup_str = json.dumps(proofs, sort_keys=True, separators=(",", ":")).encode()
    rollup_sha = sha256_hex(rollup_str)
    summary = {
        "generated_at_unix": int(time.time()),
        "total_files": total,
        "files": proofs,
        "rollup_sha256": rollup_sha,
    }
    if chronos_tail_signature is not None:
        summary["chronos_latest_signature"] = chronos_tail_signature
    if chronos_cycle_index is not None:
        summary["chronos_cycle_index"] = chronos_cycle_index
    (out_dir / "verification_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def write_viewer_index(entries: Iterable[dict], out_dir: pathlib.Path) -> None:
    entries = list(entries)
    (out_dir / "puzzles_index.json").write_text(
        json.dumps(entries, sort_keys=False, indent=2) + "\n", encoding="utf-8"
    )


def update_federated_index(
    *,
    repo_root: pathlib.Path,
    colossus_root: pathlib.Path,
    output_path: pathlib.Path,
    artifact_type: str = "glyph-reconstruction",
    puzzle_range: Tuple[int, int] = (141, 1000),
    federation_streams: Sequence[str] = (
        "pulse",
        "anchor",
        "glyph",
        "satoshi-reconstruction",
    ),
) -> None:
    """Regenerate the federated Colossus index using the tools client."""

    try:
        from tools import colossus_index
    except Exception as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("Unable to import tools.colossus_index") from exc

    cycles = colossus_index.load_colossus_cycles(colossus_root)
    puzzle_solutions = colossus_index.collect_puzzle_solutions(
        puzzle_range[0], puzzle_range[1], root=repo_root / "puzzle_solutions"
    )
    pulse = colossus_index.load_pulse_summary(
        repo_root / "pulse.json", repo_root / "pulse_history.json"
    )
    anchor = colossus_index.load_anchor_summary(
        repo_root / "genesis_ledger" / "ledger.jsonl"
    )

    context = colossus_index.build_context(
        artifact_type=artifact_type,
        puzzle_range=puzzle_range,
        federation_sources=federation_streams,
        cycles=cycles,
        puzzle_solutions=puzzle_solutions,
        pulse=pulse,
        anchor=anchor,
    )
    content = colossus_index.build_master_index(context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def write_readme(root: pathlib.Path, count: int) -> None:
    text = f"""# Echo Colossus

Generated **{count}** synthetic Bitcoin-like records with stdlib-only Python.

## Structure
- `data/puzzles/` — {count} JSON records (id, name, hash160, Base58Check address, script, checksum)
- `build/lineage/lineage.dot` — lineage graph (use Graphviz)
- `build/proofs/verification_summary.json` — file checksums and rollup
- `build/viewer/puzzles_index.json` — lightweight index for the static viewer
- `build/chronos/` — Chronos cycle snapshots, future anchors, and lattice state

## Commands
Render lineage (requires Graphviz):

dot -Tpng build/lineage/lineage.dot -o lineage.png

Regenerate with a different size:

python generate_colossus.py --count 50000 --root ./echo_colossus

Query a record by id or address:

python generate_colossus.py --root ./echo_colossus --query-id 42
python generate_colossus.py --root ./echo_colossus --query-address 1ABC...

Chronos lattice exploration:

python generate_colossus.py --root ./echo_colossus --chronos-lineage
python generate_colossus.py --root ./echo_colossus --chronos-artifact cycle_00001#artifact_00001
python generate_colossus.py --root ./echo_colossus --reconstruct-artifact 42

Serve the viewer (from the dataset root):

python -m http.server 9000
# open http://localhost:9000/viewer/echo_colossus.html

> Note: HASH160 is simulated with `sha256(...)[:20]` for portability.
"""
    (root / "README.md").write_text(textwrap.dedent(text), encoding="utf-8")


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def query_by_id(root: pathlib.Path, puzzle_id: int) -> dict:
    target = root / "data" / "puzzles" / f"puzzle_{puzzle_id:05d}.json"
    if not target.exists():
        raise FileNotFoundError(f"Puzzle id {puzzle_id} not found at {target}")
    return load_json(target)


def query_by_address(root: pathlib.Path, address: str) -> Optional[dict]:
    index_path = root / "build" / "viewer" / "puzzles_index.json"
    if index_path.exists():
        entries = json.loads(index_path.read_text(encoding="utf-8"))
        match = next((entry for entry in entries if entry["address_base58"] == address), None)
        if match:
            return load_json(root / match["file"])

    data_dir = root / "data" / "puzzles"
    for path in data_dir.glob("puzzle_*.json"):
        record = load_json(path)
        if record.get("address_base58") == address:
            return record
    return None


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or query Echo Colossus data.")
    parser.add_argument("--count", type=int, default=10000, help="Number of records to generate")
    parser.add_argument("--root", type=str, default="./echo_colossus", help="Output root directory")
    parser.add_argument("--query-id", type=int, default=None, help="Look up a single record by id")
    parser.add_argument("--query-address", type=str, default=None, help="Look up a record by Base58 address")
    parser.add_argument(
        "--chronos-artifact",
        type=str,
        default=None,
        help="Inspect a Chronos artifact by id, record id, or signature",
    )
    parser.add_argument(
        "--chronos-cycle",
        type=int,
        default=None,
        help="Show a Chronos cycle snapshot",
    )
    parser.add_argument(
        "--chronos-lineage",
        action="store_true",
        help="List the Chronos lattice lineage",
    )
    parser.add_argument(
        "--reconstruct-artifact",
        type=str,
        default=None,
        help="Reconstruct artifact data and verify its lattice signature",
    )
    parser.add_argument(
        "--federated-index",
        type=str,
        default="federated_colossus_index.md",
        help="Destination for the federated Colossus index (relative to repo root unless absolute)",
    )
    parser.add_argument(
        "--skip-federated-index",
        action="store_true",
        help="Disable federated index regeneration after dataset creation",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    root = pathlib.Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    repo_root = pathlib.Path(__file__).resolve().parent

    if (
        args.query_id is not None
        or args.query_address is not None
        or args.chronos_artifact is not None
        or args.chronos_cycle is not None
        or args.chronos_lineage
        or args.reconstruct_artifact is not None
    ):
        try:
            if args.query_id is not None or args.query_address is not None:
                if args.query_id is not None and args.query_address is not None:
                    print("[!] Please supply either --query-id or --query-address, not both", file=sys.stderr)
                    sys.exit(1)

                if args.query_id is not None:
                    record = query_by_id(root, args.query_id)
                else:
                    record = query_by_address(root, args.query_address)  # type: ignore[arg-type]
                    if record is None:
                        print("[!] Address not found", file=sys.stderr)
                        sys.exit(1)
                print(json.dumps(record, indent=2, sort_keys=True))
                return

            explorer = ChronosLatticeExplorer(root)
            if args.chronos_lineage:
                payload = explorer.lineage()
            elif args.chronos_cycle is not None:
                payload = explorer.cycle_detail(args.chronos_cycle)
            elif args.chronos_artifact is not None:
                artifact, cycle = explorer.artifact_lookup(args.chronos_artifact)
                payload = {"artifact": artifact, "cycle": cycle}
            elif args.reconstruct_artifact is not None:
                payload = explorer.reconstruct(args.reconstruct_artifact)
            else:  # pragma: no cover - defensive guard
                payload = {}
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
        except (FileNotFoundError, KeyError) as exc:
            print(f"[!] {exc}", file=sys.stderr)
            sys.exit(1)

    print(f"[.] Generating {args.count} records into {root}", file=sys.stderr)
    chronos = ChronosLattice(root)
    chronos.start_cycle(args.count)
    edges, proofs, viewer_index = generate_records(args.count, root, chronos)
    chronos_cycle = chronos.finalize_cycle()
    chronos_tail = None
    chronos_index = None
    if isinstance(chronos_cycle, dict):
        chronos_index = chronos_cycle.get("cycle_index")
        artifacts = chronos_cycle.get("artifacts", [])
        if isinstance(artifacts, list) and artifacts:
            last = artifacts[-1]
            if isinstance(last, dict):
                chronos_tail = last.get("time_pulse_signature")
    write_lineage(edges, root / "build" / "lineage")
    write_verification_summary(
        proofs,
        root / "build" / "proofs",
        total=args.count,
        chronos_tail_signature=chronos_tail if isinstance(chronos_tail, str) else None,
        chronos_cycle_index=int(chronos_index) if isinstance(chronos_index, int) else None,
    )
    write_viewer_index(viewer_index, root / "build" / "viewer")
    write_readme(root, args.count)
    if not args.skip_federated_index:
        index_path = pathlib.Path(args.federated_index)
        if not index_path.is_absolute():
            index_path = (repo_root / index_path).resolve()
        update_federated_index(
            repo_root=repo_root,
            colossus_root=root,
            output_path=index_path,
        )
    print("[\u2713] Done")


if __name__ == "__main__":
    main()
