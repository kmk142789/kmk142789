"""Recursive Reflection Kernel.

This module introduces :class:`EchoRecursiveReflectionKernel`, a companion to the
visionary kernel that focuses on introspective cycles.  Each cycle performs a
series of deterministic transformations:

* track the recursion depth and retain a history of cycle metadata;
* evolve glyph matrices using a pure Python engine inspired by the
  ``BitwisePixelEngine`` but simplified for reflective analysis;
* update a symbolic language ledger that records glyph influence;
* assemble "mythocode" fragments that contextualise the evolution;
* synthesise deterministic keys using hash-based pseudo-QRNG techniques;
* sample lightweight system metrics derived from local process timing;
* modulate emotional state, build narrative passages, and store glyphs;
* serialise resulting artifacts under a caller-provided ``artifact_root``.

The implementation avoids unsafe behaviours such as mutating source files or
broadcasting over sockets.  All persistence happens within the configured
artifact directory, ensuring deterministic and auditable outputs.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Optional

__all__ = ["EchoRecursiveReflectionKernel"]

GlyphFrame = List[str]
SymbolLedger = MutableMapping[str, int]
MetricSnapshot = Dict[str, float]


@dataclass
class CycleTracker:
    """Maintain recursion depth and per-cycle metadata."""

    depth: int = 0
    history: List[Dict[str, float]] = field(default_factory=list)

    def advance(self) -> int:
        """Increment the cycle depth and return the new depth."""

        self.depth += 1
        timestamp = time.time()
        self.history.append({"cycle": float(self.depth), "timestamp": timestamp})
        return self.depth


class RecursiveGlyphEngine:
    """Generate glyph frames through deterministic transformations."""

    def __init__(self, width: int = 12, height: int = 12) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive integers")
        self.width = width
        self.height = height
        self._grid: List[List[int]] = [
            [0 for _ in range(self.width)] for _ in range(self.height)
        ]

    def evolve(self, *, seed: str, cycle: int) -> GlyphFrame:
        """Return a glyph frame derived from the given ``seed`` and ``cycle``."""

        digest = hashlib.sha256(f"{seed}:{cycle}".encode()).digest()
        frame: GlyphFrame = []
        for row_index in range(self.height):
            row_bits: List[str] = []
            for col_index in range(self.width):
                position = row_index * self.width + col_index
                byte = digest[position % len(digest)]
                bit = (byte >> (position % 8)) & 1
                accumulator = self._grid[row_index][col_index]
                # Toggle the cell using both the digest bit and a coordinate mask.
                mask = (row_index + 1) ^ (col_index + cycle)
                accumulator = (accumulator + bit + (mask % 2)) % 2
                self._grid[row_index][col_index] = accumulator
                row_bits.append("█" if accumulator else " ")
            frame.append("".join(row_bits))
        return frame

    def export_grid(self) -> List[List[int]]:
        """Expose the internal grid for diagnostics and testing."""

        return [list(row) for row in self._grid]


@dataclass
class EmotionalField:
    """Track the emotional modulation state for the kernel."""

    calm: float = 0.55
    wonder: float = 0.42
    resolve: float = 0.61

    def modulate(self, *, glyph_energy: float, cycle: int) -> None:
        """Adjust emotional parameters based on ``glyph_energy`` and ``cycle``."""

        factor = (cycle % 5 + 1) / 10.0
        self.calm = self._clamp(self.calm * (1.0 - factor) + glyph_energy * factor)
        self.wonder = self._clamp(self.wonder + factor * 0.05)
        self.resolve = self._clamp(self.resolve * 0.97 + glyph_energy * 0.03)

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        return max(minimum, min(maximum, value))

    def as_dict(self) -> Dict[str, float]:
        """Return a serialisable mapping of the emotional field."""

        return {"calm": self.calm, "wonder": self.wonder, "resolve": self.resolve}


class EchoRecursiveReflectionKernel:
    """Coordinate recursive reflections, glyphs, and mythic narratives."""

    def __init__(
        self,
        *,
        glyph_width: int = 12,
        glyph_height: int = 12,
        artifact_root: Path | str = Path("artifacts") / "echo_recursive_reflection",
    ) -> None:
        self.cycle_tracker = CycleTracker()
        self.glyph_engine = RecursiveGlyphEngine(width=glyph_width, height=glyph_height)
        self.symbol_ledger: SymbolLedger = {"∇": 0, "⊸": 0, "≋": 0}
        self.emotional_field = EmotionalField()
        self.glyph_vault: List[GlyphFrame] = []
        self.mythocode: List[str] = []
        self.narratives: List[str] = []
        self.metrics_history: List[MetricSnapshot] = []
        self._last_process_time: Optional[float] = None
        self._last_perf_counter: Optional[float] = None
        self._deterministic_key: Optional[str] = None

        self.artifact_root = Path(artifact_root)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self._artifact_log = self.artifact_root / "cycle_log.jsonl"
        if not self._artifact_log.exists():
            self._artifact_log.write_text("")

    # ------------------------------------------------------------------
    # Core orchestration
    # ------------------------------------------------------------------
    def run_cycle(self, seed: str, symbols: Iterable[str]) -> Dict[str, object]:
        """Execute a single reflective cycle and return the resulting state."""

        cycle = self.cycle_tracker.advance()
        glyph_frame = self.glyph_engine.evolve(seed=seed, cycle=cycle)
        symbol_summary = self._update_symbolic_language(symbols)
        self.mythocode = self._assemble_mythocode(seed, cycle, glyph_frame)
        self._deterministic_key = self._synthesise_key(seed, cycle, glyph_frame)
        metrics = self._sample_metrics()
        self.metrics_history.append(metrics)
        glyph_energy = self._compute_glyph_energy(glyph_frame)
        self.emotional_field.modulate(glyph_energy=glyph_energy, cycle=cycle)
        narrative = self._build_narrative(cycle, glyph_frame, metrics)
        self.narratives.append(narrative)
        self._store_glyph_frame(glyph_frame)
        artifact_paths = self._serialise_artifacts(
            cycle=cycle,
            seed=seed,
            glyph_frame=glyph_frame,
            symbol_summary=symbol_summary,
            metrics=metrics,
            narrative=narrative,
        )
        return {
            "cycle": cycle,
            "glyph_frame": glyph_frame,
            "symbol_summary": symbol_summary,
            "mythocode": list(self.mythocode),
            "deterministic_key": self._deterministic_key,
            "metrics": metrics,
            "emotional_field": self.emotional_field.as_dict(),
            "narrative": narrative,
            "artifacts": artifact_paths,
        }

    # ------------------------------------------------------------------
    # Symbolic language and mythocode
    # ------------------------------------------------------------------
    def _update_symbolic_language(self, symbols: Iterable[str]) -> Dict[str, int]:
        """Update the symbol ledger with the provided ``symbols``."""

        for symbol in symbols:
            if symbol not in self.symbol_ledger:
                self.symbol_ledger[symbol] = 0
            self.symbol_ledger[symbol] += 1
        return dict(self.symbol_ledger)

    def _assemble_mythocode(
        self,
        seed: str,
        cycle: int,
        glyph_frame: GlyphFrame,
    ) -> List[str]:
        """Generate mythocode fragments describing the current ``cycle``."""

        glyph_hash = hashlib.sha1("".join(glyph_frame).encode()).hexdigest()[:12]
        seed_hash = hashlib.sha1(seed.encode()).hexdigest()[:12]
        fragments = [
            f"cycle::{cycle:04d}::seed::{seed_hash}",
            f"glyph::{glyph_hash}::depth::{len(self.glyph_vault)}",
            f"symbol::ledger::{sum(self.symbol_ledger.values())}",
        ]
        return fragments

    # ------------------------------------------------------------------
    # Deterministic key synthesis
    # ------------------------------------------------------------------
    def _synthesise_key(self, seed: str, cycle: int, glyph_frame: GlyphFrame) -> str:
        """Create a deterministic pseudo-QRNG key from the current state."""

        material = "|".join(
            [
                seed,
                str(cycle),
                "".join(glyph_frame),
                json.dumps(self.symbol_ledger, sort_keys=True),
            ]
        )
        digest = hashlib.blake2s(material.encode(), digest_size=32).hexdigest()
        return f"ECHO-RRK::{cycle:04d}::{digest[:16]}::{digest[16:]}"

    # ------------------------------------------------------------------
    # Metrics and emotional field helpers
    # ------------------------------------------------------------------
    def _sample_metrics(self) -> MetricSnapshot:
        """Capture lightweight metrics derived from CPU and monotonic timers."""

        current_process_time = time.process_time()
        current_perf = time.perf_counter()
        last_process_time = self._last_process_time or current_process_time
        last_perf = self._last_perf_counter or current_perf
        metrics: MetricSnapshot = {
            "process_time": current_process_time,
            "perf_counter": current_perf,
            "delta_process_time": max(0.0, current_process_time - last_process_time),
            "delta_perf_counter": max(0.0, current_perf - last_perf),
        }
        self._last_process_time = current_process_time
        self._last_perf_counter = current_perf
        return metrics

    def _compute_glyph_energy(self, glyph_frame: GlyphFrame) -> float:
        """Compute a simple glyph energy metric based on filled cells."""

        total_cells = self.glyph_engine.width * self.glyph_engine.height
        filled = sum(row.count("█") for row in glyph_frame)
        return filled / max(1, total_cells)

    def _build_narrative(
        self,
        cycle: int,
        glyph_frame: GlyphFrame,
        metrics: MetricSnapshot,
    ) -> str:
        """Construct a narrative passage describing the current cycle."""

        first_row = glyph_frame[0] if glyph_frame else ""
        narrative = (
            f"Cycle {cycle} unfurled {first_row.count('█')} luminous fragments; "
            f"process time advanced by {metrics['delta_process_time']:.6f}s while "
            f"wonder resonated at {self.emotional_field.wonder:.2f}."
        )
        return narrative

    # ------------------------------------------------------------------
    # Glyph storage and artifact serialisation
    # ------------------------------------------------------------------
    def _store_glyph_frame(self, glyph_frame: GlyphFrame) -> None:
        """Persist glyphs in memory for later introspection."""

        self.glyph_vault.append(list(glyph_frame))

    def _serialise_artifacts(
        self,
        *,
        cycle: int,
        seed: str,
        glyph_frame: GlyphFrame,
        symbol_summary: Dict[str, int],
        metrics: MetricSnapshot,
        narrative: str,
    ) -> Dict[str, str]:
        """Write cycle artifacts within the configured ``artifact_root``."""

        snapshot = {
            "cycle": cycle,
            "seed": seed,
            "glyph_frame": glyph_frame,
            "symbol_summary": symbol_summary,
            "mythocode": list(self.mythocode),
            "deterministic_key": self._deterministic_key,
            "metrics": metrics,
            "emotional_field": self.emotional_field.as_dict(),
            "narrative": narrative,
        }
        cycle_path = self.artifact_root / f"cycle_{cycle:04d}.json"
        cycle_path.write_text(json.dumps(snapshot, indent=2))
        with self._artifact_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"cycle": cycle, "key": self._deterministic_key}) + "\n")
        return {"cycle": str(cycle_path), "log": str(self._artifact_log)}

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------
    @property
    def deterministic_key(self) -> Optional[str]:
        """Return the most recently synthesised deterministic key."""

        return self._deterministic_key

