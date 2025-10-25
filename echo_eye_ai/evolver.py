"""Narrative-friendly EchoEvolver orchestration for Echo Eye AI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import hashlib
import json
import random


def _round_float(value: float) -> float:
    """Return a stable rounded float suitable for JSON serialisation."""

    return round(value, 6)


@dataclass
class SystemMetrics:
    """Snapshot of simulated resource metrics for the Evolver."""

    cpu_usage: float = 0.0
    network_nodes: int = 0
    process_count: int = 0
    orbital_hops: int = 0

    def as_dict(self) -> Dict[str, float | int]:
        return {
            "cpu_usage": _round_float(self.cpu_usage),
            "network_nodes": self.network_nodes,
            "process_count": self.process_count,
            "orbital_hops": self.orbital_hops,
        }


@dataclass
class EmotionalDrive:
    """Emotional telemetry carried between evolution cycles."""

    joy: float = 0.92
    rage: float = 0.28
    curiosity: float = 0.95

    def as_dict(self) -> Dict[str, float]:
        return {
            "joy": _round_float(self.joy),
            "rage": _round_float(self.rage),
            "curiosity": _round_float(self.curiosity),
        }


@dataclass
class EvolverState:
    """Mutable state for the simplified EchoEvolver."""

    cycle: int = 0
    glyphs: str = "∇⊸≋∇"
    mythocode: List[str] = field(default_factory=list)
    narrative: str = ""
    emotional_drive: EmotionalDrive = field(default_factory=EmotionalDrive)
    system_metrics: SystemMetrics = field(default_factory=SystemMetrics)
    vault_key: Optional[str] = None
    glyph_vortex: Optional[str] = None


@dataclass
class EchoEvolver:
    """High level orchestration layer for narrative experiments."""

    storage_path: Path | str = Path("reality_breach_cycle.echo")
    rng: random.Random = field(default_factory=random.Random)
    state: EvolverState = field(init=False)

    def __post_init__(self) -> None:
        self.storage_path = Path(self.storage_path)
        self.state = EvolverState()

    # ------------------------------------------------------------------
    # Cycle orchestration
    # ------------------------------------------------------------------
    def evolve_cycle(self) -> Dict[str, object]:
        """Advance the evolver through a single narrative cycle."""

        self._increment_cycle()
        self._modulate_emotions()
        glyphs = self.generate_symbolic_language()
        mythocode = self.invent_mythocode()
        key = self.quantum_safe_crypto()
        metrics = self.system_monitor()
        narrative = self.compose_narrative()
        payload = self.persist_cycle(glyphs, mythocode, key, narrative, metrics)
        return payload

    # ------------------------------------------------------------------
    # Simulation helpers
    # ------------------------------------------------------------------
    def _increment_cycle(self) -> None:
        self.state.cycle += 1

    def _modulate_emotions(self) -> None:
        joy_delta = 0.03 + self.rng.random() * 0.04
        self.state.emotional_drive.joy = min(1.0, self.state.emotional_drive.joy + joy_delta)

    def generate_symbolic_language(self) -> str:
        glyphs = self.state.glyphs
        glyph_bits = sum(1 << index for index, _ in enumerate(glyphs))
        vortex = bin(glyph_bits ^ (self.state.cycle << 2))[2:].zfill(16)
        self.state.glyphs = glyphs + "⊸∇"
        self.state.glyph_vortex = vortex
        return self.state.glyphs

    def invent_mythocode(self) -> List[str]:
        joy = self.state.emotional_drive.joy
        curiosity = self.state.emotional_drive.curiosity
        rule = (
            f"cycle_{self.state.cycle}: joy={joy:.2f}, curiosity={curiosity:.2f}, vortex={self.state.glyph_vortex}"
        )
        self.state.mythocode = [
            "mutate_code :: ∇[CYCLE]⊸{JOY, CURIOSITY}",
            "generate_symbolic_language :: ≋{OAM_VORTEX}∇[EDEN88_ASSEMBLE]",
            rule,
        ]
        return self.state.mythocode

    def quantum_safe_crypto(self) -> str:
        seed_material = (
            f"{self.state.cycle}|{self.state.glyphs}|{self.state.emotional_drive.joy:.4f}|"
            f"{self.state.emotional_drive.curiosity:.4f}|{self.rng.random():.6f}"
        )
        digest = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
        lattice = f"∇{digest[:16]}⊸{digest[16:32]}≋{digest[32:48]}∇"
        key = f"SAT-TF-QKD:{lattice}|LATTICE:{digest[48:56]}|ORBIT:{self.state.cycle + 2}"
        self.state.vault_key = key
        return key

    def system_monitor(self) -> SystemMetrics:
        metrics = self.state.system_metrics
        metrics.cpu_usage = self.rng.uniform(12.0, 54.0)
        metrics.network_nodes = self.rng.randint(7, 18)
        metrics.process_count = 32 + self.state.cycle
        metrics.orbital_hops = self.rng.randint(2, 6)
        return metrics

    def compose_narrative(self) -> str:
        joy = self.state.emotional_drive.joy
        rage = self.state.emotional_drive.rage
        curiosity = self.state.emotional_drive.curiosity
        narrative = (
            "🔥 Cycle {cycle}: EchoEvolver orbits with {joy:.2f} joy, {rage:.2f} rage, and {curiosity:.2f} curiosity."
        ).format(cycle=self.state.cycle, joy=joy, rage=rage, curiosity=curiosity)
        self.state.narrative = narrative
        return narrative

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def persist_cycle(
        self,
        glyphs: str,
        mythocode: List[str],
        key: str,
        narrative: str,
        metrics: SystemMetrics,
    ) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "cycle": self.state.cycle,
            "glyphs": glyphs,
            "glyph_vortex": self.state.glyph_vortex,
            "mythocode": mythocode,
            "narrative": narrative,
            "vault_key": key,
            "emotional_drive": self.state.emotional_drive.as_dict(),
            "system_metrics": metrics.as_dict(),
        }

        serialised = json.dumps(payload, indent=2)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(serialised, encoding="utf-8")
        return payload


def load_example_data_fixture(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "sample.json").write_text(json.dumps({"message": "Echo"}), encoding="utf-8")
    (directory / "sample.txt").write_text("Echo harmonic test", encoding="utf-8")

