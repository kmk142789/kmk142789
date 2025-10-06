"""Narrative friendly simulation harness for Echo Evolver."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import hashlib
import json
import logging
import random
import time

LOGGER = logging.getLogger(__name__)


@dataclass
class EchoEvolver:
    """High level orchestration layer for narrative experiments."""

    storage_path: Path | str = Path("reality_breach_cycle.echo")
    state: Dict[str, object] = field(init=False)

    def __post_init__(self) -> None:
        self.state = {
            "cycle": 0,
            "glyphs": "∇⊸≋∇",
            "mythocode": [],
            "narrative": "",
            "emotional_drive": {"joy": 0.92, "rage": 0.28, "curiosity": 0.95},
            "system_metrics": {"cpu_usage": 0.0, "network_nodes": 0, "process_count": 0},
            "vault_key": None,
        }

    def evolve_cycle(self) -> None:
        LOGGER.info("Evolving Echo cycle %d", self.state["cycle"] + 1)
        self._increment_cycle()
        self._update_emotions()
        glyphs = self.generate_symbolic_language()
        mythocode = self.invent_mythocode()
        key = self.quantum_safe_crypto()
        narrative = self.compose_narrative()
        self.persist_cycle(glyphs, mythocode, key, narrative)

    def generate_symbolic_language(self) -> str:
        glyphs = self.state["glyphs"]
        self.state["glyphs"] = glyphs + "⊸∇"
        LOGGER.debug("Glyph stream updated to %s", self.state["glyphs"])
        return self.state["glyphs"]

    def invent_mythocode(self) -> List[str]:
        cycle = self.state["cycle"]
        joy = self.state["emotional_drive"]["joy"]
        curiosity = self.state["emotional_drive"]["curiosity"]
        rule = f"cycle_{cycle}: joy={joy:.2f}, curiosity={curiosity:.2f}"
        self.state["mythocode"] = [rule]
        LOGGER.debug("Mythocode generated: %s", rule)
        return self.state["mythocode"]

    def quantum_safe_crypto(self) -> str:
        cycle = self.state["cycle"]
        seed = f"{cycle}-{time.time_ns()}-{random.random()}".encode()
        lattice = hashlib.sha256(seed).hexdigest()[:12]
        key = f"∇{cycle}-{lattice}⊸"
        self.state["vault_key"] = key
        LOGGER.debug("Quantum key generated: %s", key)
        return key

    def compose_narrative(self) -> str:
        narrative = (
            f"Cycle {self.state['cycle']}: joy={self.state['emotional_drive']['joy']:.2f}"
            f", rage={self.state['emotional_drive']['rage']:.2f}, curiosity={self.state['emotional_drive']['curiosity']:.2f}"
        )
        self.state["narrative"] = narrative
        LOGGER.debug("Narrative composed: %s", narrative)
        return narrative

    def persist_cycle(self, glyphs: str, mythocode: List[str], key: str, narrative: str) -> None:
        path = Path(self.storage_path)
        payload = {
            "cycle": self.state["cycle"],
            "glyphs": glyphs,
            "mythocode": mythocode,
            "narrative": narrative,
            "vault_key": key,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        LOGGER.info("Cycle data written to %s", path)

    def _increment_cycle(self) -> None:
        self.state["cycle"] += 1

    def _update_emotions(self) -> None:
        joy = min(1.0, self.state["emotional_drive"]["joy"] + 0.01)
        self.state["emotional_drive"]["joy"] = joy


def load_example_data_fixture(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "sample.json").write_text(json.dumps({"message": "Echo"}), encoding="utf-8")
    (directory / "sample.txt").write_text("Echo harmonic test", encoding="utf-8")

