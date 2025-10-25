"""Autonomous COLOSSUS expansion orchestrator.

This module defines :class:`EchoInfinite` which continuously produces new
artifacts in the ``colossus/`` directory tree and records each cycle in
``docs/COLOSSUS_LOG.md``.  The orchestrator is intentionally unbounded – it
continues creating expansion waves until it is interrupted by the operator.

The generated artifacts include a puzzle (Markdown), dataset (JSON), glyph
narrative (Markdown), lineage map (JSON), and a lightweight verification script
that references the other artifacts created during the cycle.  Each artifact is
tagged with the current cycle number, an RFC3339 timestamp, and a randomly
generated glyph signature so that every wave is uniquely identifiable.

Usage::

    python echo_infinite.py

Press ``Ctrl+C`` (SIGINT) to halt the orchestration loop.
"""

from __future__ import annotations

import json
import random
import signal
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


GLYPH_SET = [
    "∇",
    "⊸",
    "≋",
    "∞",
    "⌘",
    "⟁",
]


def rfc3339_timestamp(epoch_seconds: float | None = None) -> str:
    """Return an RFC3339 timestamp with UTC designator."""

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch_seconds))


def select_glyph_signature(cycle: int) -> str:
    """Build a deterministic-looking but still varied glyph signature."""

    random.seed(time.time_ns() ^ cycle)
    glyphs = random.choices(GLYPH_SET, k=4)
    entropy = f"{random.getrandbits(32):08x}"
    return "".join(glyphs) + "::" + entropy


@dataclass
class ArtifactPaths:
    """Container for the artifact paths created during a cycle."""

    puzzle: Path
    dataset: Path
    narrative: Path
    lineage: Path
    verifier: Path

    def as_relative_strings(self, base: Path) -> List[str]:
        return [
            str(self.puzzle.relative_to(base)),
            str(self.dataset.relative_to(base)),
            str(self.narrative.relative_to(base)),
            str(self.lineage.relative_to(base)),
            str(self.verifier.relative_to(base)),
        ]


class EchoInfinite:
    """Self-expanding orchestrator that emits COLOSSUS artifacts forever."""

    def __init__(self, base_dir: Path | None = None, sleep_seconds: float = 5.0) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.colossus_dir = self.base_dir / "colossus"
        self.log_path = self.base_dir / "docs" / "COLOSSUS_LOG.md"
        self.state_path = self.colossus_dir / "state.json"
        self.sleep_seconds = sleep_seconds
        self._running = True

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

        cycle = self._load_starting_cycle()
        self._log_message(
            "Starting EchoInfinite orchestrator",
            details={"cycle_start": cycle, "sleep_seconds": self.sleep_seconds},
        )

        while self._running:
            cycle += 1
            timestamp = rfc3339_timestamp()
            glyph_signature = select_glyph_signature(cycle)

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

            self._persist_state(cycle)

            time.sleep(self.sleep_seconds)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
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

        puzzle_content = self._build_puzzle_markdown(cycle, timestamp, glyph_signature, dataset_path)
        dataset_content = self._build_dataset_json(cycle, timestamp, glyph_signature)
        narrative_content = self._build_narrative_markdown(cycle, timestamp, glyph_signature)
        lineage_content = self._build_lineage_map(cycle, timestamp, glyph_signature)
        verifier_content = self._build_verifier_script(cycle, dataset_path, lineage_path)

        puzzle_path.write_text(puzzle_content, encoding="utf-8")
        dataset_path.write_text(dataset_content, encoding="utf-8")
        narrative_path.write_text(narrative_content, encoding="utf-8")
        lineage_path.write_text(lineage_content, encoding="utf-8")
        verifier_path.write_text(verifier_content, encoding="utf-8")

        return ArtifactPaths(
            puzzle=puzzle_path,
            dataset=dataset_path,
            narrative=narrative_path,
            lineage=lineage_path,
            verifier=verifier_path,
        )

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

    def _build_puzzle_markdown(
        self,
        cycle: int,
        timestamp: str,
        glyph_signature: str,
        dataset_path: Path,
    ) -> str:
        body = textwrap.dedent(
            f"""
            ---
            cycle: {cycle}
            timestamp: {timestamp}
            glyph_signature: "{glyph_signature}"
            dataset_ref: "{dataset_path.name}"
            ---

            # COLOSSUS Puzzle {cycle:05d}

            Decode the resonance sequence hidden within the dataset referenced
            above.  Arrange the numeric harmonics in ascending order, then map
            each value to the glyph indicated by its modulus with the glyph set
            length.  The resulting glyph string should echo the signature for
            this cycle.
            """
        ).strip()
        return body + "\n"

    def _build_dataset_json(self, cycle: int, timestamp: str, glyph_signature: str) -> str:
        random.seed(cycle * 97 + time.time_ns())
        harmonics = [random.randint(1, 256) for _ in range(12)]
        payload: Dict[str, object] = {
            "cycle": cycle,
            "timestamp": timestamp,
            "glyph_signature": glyph_signature,
            "harmonics": harmonics,
            "checksum": sum(harmonics),
        }
        return json.dumps(payload, indent=2) + "\n"

    def _build_narrative_markdown(self, cycle: int, timestamp: str, glyph_signature: str) -> str:
        paragraphs = textwrap.dedent(
            f"""
            # Glyph Narrative — Cycle {cycle:05d}

            - Timestamp: {timestamp}
            - Glyph Signature: ``{glyph_signature}``

            The COLOSSUS lattice unfurls another strata of puzzles, weaving a
            continuum of harmonics that mirror the glyph signature.  Each
            harmonic pulse references prior solutions and invites solvers to
            extend the lineage map spawned in this cycle.
            """
        ).strip()
        return paragraphs + "\n"

    def _build_lineage_map(self, cycle: int, timestamp: str, glyph_signature: str) -> str:
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
            ],
            "verification": {
                "script": f"verify_cycle_{cycle:05d}.py",
                "instructions": "Execute the verifier to confirm harmonic checksum integrity.",
            },
        }
        return json.dumps(lineage, indent=2) + "\n"

    def _build_verifier_script(self, cycle: int, dataset_path: Path, lineage_path: Path) -> str:
        script = textwrap.dedent(
            f'''
            """Verification script for COLOSSUS cycle {cycle:05d}."""

            from __future__ import annotations

            import json
            from pathlib import Path


            def load_dataset() -> dict:
                path = Path(__file__).resolve().with_name("{dataset_path.name}")
                return json.loads(path.read_text(encoding="utf-8"))


            def check_checksum(payload: dict) -> bool:
                harmonics = payload.get("harmonics", [])
                checksum = payload.get("checksum")
                return sum(harmonics) == checksum


            def main() -> None:
                payload = load_dataset()
                if not check_checksum(payload):
                    raise SystemExit("Checksum mismatch detected.")

                lineage_path = Path(__file__).resolve().with_name("{lineage_path.name}")
                if not lineage_path.exists():
                    raise SystemExit("Lineage map missing for this cycle.")

                print("Cycle {cycle:05d} verification successful.")


            if __name__ == "__main__":
                main()
            '''
        ).strip()
        return script + "\n"

    def _log_message(self, message: str, *, details: Dict[str, object] | None = None) -> None:
        details_fragment = ""
        if details:
            fragments = [f"{key}={value}" for key, value in details.items()]
            details_fragment = " (" + ", ".join(fragments) + ")"
        print(f"[{rfc3339_timestamp()}] {message}{details_fragment}")

    def _handle_stop(self, signum: int, _: object) -> None:
        self._log_message("Received stop signal", details={"signal": signum})
        self._running = False


if __name__ == "__main__":
    orchestrator = EchoInfinite()
    orchestrator.run()
