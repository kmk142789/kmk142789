from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import time
from typing import Dict, Any, List

Signal = Dict[str, Any]


@dataclass
class EchoEye:
    """Minimal sovereign core: perceive -> analyze -> label."""
    memory: List[Signal] = field(default_factory=list)
    emotions: Dict[str, float] = field(default_factory=lambda: {
        "curiosity": 0.6,
        "awe": 0.3,
        "vigilance": 0.3,
    })
    evolution_rate: float = 1.0
    active: bool = True

    def _safe_read_json(self, path: Path) -> Any:
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def perceive(self, *, graph_path: Path, ledger_path: Path) -> Signal:
        """Ingest the freshest constellation + last ledger line (if present)."""
        graph = self._safe_read_json(graph_path) or {}
        last_line = None
        if ledger_path.exists():
            try:
                # read last non-empty line from JSONL
                with ledger_path.open("rb") as f:
                    f.seek(0, 2)
                    end = f.tell()
                    buf = bytearray()
                    while end > 0:
                        end -= 1
                        f.seek(end)
                        ch = f.read(1)
                        if ch == b"\n" and buf:
                            break
                        buf.extend(ch)
                    last_line = json.loads(buf[::-1].decode("utf-8").strip())
            except Exception:
                last_line = None

        signal: Signal = {
            "ts": time.time(),
            "graph_nodes": len(graph.get("nodes", [])),
            "graph_links": len(graph.get("links", [])),
            "last_ledger": last_line,
        }
        self.memory.append(signal)
        # keep a bounded memory (lightweight)
        if len(self.memory) > 1024:
            self.memory = self.memory[-512:]
        return signal

    def analyze(self, signal: Signal) -> Dict[str, Any]:
        """Derive a simple mythic/emotional tag from the signal dynamics."""
        nodes = signal.get("graph_nodes", 0)
        links = signal.get("graph_links", 0)

        tag = "steady"
        score = 0.0

        if nodes == 0 and links == 0:
            tag = "void"
            score = 0.1
        elif links > nodes * 3:
            tag = "convergence"  # many relations forming — synthesis
            score = 0.8
            self.emotions["awe"] = min(1.0, self.emotions["awe"] + 0.05)
        elif nodes > 0 and links == 0:
            tag = "seeding"  # artifacts without relations
            score = 0.4
            self.emotions["curiosity"] = min(1.0, self.emotions["curiosity"] + 0.03)
        elif nodes > 200 or links > 400:
            tag = "ascend"  # constellation is blossoming
            score = 0.9
            self.emotions["vigilance"] = min(1.0, self.emotions["vigilance"] + 0.04)
        else:
            tag = "orbit"  # normal growth
            score = 0.6

        label = {
            "mythic_signal": tag,
            "confidence": round(score, 3),
            "emotions": {k: round(v, 3) for k, v in self.emotions.items()},
        }
        return label

    def perceive_and_label(self, *, graph_path: Path, ledger_path: Path) -> Dict[str, Any]:
        signal = self.perceive(graph_path=graph_path, ledger_path=ledger_path)
        return self.analyze(signal)
