"""Chrono Engine and Chrono Visor helpers.

This module wraps the Chronos lattice utilities with a higher level API that
makes it straightforward to initialise cycles, ingest records, and surface
human-friendly timeline summaries.  It intentionally depends only on the
stdlib and ``colossus_chronos`` so it can run in the same minimal
environments as the existing generator and viewer scripts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Sequence

from colossus_chronos import ChronosLattice, ChronosLatticeExplorer


def _hash_file(path: pathlib.Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@dataclass
class ChronoRecord:
    """Description of a record that should be tracked by Chronos."""

    rel_path: str
    payload_sha256: str
    record_id: int

    def to_dict(self) -> dict:
        return {
            "rel_path": self.rel_path,
            "payload_sha256": self.payload_sha256,
            "record_id": self.record_id,
        }

    @staticmethod
    def _default_record_id(rel_path: str) -> int:
        digest = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()
        return int(digest[:12], 16)

    @classmethod
    def from_file(
        cls,
        root: pathlib.Path,
        rel_path: str,
        *,
        record_id: int | None = None,
    ) -> "ChronoRecord":
        root = root.resolve()
        path = (root / rel_path).resolve()
        try:
            rel_from_root = str(path.relative_to(root))
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError("record must be located inside the Chrono root") from exc
        if not path.exists():
            raise FileNotFoundError(f"record file {rel_from_root} does not exist")
        payload_sha = _hash_file(path)
        resolved_record_id = record_id if record_id is not None else cls._default_record_id(rel_from_root)
        return cls(rel_from_root, payload_sha, resolved_record_id)


class ChronoEngine:
    """High level wrapper around :class:`ChronosLattice`."""

    def __init__(self, root: pathlib.Path):
        self.root = root
        self.lattice = ChronosLattice(root)

    def discover_records(
        self,
        pattern: str,
        *,
        start_record_id: int | None = None,
    ) -> List[ChronoRecord]:
        """Return ``ChronoRecord`` entries for files matching ``pattern``."""

        start = start_record_id
        records: List[ChronoRecord] = []
        for index, path in enumerate(sorted(self.root.glob(pattern)), start=0):
            rel_path = str(path.relative_to(self.root))
            record_id = (start + index) if start is not None else None
            records.append(ChronoRecord.from_file(self.root, rel_path, record_id=record_id))
        return records

    def build_cycle(
        self,
        records: Sequence[ChronoRecord],
        *,
        persist_manifest: bool = True,
    ) -> dict:
        if not records:
            raise ValueError("no records supplied to Chrono Engine")

        cycle = self.lattice.start_cycle(len(records))
        for ordinal, record in enumerate(records, start=1):
            self.lattice.register_artifact(
                ordinal=ordinal,
                record_id=record.record_id,
                rel_path=record.rel_path,
                payload_sha256=record.payload_sha256,
            )
        finalized = self.lattice.finalize_cycle()

        if persist_manifest:
            manifest_path = (
                self.lattice.lattice_dir
                / f"cycle_{finalized['cycle_index']:05d}_records.json"
            )
            manifest_path.write_text(
                json.dumps([record.to_dict() for record in records], indent=2) + "\n",
                encoding="utf-8",
            )
        return finalized


class ChronoVisor:
    """User-friendly views on top of the Chronos explorer."""

    def __init__(self, root: pathlib.Path):
        self.explorer = ChronosLatticeExplorer(root)

    def timeline(self, *, reverse: bool = False) -> List[dict]:
        lineage = self.explorer.lineage()
        return list(reversed(lineage)) if reverse else lineage

    def describe_cycles(self) -> List[dict]:
        return self.explorer.cycle_summaries()

    def render_timeline(self, *, reverse: bool = False) -> str:
        lineage = self.timeline(reverse=reverse)
        if not lineage:
            return "Chrono visor: no artifacts recorded."

        direction_note = " (newest → oldest)" if reverse else ""
        lines = [f"Chrono visor timeline{direction_note}"]
        for entry in lineage:
            ts_ns = int(entry.get("timestamp_unix_ns", 0))
            iso = datetime.fromtimestamp(ts_ns / 1_000_000_000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
            signature = str(entry.get("signature"))
            lines.append(
                "• cycle {cycle:05d} · ordinal {ordinal:05d} · {artifact} · sig {sig} · {timestamp}".format(
                    cycle=int(entry.get("cycle", 0)),
                    ordinal=int(entry.get("ordinal", 0)),
                    artifact=entry.get("artifact_id", "?"),
                    sig=(signature[:12] + "…") if signature else "n/a",
                    timestamp=iso,
                )
            )
        return "\n".join(lines)

    def render_cycle_table(self) -> str:
        summaries = self.describe_cycles()
        if not summaries:
            return "Chrono visor: no cycles recorded."

        header = f"{'Cycle':>5} | {'Artifacts':>9} | {'Started':>19} | {'Completed':>19} | {'Anchors':>7}"
        lines = [header, "-" * len(header)]
        for summary in summaries:
            lines.append(
                f"{summary.get('cycle_index', 0):5d} | "
                f"{summary.get('artifact_total', 0):9d} | "
                f"{summary.get('started_at_unix', 0):19d} | "
                f"{summary.get('completed_at_unix', 0):19d} | "
                f"{summary.get('future_anchor_count', 0):7d}"
            )
        return "\n".join(lines)

    def inspect_artifact(self, key: str) -> dict:
        return self.explorer.reconstruct(key)


def _cmd_engine(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    engine = ChronoEngine(root)
    records: List[ChronoRecord] = []
    if args.pattern:
        records.extend(engine.discover_records(args.pattern, start_record_id=args.record_base))

    base_offset = args.record_base + len(records)
    for index, rel in enumerate(args.records, start=0):
        record_id = base_offset + index
        records.append(ChronoRecord.from_file(root, rel, record_id=record_id))

    if not records:
        raise SystemExit("no records supplied; provide --pattern or --records")

    cycle = engine.build_cycle(records)
    print(json.dumps(cycle, indent=2))


def _cmd_visor(args: argparse.Namespace) -> None:
    visor = ChronoVisor(args.root.resolve())
    output: List[str] = []
    if args.timeline or (not args.timeline and not args.cycles and args.artifact is None):
        output.append(visor.render_timeline(reverse=args.reverse))
    if args.cycles or (not args.timeline and not args.cycles and args.artifact is None):
        output.append(visor.render_cycle_table())
    if args.artifact is not None:
        inspection = visor.inspect_artifact(args.artifact)
        output.append(json.dumps(inspection["verification"], indent=2))
    print("\n\n".join(output))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chrono Engine / Chrono Visor toolkit")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."), help="Project root that contains build/chronos")
    subparsers = parser.add_subparsers(dest="command", required=True)

    engine_parser = subparsers.add_parser("engine", help="Initialise a Chronos cycle from record files")
    engine_parser.add_argument("--pattern", help="Glob pattern (relative to root) used to auto-discover records")
    engine_parser.add_argument("--records", nargs="*", default=[], help="Explicit record paths relative to root")
    engine_parser.add_argument("--record-base", type=int, default=1, help="Starting record identifier")
    engine_parser.set_defaults(func=_cmd_engine)

    visor_parser = subparsers.add_parser("visor", help="Render Chronos summaries")
    visor_parser.add_argument("--timeline", action="store_true", help="Print the Chrono visor timeline")
    visor_parser.add_argument(
        "--reverse",
        action="store_true",
        help="Render the timeline backwards (newest first)",
    )
    visor_parser.add_argument("--cycles", action="store_true", help="Print the Chrono visor cycle table")
    visor_parser.add_argument("--artifact", help="Inspect a specific artifact by id, record id, or signature")
    visor_parser.set_defaults(func=_cmd_visor)

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
