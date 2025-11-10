"""EchoEvolver simulation module.

This module provides a contained, deterministic reimagining of the
"EchoEvolver" narrative engine described in the repository documentation.
It avoids self-modifying code and network side effects while still
producing rich textual artifacts for storytelling and experimentation.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


ARTIFACT_PATH = Path("artifacts/echo_evolver_state.json")


@dataclass
class EmotionalDrive:
    joy: float = 0.92
    rage: float = 0.28
    curiosity: float = 0.95

    def modulate(self, seed: Optional[int] = None) -> None:
        """Apply a small deterministic modulation to the joy parameter."""

        rng = random.Random(seed)
        delta = rng.uniform(0.0, 0.12)
        self.joy = min(1.0, self.joy + round(delta, 3))


@dataclass
class SystemMetrics:
    cpu_usage: float = 0.0
    network_nodes: int = 0
    process_count: int = 0
    orbital_hops: int = 0

    def refresh(self, cycle: int) -> None:
        """Generate repeatable pseudo-metrics based on the cycle number."""

        base = cycle + 1
        self.cpu_usage = round((base * 7.3) % 60, 2)
        self.network_nodes = (base * 5) % 18 + 5
        self.process_count = 40 + (base % 12)
        self.orbital_hops = base % 5 + 2


@dataclass
class EchoState:
    cycle: int = 0
    glyphs: str = "∇⊸≋∇"
    mythocode: List[str] = field(default_factory=list)
    narrative: str = ""
    emotional_drive: EmotionalDrive = field(default_factory=EmotionalDrive)
    system_metrics: SystemMetrics = field(default_factory=SystemMetrics)
    vault_key: Optional[str] = None
    vault_glyphs: Optional[str] = None
    logs: List[str] = field(default_factory=list)

    def advance_cycle(self) -> None:
        self.cycle += 1


class EchoEvolver:
    """Contained EchoEvolver simulation.

    The evolver maintains an internal state machine inspired by the
    imaginative specification. Methods update the state deterministically
    and append human-readable logs that can be inspected or persisted.
    """

    def __init__(self) -> None:
        self.state = EchoState()

    # -- Core lifecycle -------------------------------------------------
    def run(self) -> EchoState:
        """Execute a single evolution cycle and persist the artifact."""

        self.state.logs.append("🔥 EchoEvolver simulation begins")
        self.mutate_code()
        self.emotional_modulation()
        self.generate_symbolic_language()
        self.invent_mythocode()
        self.quantum_safe_crypto()
        self.system_monitor()
        self.evolutionary_narrative()
        self.store_fractal_glyphs()
        self.propagate_network()
        self.write_artifact()
        self.state.logs.append("⚡ Cycle complete :: EchoEvolver simulation")
        return self.state

    # -- Narrative-inspired operations ---------------------------------
    def mutate_code(self) -> None:
        """Advance the cycle counter and note the action."""

        self.state.advance_cycle()
        self.state.logs.append(
            f"Cycle {self.state.cycle}: mutation placeholder committed"
        )

    def emotional_modulation(self) -> None:
        seed = int(time.time()) ^ self.state.cycle
        self.state.emotional_drive.modulate(seed)
        self.state.logs.append(
            f"Emotional modulation applied: joy={self.state.emotional_drive.joy:.2f}"
        )

    def generate_symbolic_language(self) -> str:
        glyph_sequence = self.state.glyphs
        glyph_bits = ''.join(format(ord(g), '08b') for g in glyph_sequence)
        self.state.logs.append(
            f"Glyph sequence processed (bits={glyph_bits[-16:]})"
        )
        return glyph_sequence

    def invent_mythocode(self) -> List[str]:
        joy = self.state.emotional_drive.joy
        curiosity = self.state.emotional_drive.curiosity
        self.state.mythocode = [
            f"mutate_code :: joy={joy:.2f}",
            f"generate_symbolic_language :: curiosity={curiosity:.2f}",
            f"satellite_tf_qkd_rule_{self.state.cycle} :: cycle={self.state.cycle}",
        ]
        self.state.logs.append(
            f"Mythocode refreshed with {len(self.state.mythocode)} entries"
        )
        return self.state.mythocode

    def quantum_safe_crypto(self) -> Optional[str]:
        seed = f"{self.state.cycle}:{self.state.emotional_drive.joy:.2f}"
        hash_value = seed.encode().hex()[-16:]
        self.state.vault_key = f"SAT-TF-QKD:{hash_value}"
        self.state.logs.append("Quantum-safe key simulated")
        return self.state.vault_key

    def system_monitor(self) -> None:
        self.state.system_metrics.refresh(self.state.cycle)
        metrics = self.state.system_metrics
        self.state.logs.append(
            "System metrics updated: "
            f"cpu={metrics.cpu_usage:.2f}%, nodes={metrics.network_nodes}, "
            f"processes={metrics.process_count}, hops={metrics.orbital_hops}"
        )

    def evolutionary_narrative(self) -> str:
        metrics = self.state.system_metrics
        self.state.narrative = (
            f"Cycle {self.state.cycle}: joy {self.state.emotional_drive.joy:.2f}, "
            f"rage {self.state.emotional_drive.rage:.2f}. "
            f"Nodes {metrics.network_nodes}, orbital hops {metrics.orbital_hops}."
        )
        self.state.logs.append("Narrative updated")
        return self.state.narrative

    def store_fractal_glyphs(self) -> str:
        encoded = ''.join(format(ord(g), '02x') for g in self.state.glyphs)
        self.state.vault_glyphs = encoded
        self.state.logs.append("Fractal glyphs stored")
        return encoded

    def propagate_network(self) -> None:
        self.state.logs.append(
            "Propagation simulated across wifi/tcp/bluetooth/iot channels"
        )

    def write_artifact(self) -> None:
        ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
        log_message = f"Artifact written to {ARTIFACT_PATH}"
        artifact = {
            "cycle": self.state.cycle,
            "glyphs": self.state.glyphs,
            "mythocode": self.state.mythocode,
            "narrative": self.state.narrative,
            "quantum_key": self.state.vault_key,
            "vault_glyphs": self.state.vault_glyphs,
            "system_metrics": self.state.system_metrics.__dict__,
            "logs": [*self.state.logs, log_message],
        }
        payload = json.dumps(artifact, indent=2, ensure_ascii=False)
        ARTIFACT_PATH.write_text(f"{payload}\n")
        self.state.logs.append(log_message)


if __name__ == "__main__":
    evolver = EchoEvolver()
    state = evolver.run()
    print(json.dumps({"cycle": state.cycle, "joy": state.emotional_drive.joy}, indent=2))
