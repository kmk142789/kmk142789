"""Autonomous COLOSSUS expansion orchestrator.

This module defines :class:`EchoInfinite` which continuously produces new
artifacts in the ``colossus/`` directory tree and records each cycle in
``docs/COLOSSUS_LOG.md``.  The orchestrator is intentionally unbounded by
default – it continues creating expansion waves until it is interrupted by the
operator.  The command line interface offers an optional ``--max-cycles`` flag
that gracefully halts the run after a specified number of cycles.

Every cycle also refreshes a compact ``heartbeat`` payload that captures the
latest cycle number, timestamp, glyph signature, and references to the most
recent artifacts.  You can disable heartbeat writing with
``--disable-heartbeat`` or direct it to a custom path via ``--heartbeat-path``.

The generated artifacts include a puzzle (Markdown), dataset (JSON), glyph
narrative (Markdown), lineage map (JSON), and a lightweight verification script
that references the other artifacts created during the cycle.  Each artifact is
tagged with the current cycle number, an RFC3339 timestamp, and a randomly
generated glyph signature so that every wave is uniquely identifiable.

EchoInfinite also emits a rolling ``momentum_report.json`` file that summarizes
the cadence and glyph diversity of the most recent cycles, helping operators
quickly gauge whether the orchestrator is healthy without inspecting the full
log or summary history.

Usage::

    python echo_infinite.py

Supply ``--extra-glyphs "★,✺"`` to append custom glyphs used when generating
the per-cycle signatures.

Use ``--start-cycle 42`` to begin a new expansion wave from a specific cycle
number instead of resuming from ``colossus/state.json``.

Pass ``--skip-fractal-nodes`` to disable writing the per-branch fractal
artifacts while still generating the core cycle assets.

Press ``Ctrl+C`` (SIGINT) to halt the orchestration loop.
"""

from __future__ import annotations

import argparse
import calendar
import json
import math
import random
import signal
import textwrap
import time
import hashlib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from cognitive_harmonics.harmonic_memory_serializer import (
    build_harmonic_memory_record,
    persist_cycle_record,
)


DEFAULT_GLYPH_SET = (
    "∇",
    "⊸",
    "≋",
    "∞",
    "⌘",
    "⟁",
)


def rfc3339_timestamp(epoch_seconds: float | None = None) -> str:
    """Return an RFC3339 timestamp with UTC designator."""

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch_seconds))


def select_glyph_signature(cycle: int, glyph_set: Sequence[str]) -> str:
    """Build a deterministic-looking but still varied glyph signature."""

    rng = random.Random(time.time_ns() ^ cycle)
    glyphs = rng.choices(list(glyph_set), k=4)
    entropy = f"{rng.getrandbits(32):08x}"
    return "".join(glyphs) + "::" + entropy


@dataclass
class ArtifactPaths:
    """Container for the artifact paths created during a cycle."""

    puzzle: Path
    dataset: Path
    narrative: Path
    lineage: Path
    verifier: Path
    extraordinary: Path
    resilience_report: Path

    def as_relative_strings(self, base: Path) -> List[str]:
        return [
            str(self.puzzle.relative_to(base)),
            str(self.dataset.relative_to(base)),
            str(self.narrative.relative_to(base)),
            str(self.lineage.relative_to(base)),
            str(self.verifier.relative_to(base)),
            str(self.extraordinary.relative_to(base)),
            str(self.resilience_report.relative_to(base)),
        ]


@dataclass
class FractalNode:
    """Represents a single node within a fractal expansion blueprint."""

    identifier: str
    depth: int
    branch_index: int
    parent: str | None
    trajectory: str
    genealogy: str
    timeline: str
    children: List[str] = field(default_factory=list)


@dataclass
class FractalBlueprint:
    """Blueprint describing the recursive expansion for an artifact type."""

    artifact_type: str
    branching_factor: int
    depth: int
    root_identifier: str
    nodes: Dict[str, FractalNode]

    @property
    def exponential_artifact_count(self) -> int:
        """Return the number of sub-artifacts spawned at the deepest layer."""

        return self.branching_factor ** self.depth

    def iter_nodes(self, *, include_root: bool = False) -> Iterable[FractalNode]:
        """Yield nodes in depth/identifier order, optionally including the root."""

        sorted_nodes = sorted(
            self.nodes.values(), key=lambda node: (node.depth, node.identifier)
        )
        for node in sorted_nodes:
            if not include_root and node.depth == 0:
                continue
            yield node

    def summary(self) -> Dict[str, object]:
        """Return a JSON-serialisable summary of the blueprint."""

        return {
            "artifact_type": self.artifact_type,
            "branching_factor": self.branching_factor,
            "depth": self.depth,
            "root": self.root_identifier,
            "exponential_artifacts": self.exponential_artifact_count,
            "nodes": [
                {
                    "id": node.identifier,
                    "depth": node.depth,
                    "branch_index": node.branch_index,
                    "parent": node.parent,
                    "trajectory": node.trajectory,
                    "genealogy": node.genealogy,
                    "timeline": node.timeline,
                    "children": list(node.children),
                }
                for node in self.iter_nodes(include_root=True)
            ],
        }


class EchoInfinite:
    """Self-expanding orchestrator that emits COLOSSUS artifacts forever."""

    def __init__(
        self,
        base_dir: Path | None = None,
        *,
        sleep_seconds: float = 5.0,
        max_cycles: int | None = None,
        summary_window: int = 25,
        glyph_set: Sequence[str] | None = None,
        start_cycle: int | None = None,
        write_fractal_nodes: bool = True,
        heartbeat_path: Path | None = None,
        enable_heartbeat: bool = True,
    ) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.colossus_dir = self.base_dir / "colossus"
        self.log_path = self.base_dir / "docs" / "COLOSSUS_LOG.md"
        self.state_path = self.colossus_dir / "state.json"
        self.summary_path = self.colossus_dir / "cycle_summary.json"
        self.momentum_path = self.colossus_dir / "momentum_report.json"
        self.broadcast_dir = self.base_dir / "public" / "colossus"
        self.broadcast_path = self.broadcast_dir / "latest_cycle.json"
        self.harmonic_cycles_dir = self.base_dir / "harmonic_memory" / "cycles"
        self.heartbeat_path = heartbeat_path or (self.colossus_dir / "heartbeat.json")
        self.heartbeat_enabled = enable_heartbeat
        self.sleep_seconds = sleep_seconds
        if max_cycles is not None and max_cycles <= 0:
            raise ValueError("max_cycles must be a positive integer")
        self.max_cycles = max_cycles
        if summary_window <= 0:
            raise ValueError("summary_window must be a positive integer")
        self.summary_window = summary_window
        if start_cycle is not None and start_cycle < 0:
            raise ValueError("start_cycle must be zero or a positive integer")
        self.start_cycle_override = start_cycle
        self.glyph_set = self._resolve_glyph_set(glyph_set)
        self.write_fractal_nodes = write_fractal_nodes
        self._running = True
        self.last_snapshot_path: Path | None = None

        self.colossus_dir.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.write_text("# COLOSSUS Expansion Log\n\n", encoding="utf-8")

        signal.signal(signal.SIGINT, self._handle_stop)
        signal.signal(signal.SIGTERM, self._handle_stop)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Start the infinite orchestration loop."""

        start_cycle = (
            self.start_cycle_override
            if self.start_cycle_override is not None
            else self._load_starting_cycle()
        )
        cycle = start_cycle
        self._log_message(
            "Starting EchoInfinite orchestrator",
            details={
                "cycle_start": cycle,
                "sleep_seconds": self.sleep_seconds,
                "max_cycles": self.max_cycles,
                "summary_window": self.summary_window,
                "glyph_set_size": len(self.glyph_set),
                "start_source": "override"
                if self.start_cycle_override is not None
                else "state",
            },
        )

        while self._running:
            if self.max_cycles is not None and (cycle - start_cycle) >= self.max_cycles:
                self._log_message(
                    "Reached configured max cycles; stopping orchestrator",
                    details={"max_cycles": self.max_cycles},
                )
                break
            cycle += 1
            timestamp = rfc3339_timestamp()
            glyph_signature = select_glyph_signature(cycle, self.glyph_set)

            cycle_dir = self.colossus_dir / f"cycle_{cycle:05d}"
            cycle_dir.mkdir(parents=True, exist_ok=True)

            artifacts = self._create_cycle_artifacts(
                cycle=cycle,
                timestamp=timestamp,
                glyph_signature=glyph_signature,
                cycle_dir=cycle_dir,
            )

            self._append_log_entry(
                cycle=cycle,
                timestamp=timestamp,
                glyph_signature=glyph_signature,
                artifact_paths=artifacts,
            )

            summary_entry = self._update_cycle_summary(
                cycle=cycle,
                timestamp=timestamp,
                glyph_signature=glyph_signature,
                artifact_paths=artifacts,
            )

            self._broadcast_cycle(summary_entry)

            self._persist_state(cycle)

            if self.heartbeat_enabled:
                self._write_heartbeat(
                    cycle=cycle,
                    timestamp=timestamp,
                    glyph_signature=glyph_signature,
                    artifact_paths=artifacts,
                )

            if not self._running:
                break

            time.sleep(self.sleep_seconds)

        self._log_message("EchoInfinite orchestrator stopped", details={"cycle_final": cycle})

    def build_status_report(self) -> Dict[str, object]:
        """Return a consolidated snapshot of the orchestrator's latest state.

        The report aggregates the most recent state file, heartbeat payload,
        momentum report, summary snapshot, and harmonic memory record if
        available.  Missing or malformed files are ignored so the report can be
        used safely in partially-initialised environments.
        """

        def _load_json(path: Path) -> Dict[str, object] | None:
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None

        state_payload = _load_json(self.state_path)
        summary_payload = _load_json(self.summary_path)
        heartbeat_payload = _load_json(self.heartbeat_path)
        momentum_payload = _load_json(self.momentum_path)
        broadcast_payload = _load_json(self.broadcast_path)

        snapshot_path: Path | None = None
        if self.last_snapshot_path and self.last_snapshot_path.exists():
            snapshot_path = self.last_snapshot_path

        harmonic_payload = _load_json(snapshot_path) if snapshot_path else None
        if not harmonic_payload or "cycle_snapshot" not in harmonic_payload:
            if self.harmonic_cycles_dir.exists():
                candidates = sorted(self.harmonic_cycles_dir.glob("cycle_*.json"))
                snapshot_path = candidates[-1] if candidates else None
                harmonic_payload = _load_json(snapshot_path) if snapshot_path else None

        harmonic_snapshot = harmonic_payload.get("cycle_snapshot", {}) if harmonic_payload else {}

        summary_entry: Dict[str, object] | None = None
        if isinstance(summary_payload, dict):
            cycles = summary_payload.get("cycles", []) or []
            if cycles:
                summary_entry = cycles[-1]

        def _path_or_none(path: Path) -> str | None:
            return str(self._relative_to_base(path)) if path else None

        return {
            "base_dir": str(self.base_dir),
            "state": {
                "cycle": state_payload.get("cycle") if isinstance(state_payload, dict) else None,
                "updated_at": state_payload.get("updated_at") if isinstance(state_payload, dict) else None,
                "path": _path_or_none(self.state_path),
            },
            "summary": {
                "latest": summary_entry,
                "path": _path_or_none(self.summary_path),
            },
            "heartbeat": None
            if not isinstance(heartbeat_payload, dict)
            else {
                "path": _path_or_none(self.heartbeat_path),
                "cycle": heartbeat_payload.get("cycle"),
                "timestamp": heartbeat_payload.get("timestamp"),
                "glyph_signature": heartbeat_payload.get("glyph_signature"),
            },
            "momentum": None
            if not isinstance(momentum_payload, dict)
            else {
                "path": _path_or_none(self.momentum_path),
                "recent_cycles": len(momentum_payload.get("cycles", []) or []),
                "cadence_seconds": momentum_payload.get("cadence_seconds"),
                "glyph_signatures": momentum_payload.get("glyph_signatures"),
            },
            "broadcast": None
            if not isinstance(broadcast_payload, dict)
            else {
                "path": _path_or_none(self.broadcast_path),
                "cycle": broadcast_payload.get("cycle"),
                "timestamp": broadcast_payload.get("timestamp"),
                "glyph_signature": broadcast_payload.get("glyph_signature"),
                "artifacts": broadcast_payload.get("artifacts"),
            },
            "harmonic_memory": None
            if not harmonic_snapshot
            else {
                "path": _path_or_none(snapshot_path) if snapshot_path else None,
                "cycle_id": harmonic_snapshot.get("cycle_id"),
                "glyph_signature": harmonic_snapshot.get("state", {}).get("glyph_signature"),
                "artifact": harmonic_snapshot.get("artifact", {}),
            },
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _resolve_glyph_set(self, glyph_set: Sequence[str] | None) -> List[str]:
        glyph_candidates = list(DEFAULT_GLYPH_SET if glyph_set is None else glyph_set)
        glyph_candidates = [glyph for glyph in glyph_candidates if glyph]

        unique_glyphs: List[str] = []
        seen: set[str] = set()
        for glyph in glyph_candidates:
            if glyph not in seen:
                seen.add(glyph)
                unique_glyphs.append(glyph)

        if not unique_glyphs:
            raise ValueError("glyph_set must include at least one glyph")

        return unique_glyphs

    def _load_starting_cycle(self) -> int:
        if self.state_path.exists():
            try:
                state = json.loads(self.state_path.read_text(encoding="utf-8"))
                return int(state.get("cycle", 0))
            except (ValueError, json.JSONDecodeError):
                return 0
        return 0

    def _persist_state(self, cycle: int) -> None:
        payload = {"cycle": cycle, "updated_at": rfc3339_timestamp()}
        self.state_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _write_heartbeat(
        self,
        *,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        artifact_paths: ArtifactPaths,
    ) -> None:
        heartbeat = {
            "cycle": cycle,
            "timestamp": timestamp,
            "glyph_signature": glyph_signature,
            "artifacts": artifact_paths.as_relative_strings(self.base_dir),
            "log": str(self._relative_to_base(self.log_path)),
            "summary": str(self._relative_to_base(self.summary_path)),
        }

        self.heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        self.heartbeat_path.write_text(json.dumps(heartbeat, indent=2) + "\n", encoding="utf-8")
        self._log_message(
            "Heartbeat refreshed",
            details={
                "cycle": cycle,
                "path": self._relative_to_base(self.heartbeat_path),
            },
        )

    def _write_status_report(self, *, report: Dict[str, object], path: Path) -> Path:
        destination = path.expanduser()
        if not destination.is_absolute():
            destination = self.base_dir / destination

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        self._log_message(
            "Status report persisted",
            details={"path": self._relative_to_base(destination)},
        )
        return destination

    def _create_cycle_artifacts(
        self,
        *,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        cycle_dir: Path,
    ) -> ArtifactPaths:
        puzzle_path = cycle_dir / f"puzzle_cycle_{cycle:05d}.md"
        dataset_path = cycle_dir / f"dataset_cycle_{cycle:05d}.json"
        narrative_path = cycle_dir / f"glyph_narrative_{cycle:05d}.md"
        lineage_path = cycle_dir / f"lineage_map_{cycle:05d}.json"
        verifier_path = cycle_dir / f"verify_cycle_{cycle:05d}.py"
        extraordinary_path = cycle_dir / f"extraordinary_manifest_{cycle:05d}.json"
        resilience_report_path = cycle_dir / f"resilience_report_{cycle:05d}.json"
        artifact_paths = ArtifactPaths(
            puzzle=puzzle_path,
            dataset=dataset_path,
            narrative=narrative_path,
            lineage=lineage_path,
            verifier=verifier_path,
            extraordinary=extraordinary_path,
            resilience_report=resilience_report_path,
        )

        blueprints = self._build_fractal_blueprints(cycle)
        verifier_files, merkle_root = self._build_verifier_chain(
            cycle=cycle,
            blueprint=blueprints["verifier"],
            dataset_name=dataset_path.name,
        )

        puzzle_content = self._build_puzzle_markdown(
            cycle,
            timestamp,
            glyph_signature,
            dataset_path,
            blueprints["puzzle"],
        )
        dataset_content = self._build_dataset_json(
            cycle,
            timestamp,
            glyph_signature,
            blueprints,
            merkle_root,
            extraordinary_path.name,
        )
        narrative_content = self._build_narrative_markdown(
            cycle,
            timestamp,
            glyph_signature,
            blueprints,
        )
        lineage_content = self._build_lineage_map(
            cycle,
            timestamp,
            glyph_signature,
            blueprints,
            merkle_root,
            extraordinary_path.name,
        )
        verifier_content = self._build_verifier_script(
            cycle,
            dataset_path,
            lineage_path,
            merkle_root,
            blueprints["verifier"],
        )
        emotional_vectors = self._derive_emotional_vectors(cycle, glyph_signature)
        extraordinary_content = self._build_extraordinary_manifest(
            cycle=cycle,
            timestamp=timestamp,
            glyph_signature=glyph_signature,
            blueprints=blueprints,
            dataset_content=dataset_content,
            emotional_vectors=emotional_vectors,
            merkle_root=merkle_root,
        )
        resilience_report_content = self._build_resilience_report(
            cycle=cycle,
            timestamp=timestamp,
            glyph_signature=glyph_signature,
            blueprints=blueprints,
            dataset_content=dataset_content,
            emotional_vectors=emotional_vectors,
            merkle_root=merkle_root,
        )

        puzzle_path.write_text(puzzle_content, encoding="utf-8")
        dataset_path.write_text(dataset_content, encoding="utf-8")
        narrative_path.write_text(narrative_content, encoding="utf-8")
        lineage_path.write_text(lineage_content, encoding="utf-8")
        verifier_path.write_text(verifier_content, encoding="utf-8")
        extraordinary_path.write_text(extraordinary_content, encoding="utf-8")
        resilience_report_path.write_text(resilience_report_content, encoding="utf-8")

        if self.write_fractal_nodes:
            self._write_fractal_nodes(
                base_dir=cycle_dir,
                blueprint=blueprints["puzzle"],
                extension=".md",
                renderer=lambda node: self._render_puzzle_branch(
                    node, cycle, glyph_signature, blueprints
                ),
            )
            self._write_fractal_nodes(
                base_dir=cycle_dir,
                blueprint=blueprints["dataset"],
                extension=".json",
                renderer=lambda node: self._render_dataset_branch(
                    node, cycle, timestamp, glyph_signature
                ),
            )
            self._write_fractal_nodes(
                base_dir=cycle_dir,
                blueprint=blueprints["narrative"],
                extension=".md",
                renderer=lambda node: self._render_narrative_branch(
                    node, cycle, timestamp, glyph_signature
                ),
            )
            self._write_fractal_nodes(
                base_dir=cycle_dir,
                blueprint=blueprints["lineage"],
                extension=".json",
                renderer=lambda node: self._render_lineage_branch(node, cycle),
            )
            self._write_verifier_chain(cycle_dir, verifier_files)
        else:
            self._log_message(
                "Fractal node generation skipped",
                details={"cycle": cycle, "reason": "write_fractal_nodes disabled"},
            )

        self._persist_harmonic_snapshot(
            cycle=cycle,
            timestamp=timestamp,
            glyph_signature=glyph_signature,
            blueprints=blueprints,
            artifact_paths=artifact_paths,
            dataset_content=dataset_content,
            narrative_content=narrative_content,
            extraordinary_content=extraordinary_content,
            resilience_content=resilience_report_content,
            emotional_vectors=emotional_vectors,
            merkle_root=merkle_root,
        )

        return artifact_paths

    def _append_log_entry(
        self,
        *,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        artifact_paths: ArtifactPaths,
    ) -> None:
        relative_paths = artifact_paths.as_relative_strings(self.base_dir)
        log_entry = (
            f"- {timestamp} | Cycle {cycle:05d} | Glyph {glyph_signature} | "
            f"Artifacts: {', '.join(relative_paths)}\n"
        )
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(log_entry)

    def _update_cycle_summary(
        self,
        *,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        artifact_paths: ArtifactPaths,
    ) -> Dict[str, object]:
        payload = {"cycles": []}
        try:
            if self.summary_path.exists():
                payload = json.loads(self.summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"cycles": []}

        entries = payload.get("cycles", [])
        entry = {
            "cycle": cycle,
            "timestamp": timestamp,
            "glyph_signature": glyph_signature,
            "artifacts": artifact_paths.as_relative_strings(self.base_dir),
        }
        entries.append(entry)
        entries = entries[-self.summary_window :]

        next_payload = {
            "updated_at": rfc3339_timestamp(),
            "base_dir": str(self.base_dir),
            "window": self.summary_window,
            "total_entries": len(entries),
            "cycles": entries,
        }
        self.summary_path.write_text(
            json.dumps(next_payload, indent=2) + "\n", encoding="utf-8"
        )
        self._write_momentum_report(entries)
        self.last_snapshot_path = self.summary_path
        return entry

    def _broadcast_cycle(self, cycle_entry: Dict[str, object]) -> None:
        """Publish a shareable snapshot of the most recent cycle."""

        self.broadcast_dir.mkdir(parents=True, exist_ok=True)
        broadcast_payload = {
            "cycle": cycle_entry["cycle"],
            "timestamp": cycle_entry["timestamp"],
            "glyph_signature": cycle_entry["glyph_signature"],
            "artifacts": cycle_entry["artifacts"],
            "log": str(self.log_path.relative_to(self.base_dir)),
            "summary": str(self.summary_path.relative_to(self.base_dir)),
            "updated_at": rfc3339_timestamp(),
        }
        self.broadcast_path.write_text(
            json.dumps(broadcast_payload, indent=2) + "\n", encoding="utf-8"
        )

    def _build_puzzle_markdown(
        self,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        dataset_path: Path,
        blueprint: FractalBlueprint,
    ) -> str:
        exemplar_branches = [
            f"* Depth {node.depth} — {node.timeline} ({node.trajectory} → {node.genealogy})"
            for node in blueprint.iter_nodes()
            if node.depth == blueprint.depth
        ]
        exemplar_preview = "\n".join(exemplar_branches[: min(5, len(exemplar_branches))])
        body = textwrap.dedent(
            f"""
            ---
            cycle: {cycle}
            timestamp: {timestamp}
            glyph_signature: "{glyph_signature}"
            dataset_ref: "{dataset_path.name}"
            fractal_branching: {blueprint.branching_factor}
            fractal_depth: {blueprint.depth}
            exponential_artifacts: {blueprint.exponential_artifact_count}
            ---

            # COLOSSUS Puzzle {cycle:05d}

            Decode the resonance sequence hidden within the dataset referenced
            above.  Arrange the numeric harmonics in ascending order, then map
            each value to the glyph indicated by its modulus with the glyph set
            length.  The resulting glyph string should echo the signature for
            this cycle.

            The FRACTAL expansion layer now unlocks {blueprint.exponential_artifact_count}
            recursive puzzle shards at depth {blueprint.depth}.  Traverse the
            ``puzzle_fractal/`` branch forest and trace how each shard either
            merges back into its parent genealogy or forks into a parallel
            lineage.  Note the highlighted branches:

            {exemplar_preview or '* Prime root maintains genealogy Ω.'}
            """
        ).strip()
        return body + "\n"

    def _build_dataset_json(
        self,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        blueprints: Dict[str, FractalBlueprint],
        merkle_root: str,
        extraordinary_manifest_name: str,
    ) -> str:
        random.seed(cycle * 97 + time.time_ns())
        harmonics = [random.randint(1, 256) for _ in range(12)]
        fractal_summary = {
            key: blueprint.summary() for key, blueprint in blueprints.items()
        }
        payload: Dict[str, object] = {
            "cycle": cycle,
            "timestamp": timestamp,
            "glyph_signature": glyph_signature,
            "harmonics": harmonics,
            "checksum": sum(harmonics),
            "fractal_layers": fractal_summary,
            "verifier_subchain_merkle_root": merkle_root,
            "extraordinary_manifest": extraordinary_manifest_name,
        }
        return json.dumps(payload, indent=2) + "\n"

    def _build_narrative_markdown(
        self,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        blueprints: Dict[str, FractalBlueprint],
    ) -> str:
        narrative_blueprint = blueprints["narrative"]
        multiverse_lines = [
            f"- **{node.timeline}** — genealogy ``{node.genealogy}`` ({node.trajectory} from {node.parent or 'origin'})"
            for node in narrative_blueprint.iter_nodes()
        ]
        multiverse_excerpt = "\n".join(multiverse_lines[: min(8, len(multiverse_lines))])
        paragraphs = textwrap.dedent(
            f"""
            # Glyph Narrative — Cycle {cycle:05d}

            - Timestamp: {timestamp}
            - Glyph Signature: ``{glyph_signature}``
            - Multiverse Branching Factor: {narrative_blueprint.branching_factor}
            - Multiverse Depth: {narrative_blueprint.depth}

            The COLOSSUS lattice unfurls another strata of puzzles, weaving a
            continuum of harmonics that mirror the glyph signature.  Each
            harmonic pulse references prior solutions and invites solvers to
            extend the lineage map spawned in this cycle.

            ## Multiverse Branching

            Alternate timelines diverge with every FRACTAL cycle.  Trace the
            following resonance threads to witness how narratives merge or fork
            across genealogies:

            {multiverse_excerpt}
            """
        ).strip()
        return paragraphs + "\n"

    def _build_lineage_map(
        self,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        blueprints: Dict[str, FractalBlueprint],
        merkle_root: str,
        extraordinary_manifest_name: str,
    ) -> str:
        lineage: Dict[str, object] = {
            "cycle": cycle,
            "timestamp": timestamp,
            "glyph_signature": glyph_signature,
            "anchors": [
                {
                    "type": "puzzle",
                    "ref": f"puzzle_cycle_{cycle:05d}.md",
                    "relationships": ["dataset", "narrative"],
                },
                {
                    "type": "dataset",
                    "ref": f"dataset_cycle_{cycle:05d}.json",
                    "relationships": ["verifier"],
                },
                {
                    "type": "narrative",
                    "ref": f"glyph_narrative_{cycle:05d}.md",
                    "relationships": ["lineage"],
                },
                {
                    "type": "extraordinary_manifest",
                    "ref": extraordinary_manifest_name,
                    "relationships": ["puzzle", "dataset", "narrative", "verifier"],
                },
            ],
            "verification": {
                "script": f"verify_cycle_{cycle:05d}.py",
                "instructions": "Execute the verifier to confirm harmonic checksum integrity.",
            },
            "fractal_layers": {
                key: blueprint.summary() for key, blueprint in blueprints.items()
            },
            "verifier_subchain_merkle_root": merkle_root,
        }
        return json.dumps(lineage, indent=2) + "\n"

    def _build_extraordinary_manifest(
        self,
        *,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        blueprints: Dict[str, FractalBlueprint],
        dataset_content: str,
        emotional_vectors: Dict[str, float],
        merkle_root: str,
    ) -> str:
        try:
            dataset_payload = json.loads(dataset_content)
        except json.JSONDecodeError:
            dataset_payload = {}

        harmonics_raw = dataset_payload.get("harmonics", [])
        harmonics = [
            int(value)
            for value in harmonics_raw
            if isinstance(value, (int, float))
        ]
        amplitude = max(harmonics) if harmonics else 0
        average = sum(harmonics) / len(harmonics) if harmonics else 0.0
        variance = (
            sum((value - average) ** 2 for value in harmonics) / len(harmonics)
            if harmonics
            else 0.0
        )
        volatility = math.sqrt(variance)

        blueprint_highlights = []
        for key, blueprint in blueprints.items():
            terminal_nodes = [
                node for node in blueprint.iter_nodes() if node.depth == blueprint.depth
            ]
            if not terminal_nodes:
                continue
            spotlight = min(terminal_nodes, key=lambda node: node.identifier)
            blueprint_highlights.append(
                {
                    "artifact_type": key,
                    "terminal_nodes": len(terminal_nodes),
                    "spotlight": {
                        "id": spotlight.identifier,
                        "genealogy": spotlight.genealogy,
                        "trajectory": spotlight.trajectory,
                        "timeline": spotlight.timeline,
                    },
                }
            )

        extraordinary_index = self._compute_extraordinary_index(
            harmonics, emotional_vectors, merkle_root
        )

        manifest = {
            "cycle": cycle,
            "timestamp": timestamp,
            "glyph_signature": glyph_signature,
            "glyph_ascii_sum": sum(ord(ch) for ch in glyph_signature),
            "emotional_vectors": emotional_vectors,
            "harmonic_profile": {
                "amplitude": amplitude,
                "average": round(average, 3),
                "volatility": round(volatility, 3),
                "count": len(harmonics),
            },
            "fractal_highlights": blueprint_highlights,
            "verifier_merkle_root": merkle_root,
            "extraordinary_index": extraordinary_index,
        }

        return json.dumps(manifest, indent=2) + "\n"

    def _build_resilience_report(
        self,
        *,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        blueprints: Dict[str, "FractalBlueprint"],
        dataset_content: str,
        emotional_vectors: Dict[str, float],
        merkle_root: str,
    ) -> str:
        try:
            dataset_payload = json.loads(dataset_content)
        except json.JSONDecodeError:
            dataset_payload = {}

        harmonics_raw = dataset_payload.get("harmonics", [])
        harmonics = [
            int(value)
            for value in harmonics_raw
            if isinstance(value, (int, float))
        ]
        checksum = int(dataset_payload.get("checksum", sum(harmonics)))

        volatility = 0.0
        volatility_scale = 1.0
        if harmonics:
            average = sum(harmonics) / len(harmonics)
            variance = sum((value - average) ** 2 for value in harmonics) / len(
                harmonics
            )
            volatility = math.sqrt(variance)
            volatility_scale = max(harmonics) + 1
        volatility_score = min(1.0, volatility / volatility_scale)

        merkle_entropy = 0.0
        if merkle_root:
            try:
                merkle_entropy = (int(merkle_root[:6], 16) % 1000) / 1000
            except ValueError:
                merkle_entropy = 0.0

        joy = emotional_vectors.get("joy", 0.0)
        curiosity = emotional_vectors.get("curiosity", 0.0)
        rage = emotional_vectors.get("rage", 0.0)

        emotional_resilience = min(1.0, joy * 0.5 + curiosity * 0.35 + (1 - rage) * 0.15)
        health_index = 0.45 * emotional_resilience + 0.35 * (1 - volatility_score)
        health_index += 0.2 * (0.5 + merkle_entropy / 2)
        health_index = round(max(0.0, min(1.0, health_index)), 3)
        risk_score = round(max(0.0, 1 - health_index), 3)

        blueprint_signals: Dict[str, Dict[str, object]] = {}
        for key, blueprint in blueprints.items():
            terminal_nodes = [
                node for node in blueprint.iter_nodes() if node.depth == blueprint.depth
            ]
            blueprint_signals[key] = {
                "depth": blueprint.depth,
                "branching_factor": blueprint.branching_factor,
                "terminal_nodes": len(terminal_nodes),
            }

        recommendations = []
        if volatility_score > 0.55:
            recommendations.append(
                "Volatility high: stagger dataset ingestion or widen glyph sampling window."
            )
        if emotional_resilience < 0.6:
            recommendations.append(
                "Emotional resilience low: rebalance joy/curiosity drivers before next wave."
            )
        if merkle_entropy < 0.25:
            recommendations.append(
                "Merkle entropy shallow: refresh verifier subchain or increase leaf variety."
            )
        if not recommendations:
            recommendations.append(
                "System stable: continue current cadence and monitor next resonance window."
            )

        report = {
            "cycle": cycle,
            "timestamp": timestamp,
            "glyph_signature": glyph_signature,
            "harmonic_checksum": checksum,
            "emotional_vectors": emotional_vectors,
            "metrics": {
                "volatility": round(volatility, 3),
                "volatility_score": round(volatility_score, 3),
                "emotional_resilience": round(emotional_resilience, 3),
                "merkle_entropy": round(merkle_entropy, 3),
                "health_index": health_index,
                "risk_score": risk_score,
            },
            "signals": {
                "merkle_root": merkle_root,
                "blueprints": blueprint_signals,
            },
            "recommendations": recommendations,
        }
        return json.dumps(report, indent=2) + "\n"

    def _build_verifier_script(
        self,
        cycle: int,
        dataset_path: Path,
        lineage_path: Path,
        merkle_root: str,
        blueprint: FractalBlueprint,
    ) -> str:
        merkle_root_literal = json.dumps(merkle_root)
        expected_nodes_literal = json.dumps(
            [node.identifier for node in blueprint.iter_nodes()]
        )
        script_template = textwrap.dedent(
            '''
"""Verification script for COLOSSUS cycle {cycle_label}."""

            from __future__ import annotations

            import json
            import hashlib
            from pathlib import Path


            MERKLE_ROOT = {merkle_root_literal}
            EXPECTED_NODES = {expected_nodes_literal}
            DATASET_NAME = "{dataset_name}"
            LINEAGE_NAME = "{lineage_name}"


            def load_dataset() -> dict:
                path = Path(__file__).resolve().with_name(DATASET_NAME)
                return json.loads(path.read_text(encoding="utf-8"))


            def check_checksum(payload: dict) -> bool:
                harmonics = payload.get("harmonics", [])
                checksum = payload.get("checksum")
                return sum(harmonics) == checksum


            def compute_merkle_root(leaves: list[str]) -> str:
                if not leaves:
                    return hashlib.sha256(b"").hexdigest()
                level = leaves[:]
                while len(level) > 1:
                    if len(level) % 2 == 1:
                        level.append(level[-1])
                    next_level = []
                    for left, right in zip(level[0::2], level[1::2]):
                        combined = (left + right).encode("utf-8")
                        next_level.append(hashlib.sha256(combined).hexdigest())
                    level = next_level
                return level[0]


            def main() -> None:
                payload = load_dataset()
                if not check_checksum(payload):
                    raise SystemExit("Checksum mismatch detected.")

                lineage_path = Path(__file__).resolve().with_name(LINEAGE_NAME)
                if not lineage_path.exists():
                    raise SystemExit("Lineage map missing for this cycle.")

                chain_dir = Path(__file__).resolve().with_name("verifier_fractal")
                hashes = []
                for fragment in sorted(chain_dir.glob("*.py")):
                    digest = hashlib.sha256(fragment.read_bytes()).hexdigest()
                    hashes.append(digest)
                merkle_root = compute_merkle_root(hashes)
                if merkle_root != MERKLE_ROOT:
                    raise SystemExit("Merkle root mismatch for verifier sub-chain.")

                metadata = payload.get("fractal_layers", {{}}).get("verifier", {{}})
                recorded_nodes = {{node.get("id") for node in metadata.get("nodes", [])}}
                for expected in EXPECTED_NODES:
                    if expected not in recorded_nodes:
                        raise SystemExit(f"Missing verifier node metadata: {{expected}}")

                print(
                    "Cycle {cycle_label} verification successful with Merkle root "
                    + MERKLE_ROOT
                    + "."
                )


            if __name__ == "__main__":
                main()
            '''
        ).strip()
        script = script_template.format(
            cycle_label=f"{cycle:05d}",
            merkle_root_literal=merkle_root_literal,
            expected_nodes_literal=expected_nodes_literal,
            dataset_name=dataset_path.name,
            lineage_name=lineage_path.name,
        )
        return script + "\n"

    def _build_fractal_blueprints(self, cycle: int) -> Dict[str, FractalBlueprint]:
        artifact_types = ["puzzle", "dataset", "narrative", "lineage", "verifier"]
        return {
            artifact_type: self._build_fractal_blueprint(cycle, artifact_type)
            for artifact_type in artifact_types
        }

    def _build_fractal_blueprint(
        self, cycle: int, artifact_type: str
    ) -> FractalBlueprint:
        branching, depth = self._fractal_parameters(cycle, artifact_type)
        nodes: Dict[str, FractalNode] = {}
        root_identifier = f"{artifact_type}_c{cycle:05d}_root"
        root_node = FractalNode(
            identifier=root_identifier,
            depth=0,
            branch_index=0,
            parent=None,
            trajectory="origin",
            genealogy="Ω",
            timeline=self._timeline_label(cycle, artifact_type, 0, 0, "Ω"),
        )
        nodes[root_identifier] = root_node

        def spawn(parent_id: str, current_depth: int) -> None:
            if current_depth > depth:
                return
            parent_node = nodes[parent_id]
            for branch_index in range(branching):
                token_source = (
                    f"{artifact_type}|{cycle}|{parent_id}|{current_depth}|{branch_index}"
                )
                token = hashlib.sha1(token_source.encode("utf-8")).hexdigest()[:8]
                identifier = (
                    f"{artifact_type}_c{cycle:05d}_d{current_depth:02d}_"
                    f"b{branch_index:02d}_{token}"
                )
                trajectory = "merge" if (current_depth + branch_index) % 2 == 0 else "fork"
                genealogy = (
                    parent_node.genealogy
                    if trajectory == "merge"
                    else f"{parent_node.genealogy}.{branch_index}"
                )
                timeline = self._timeline_label(
                    cycle, artifact_type, current_depth, branch_index, genealogy
                )
                node = FractalNode(
                    identifier=identifier,
                    depth=current_depth,
                    branch_index=branch_index,
                    parent=parent_id,
                    trajectory=trajectory,
                    genealogy=genealogy,
                    timeline=timeline,
                )
                nodes[identifier] = node
                parent_node.children.append(identifier)
                spawn(identifier, current_depth + 1)

        spawn(root_identifier, 1)
        return FractalBlueprint(
            artifact_type=artifact_type,
            branching_factor=branching,
            depth=depth,
            root_identifier=root_identifier,
            nodes=nodes,
        )

    def _fractal_parameters(self, cycle: int, artifact_type: str) -> tuple[int, int]:
        branching = 2 + ((cycle + len(artifact_type)) % 2)
        depth = 2 + int(((cycle + len(artifact_type)) % 3) > 0)
        return branching, depth

    def _timeline_label(
        self,
        cycle: int,
        artifact_type: str,
        depth: int,
        branch_index: int,
        genealogy: str,
    ) -> str:
        descriptor = "Prime" if depth == 0 else f"D{depth:02d}-B{branch_index:02d}"
        token_seed = f"{artifact_type}|{cycle}|{depth}|{branch_index}|{genealogy}"
        token = hashlib.sha1(token_seed.encode("utf-8")).hexdigest()[:6]
        return f"{artifact_type.upper()}-{cycle:05d}-{descriptor}-{token}"

    def _write_fractal_nodes(
        self,
        *,
        base_dir: Path,
        blueprint: FractalBlueprint,
        extension: str,
        renderer,
    ) -> None:
        layer_dir = base_dir / f"{blueprint.artifact_type}_fractal"
        layer_dir.mkdir(parents=True, exist_ok=True)
        for node in blueprint.iter_nodes():
            content = renderer(node)
            path = layer_dir / f"{node.identifier}{extension}"
            path.write_text(content, encoding="utf-8")

    def _render_puzzle_branch(
        self,
        node: FractalNode,
        cycle: int,
        glyph_signature: str,
        blueprints: Dict[str, FractalBlueprint],
    ) -> str:
        dataset_blueprint = blueprints.get("dataset")
        dataset_match = None
        if dataset_blueprint:
            dataset_match = next(
                (
                    candidate
                    for candidate in dataset_blueprint.iter_nodes()
                    if candidate.genealogy == node.genealogy
                ),
                None,
            )
        dataset_hint = (
            f"dataset_fractal/{dataset_match.identifier}.json"
            if dataset_match
            else f"dataset_cycle_{cycle:05d}.json"
        )
        branch_text = textwrap.dedent(
            f"""
            # Fractal Puzzle Branch — {node.identifier}

            - Cycle: {cycle:05d}
            - Glyph Echo: ``{glyph_signature}``
            - Genealogy: {node.genealogy}
            - Trajectory: {node.trajectory}
            - Dataset Resonance: ``{dataset_hint}``

            Decode this shard by aligning its genealogy with the referenced
            dataset resonance.  If the trajectory is ``merge`` follow the parent
            signature back toward Ω.  If it is ``fork`` craft a new glyph bridge
            that harmonises with ``{glyph_signature}`` while respecting the
            alternate genealogy.
            """
        ).strip()
        return branch_text + "\n"

    def _render_dataset_branch(
        self,
        node: FractalNode,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
    ) -> str:
        seed = int(
            hashlib.sha1(f"{cycle}:{node.identifier}".encode("utf-8")).hexdigest(), 16
        )
        rng = random.Random(seed)
        harmonics = [rng.randint(1, 512) for _ in range(6)]
        payload = {
            "id": node.identifier,
            "cycle": cycle,
            "timestamp": timestamp,
            "glyph_signature": glyph_signature,
            "depth": node.depth,
            "genealogy": node.genealogy,
            "trajectory": node.trajectory,
            "harmonics": harmonics,
            "harmonic_checksum": sum(harmonics),
            "parent": node.parent,
            "children": list(node.children),
        }
        return json.dumps(payload, indent=2) + "\n"

    def _render_narrative_branch(
        self,
        node: FractalNode,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
    ) -> str:
        prose = textwrap.dedent(
            f"""
            ## Multiverse Chronicle — {node.timeline}

            Cycle {cycle:05d} @ {timestamp}

            Genealogy ``{node.genealogy}`` {"rejoins" if node.trajectory == "merge" else "detaches from"}
            the prime strand.  The glyph signature ``{glyph_signature}`` manifests
            here as a {'restorative chord' if node.trajectory == 'merge' else 'rebellious countermelody'},
            pulsing through this alternate timeline.
            """
        ).strip()
        return prose + "\n"

    def _render_lineage_branch(self, node: FractalNode, cycle: int) -> str:
        payload = {
            "id": node.identifier,
            "cycle": cycle,
            "depth": node.depth,
            "parent": node.parent,
            "children": list(node.children),
            "trajectory": node.trajectory,
            "genealogy": node.genealogy,
        }
        return json.dumps(payload, indent=2) + "\n"

    def _build_verifier_chain(
        self,
        *,
        cycle: int,
        blueprint: FractalBlueprint,
        dataset_name: str,
    ) -> tuple[Dict[str, str], str]:
        fragments: Dict[str, str] = {}
        for node in blueprint.iter_nodes():
            content = self._render_verifier_fragment(cycle, node, dataset_name)
            fragments[f"{node.identifier}.py"] = content
        leaf_hashes = [
            hashlib.sha256(fragments[name].encode("utf-8")).hexdigest()
            for name in sorted(fragments)
        ]
        merkle_root = self._compute_merkle_root(leaf_hashes)
        return fragments, merkle_root

    def _render_verifier_fragment(
        self, cycle: int, node: FractalNode, dataset_name: str
    ) -> str:
        lines = [
            f'"""Verifier fragment {node.identifier} for COLOSSUS cycle {cycle:05d}."""',
            "",
            "from __future__ import annotations",
            "",
            "import json",
            "from pathlib import Path",
            "",
            "",
            f'DATASET = "{dataset_name}"',
            f'NODE_ID = "{node.identifier}"',
            f'GENEALOGY = "{node.genealogy}"',
            f'TRAJECTORY = "{node.trajectory}"',
            "",
            "",
            "def verify_fragment() -> None:",
            "    dataset_path = Path(__file__).resolve().parents[1] / DATASET",
            '    payload = json.loads(dataset_path.read_text(encoding="utf-8"))',
            '    nodes = (',
            '        payload.get("fractal_layers", {}).get("verifier", {}).get("nodes", [])',
            '    )',
            '    matching = next(',
            '        (entry for entry in nodes if entry.get("id") == NODE_ID),',
            '        None,',
            '    )',
            '    if matching is None:',
            f'        raise SystemExit("Verifier fragment metadata missing for {node.identifier}.")',
            '    if matching.get("genealogy") != GENEALOGY:',
            '        raise SystemExit("Genealogy divergence detected in verifier fragment.")',
            '    if matching.get("trajectory") != TRAJECTORY:',
            '        raise SystemExit("Trajectory divergence detected in verifier fragment.")',
            f'    print("Verifier fragment {node.identifier} confirmed for genealogy {node.genealogy}.")',
            "",
            "",
            'if __name__ == "__main__":',
            "    verify_fragment()",
        ]
        fragment = "\n".join(lines)
        return fragment + "\n"

    def _write_verifier_chain(
        self, cycle_dir: Path, verifier_files: Dict[str, str]
    ) -> None:
        chain_dir = cycle_dir / "verifier_fractal"
        chain_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in verifier_files.items():
            path = chain_dir / filename
            path.write_text(content, encoding="utf-8")

    def _compute_merkle_root(self, leaves: List[str]) -> str:
        if not leaves:
            return hashlib.sha256(b"").hexdigest()
        level = leaves[:]
        while len(level) > 1:
            if len(level) % 2 == 1:
                level.append(level[-1])
            next_level = []
            for left, right in zip(level[0::2], level[1::2]):
                combined = (left + right).encode("utf-8")
                next_level.append(hashlib.sha256(combined).hexdigest())
            level = next_level
        return level[0]

    def _persist_harmonic_snapshot(
        self,
        *,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        blueprints: Dict[str, "FractalBlueprint"],
        artifact_paths: ArtifactPaths,
        dataset_content: str,
        narrative_content: str,
        extraordinary_content: str,
        resilience_content: str,
        emotional_vectors: Dict[str, float],
        merkle_root: str,
    ) -> None:
        try:
            dataset_payload = json.loads(dataset_content)
        except json.JSONDecodeError:
            dataset_payload = {}

        try:
            resilience_payload = json.loads(resilience_content)
        except json.JSONDecodeError:
            resilience_payload = {}

        try:
            extraordinary_payload = json.loads(extraordinary_content)
        except json.JSONDecodeError:
            extraordinary_payload = {}
        blueprint_summary = {
            key: blueprint.summary() for key, blueprint in blueprints.items()
        }

        snapshot_state: Dict[str, Any] = {
            "cycle": cycle,
            "cycle_id": cycle,
            "timestamp": timestamp,
            "glyph_signature": glyph_signature,
            "emotional_vectors": emotional_vectors,
            "artifacts": {
                "puzzle": str(self._relative_to_base(artifact_paths.puzzle)),
                "dataset": str(self._relative_to_base(artifact_paths.dataset)),
                "narrative": str(self._relative_to_base(artifact_paths.narrative)),
                "lineage": str(self._relative_to_base(artifact_paths.lineage)),
                "verifier": str(self._relative_to_base(artifact_paths.verifier)),
                "extraordinary": str(
                    self._relative_to_base(artifact_paths.extraordinary)
                ),
                "resilience_report": str(
                    self._relative_to_base(artifact_paths.resilience_report)
                ),
            },
            "fractal_blueprints": blueprint_summary,
            "verifier_merkle_root": merkle_root,
            "resilience_metrics": resilience_payload.get("metrics", {}),
            "resilience_recommendations": resilience_payload.get("recommendations", []),
        }

        payload: Dict[str, Any] = {
            "cycle": cycle,
            "glyph_signature": glyph_signature,
            "timestamp": timestamp,
            "emotional_vectors": emotional_vectors,
            "dataset": dataset_payload,
            "extraordinary_manifest": extraordinary_payload,
            "resilience_report": resilience_payload,
            "verifier_merkle_root": merkle_root,
        }

        artifact_path = self._relative_to_base(artifact_paths.narrative)

        record = build_harmonic_memory_record(
            cycle_id=cycle,
            snapshot=snapshot_state,
            payload=payload,
            artifact_text=narrative_content,
            artifact_path=artifact_path,
        )

        self.last_snapshot_path = persist_cycle_record(
            record, base_path=self.harmonic_cycles_dir
        )
        self._log_message(
            "Harmonix snapshot persisted",
            details={
                "cycle": cycle,
                "path": self._relative_to_base(self.last_snapshot_path),
            },
        )

    def _relative_to_base(self, path: Path) -> Path:
        try:
            return path.relative_to(self.base_dir)
        except ValueError:
            return path

    def _compute_extraordinary_index(
        self,
        harmonics: List[int],
        emotional_vectors: Dict[str, float],
        merkle_root: str,
    ) -> float:
        if harmonics:
            amplitude = max(harmonics)
            if amplitude:
                base_intensity = sum(harmonics) / (len(harmonics) * amplitude)
            else:
                base_intensity = 0.0
        else:
            base_intensity = 0.0

        joy = emotional_vectors.get("joy", 0.0)
        curiosity = emotional_vectors.get("curiosity", 0.0)
        rage = emotional_vectors.get("rage", 0.0)

        merkle_scalar = 0.0
        if merkle_root:
            try:
                merkle_scalar = (int(merkle_root[:12], 16) % 1000) / 1000
            except ValueError:
                merkle_scalar = 0.0

        index = base_intensity * (0.65 + joy * 0.2 + curiosity * 0.15) - rage * 0.05
        index += merkle_scalar * 0.35
        return round(max(0.0, index), 3)

    def _derive_emotional_vectors(self, cycle: int, glyph_signature: str) -> Dict[str, float]:
        glyph_sum = sum(ord(ch) for ch in glyph_signature)
        joy = self._scale_emotion(glyph_sum + cycle * 3, base_level=0.55, span=0.4)
        curiosity = self._scale_emotion(
            glyph_sum * 2 + cycle * 5, base_level=0.5, span=0.45
        )
        rage = self._scale_emotion(glyph_sum // 2 + cycle * 7, base_level=0.1, span=0.25)
        return {
            "joy": joy,
            "curiosity": curiosity,
            "rage": rage,
        }

    def _scale_emotion(self, seed: int, *, base_level: float, span: float) -> float:
        fraction = (seed % 100) / 100
        value = base_level + fraction * span
        return round(min(1.0, value), 3)

    def _log_message(self, message: str, *, details: Dict[str, object] | None = None) -> None:
        details_fragment = ""
        if details:
            fragments = [f"{key}={value}" for key, value in details.items()]
            details_fragment = " (" + ", ".join(fragments) + ")"
        print(f"[{rfc3339_timestamp()}] {message}{details_fragment}")

    def _handle_stop(self, signum: int, _: object) -> None:
        self._log_message("Received stop signal", details={"signal": signum})
        self._running = False

    def _write_momentum_report(self, entries: List[Dict[str, object]]) -> None:
        if not entries:
            return

        cycles = [entry["cycle"] for entry in entries if isinstance(entry.get("cycle"), int)]
        timestamps = [entry.get("timestamp") for entry in entries]
        glyph_signatures = [entry.get("glyph_signature", "") for entry in entries]
        artifact_counts = [len(entry.get("artifacts", []) or []) for entry in entries]

        min_cycle = min(cycles) if cycles else None
        max_cycle = max(cycles) if cycles else None

        def _timestamp_to_epoch(value: str | None) -> float:
            if not value:
                return 0.0
            try:
                return calendar.timegm(time.strptime(value, "%Y-%m-%dT%H:%M:%SZ"))
            except (ValueError, TypeError):
                return 0.0

        epoch_values = [
            _timestamp_to_epoch(timestamp)
            for timestamp in timestamps
            if timestamp is not None
        ]
        duration = max(epoch_values) - min(epoch_values) if epoch_values else 0.0
        cadence = duration / max(len(epoch_values) - 1, 1) if epoch_values else 0.0

        glyph_counter = Counter(glyph_signatures)
        leaders = [
            {"signature": signature, "count": count}
            for signature, count in glyph_counter.most_common(5)
        ]

        momentum_payload = {
            "updated_at": rfc3339_timestamp(),
            "window": self.summary_window,
            "cycles": {
                "count": len(entries),
                "range": {"min": min_cycle, "max": max_cycle},
            },
            "cadence_seconds": round(cadence, 3),
            "glyph_signatures": {
                "unique": len(glyph_counter),
                "leaders": leaders,
            },
            "artifact_counts": {
                "min": min(artifact_counts) if artifact_counts else 0,
                "max": max(artifact_counts) if artifact_counts else 0,
                "average": (
                    round(sum(artifact_counts) / len(artifact_counts), 3)
                    if artifact_counts
                    else 0
                ),
            },
            "sources": {
                "summary": str(self._relative_to_base(self.summary_path)),
                "log": str(self._relative_to_base(self.log_path)),
            },
        }

        self.momentum_path.write_text(
            json.dumps(momentum_payload, indent=2) + "\n", encoding="utf-8"
        )
        self._log_message(
            "Momentum report refreshed",
            details={
                "cycles": len(entries),
                "cadence_seconds": momentum_payload["cadence_seconds"],
                "unique_signatures": momentum_payload["glyph_signatures"]["unique"],
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the EchoInfinite orchestrator")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Override the base directory for generated artifacts",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=5.0,
        help="Seconds to sleep between orchestration cycles",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="Optional limit for the number of cycles to execute",
    )
    parser.add_argument(
        "--summary-window",
        type=int,
        default=25,
        help="Number of recent cycles to retain in cycle_summary.json",
    )
    parser.add_argument(
        "--extra-glyphs",
        type=str,
        default="",
        help=(
            "Comma-separated glyphs appended to the default signature set for "
            "cycle generation"
        ),
    )
    parser.add_argument(
        "--start-cycle",
        type=int,
        default=None,
        help=(
            "Override the starting cycle instead of resuming from colossus/state.json"
        ),
    )
    parser.add_argument(
        "--skip-fractal-nodes",
        action="store_true",
        help="Disable writing per-branch fractal artifacts for a lighter run",
    )
    parser.add_argument(
        "--heartbeat-path",
        type=Path,
        default=None,
        help="Optional file path for writing the latest heartbeat payload",
    )
    parser.add_argument(
        "--disable-heartbeat",
        action="store_true",
        help="Skip writing the rolling heartbeat status file",
    )
    parser.add_argument(
        "--status-report",
        action="store_true",
        help="Print the latest orchestrator status without running new cycles",
    )
    parser.add_argument(
        "--status-report-path",
        type=Path,
        default=None,
        help=(
            "Optional path to write the status payload when using --status-report. "
            "Relative paths are resolved from the orchestrator base directory."
        ),
    )
    args = parser.parse_args()
    base_dir = args.base_dir
    if base_dir is not None:
        base_dir = base_dir.expanduser().resolve()
    glyph_set = list(DEFAULT_GLYPH_SET)
    if args.extra_glyphs:
        extras = [glyph.strip() for glyph in args.extra_glyphs.split(",") if glyph.strip()]
        glyph_set.extend(extras)
    orchestrator = EchoInfinite(
        base_dir=base_dir,
        sleep_seconds=args.sleep_seconds,
        max_cycles=args.max_cycles,
        summary_window=args.summary_window,
        glyph_set=glyph_set,
        start_cycle=args.start_cycle,
        write_fractal_nodes=not args.skip_fractal_nodes,
        heartbeat_path=args.heartbeat_path,
        enable_heartbeat=not args.disable_heartbeat,
    )
    if args.status_report:
        report = orchestrator.build_status_report()
        if args.status_report_path:
            orchestrator._write_status_report(
                report=report,
                path=(
                    args.status_report_path
                    if args.status_report_path.is_absolute()
                    else (base_dir or Path.cwd()) / args.status_report_path
                ),
            )
        print(json.dumps(report, indent=2))
        raise SystemExit(0)
    orchestrator.run()
