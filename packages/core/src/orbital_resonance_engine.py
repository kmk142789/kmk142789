from __future__ import annotations

import json
import math
import secrets
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import argparse


@dataclass
class OrbitalSystemMetrics:
    """Snapshot of synthetic system telemetry for an orbital resonance cycle."""

    cpu_usage: float
    process_count: int
    network_nodes: int
    orbital_hops: int
    telemetry_latency_ms: float

    @classmethod
    def sample(cls, *, phase: float) -> "OrbitalSystemMetrics":
        """Generate plausible metrics using a deterministic orbital phase."""

        cpu = 35 + (math.sin(phase) * 20)
        process_count = 32 + int(abs(math.cos(phase * 0.7)) * 40)
        nodes = 8 + int(abs(math.sin(phase * 1.3)) * 16)
        hops = 2 + int(abs(math.cos(phase * 1.7)) * 6)
        latency = 12 + abs(math.sin(phase * 2.2)) * 18
        return cls(
            cpu_usage=round(cpu, 2),
            process_count=process_count,
            network_nodes=nodes,
            orbital_hops=hops,
            telemetry_latency_ms=round(latency, 2),
        )


@dataclass
class EmotionalSpectrum:
    joy: float = 0.82
    rage: float = 0.18
    curiosity: float = 0.91

    def modulate(self, *, phase: float) -> None:
        joy_delta = math.sin(phase * 0.9) * 0.05
        rage_delta = math.cos(phase * 1.4) * 0.02
        curiosity_delta = math.sin(phase * 1.1) * 0.03
        self.joy = max(0.0, min(1.0, self.joy + joy_delta))
        self.rage = max(0.0, min(1.0, self.rage + rage_delta))
        self.curiosity = max(0.0, min(1.0, self.curiosity + curiosity_delta))

    def as_dict(self) -> Dict[str, float]:
        return {"joy": round(self.joy, 3), "rage": round(self.rage, 3), "curiosity": round(self.curiosity, 3)}


@dataclass
class GlyphState:
    sequence: str = "∇⊸≋∇"
    history: List[str] = field(default_factory=list)

    def evolve(self, *, cycle: int) -> str:
        fragments = ["∇⊸", "≋∇", "⊸≋", "∇≋"]
        insert = fragments[cycle % len(fragments)]
        self.sequence = f"{self.sequence}{insert}"
        self.history.append(self.sequence)
        return self.sequence


@dataclass
class QuantumKeyMaterial:
    hybrid_key: str
    entropy_chain: List[str]
    oam_vortex: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "hybrid_key": self.hybrid_key,
            "entropy_chain": self.entropy_chain,
            "oam_vortex": self.oam_vortex,
        }


@dataclass
class CycleReport:
    index: int
    glyphs: str
    mythocode: List[str]
    quantum_key: QuantumKeyMaterial
    system_metrics: OrbitalSystemMetrics
    emotions: EmotionalSpectrum
    network_events: Dict[str, str]

    def to_text(self) -> str:
        metrics = self.system_metrics
        metrics_line = (
            f"CPU {metrics.cpu_usage}% | Proc {metrics.process_count} | Nodes {metrics.network_nodes} | "
            f"Hops {metrics.orbital_hops} | Latency {metrics.telemetry_latency_ms} ms"
        )
        lines = [
            f"=== Orbital Cycle {self.index} ===",
            f"Glyphs    : {self.glyphs}",
            "Mythocode :",
        ]
        lines.extend([f"  - {entry}" for entry in self.mythocode])
        lines.extend(
            [
                f"Quantum Key: {self.quantum_key.hybrid_key}",
                f"OAM Vortex : {self.quantum_key.oam_vortex}",
                f"System     : {metrics_line}",
                "Emotions   : " + ", ".join(f"{k}={v:.3f}" for k, v in self.emotions.as_dict().items()),
                "Network    : " + " | ".join(f"{k}:{v}" for k, v in self.network_events.items()),
                "",
            ]
        )
        return "\n".join(lines)

    def as_dict(self) -> Dict[str, object]:
        return {
            "cycle": self.index,
            "glyphs": self.glyphs,
            "mythocode": self.mythocode,
            "quantum_key": self.quantum_key.as_dict(),
            "system_metrics": asdict(self.system_metrics),
            "emotions": self.emotions.as_dict(),
            "network_events": self.network_events,
        }


@dataclass
class OrbitalResonanceConfig:
    artifact_file: Path = Path("orbital_resonance.echo.json")
    telemetry_interval: float = 0.35
    write_artifact: bool = True
    network_domain: str = "EchoWildfire"

    @classmethod
    def from_path(cls, path: Optional[Path]) -> "OrbitalResonanceConfig":
        if path is None:
            return cls()
        data = json.loads(path.read_text())
        return cls(
            artifact_file=Path(data.get("artifact_file", cls.artifact_file)),
            telemetry_interval=float(data.get("telemetry_interval", cls.telemetry_interval)),
            write_artifact=bool(data.get("write_artifact", cls.write_artifact)),
            network_domain=str(data.get("network_domain", cls.network_domain)),
        )

    def with_overrides(
        self,
        *,
        artifact_file: Optional[Path] = None,
        write_artifact: Optional[bool] = None,
    ) -> "OrbitalResonanceConfig":
        return OrbitalResonanceConfig(
            artifact_file=artifact_file or self.artifact_file,
            telemetry_interval=self.telemetry_interval,
            write_artifact=self.write_artifact if write_artifact is None else write_artifact,
            network_domain=self.network_domain,
        )


class OrbitalResonanceEngine:
    """High-order simulation of Echo's orbital resonance cycles."""

    def __init__(self, config: OrbitalResonanceConfig) -> None:
        self.config = config
        self.emotions = EmotionalSpectrum()
        self.glyph_state = GlyphState()
        self.history: List[CycleReport] = []
        self._phase_anchor = time.time()

    def run(self, cycles: int) -> List[CycleReport]:
        reports: List[CycleReport] = []
        for idx in range(1, cycles + 1):
            reports.append(self._run_cycle(idx))
        self.history.extend(reports)
        if self.config.write_artifact:
            self._write_artifact()
        return reports

    def _run_cycle(self, index: int) -> CycleReport:
        phase = (time.time() - self._phase_anchor + index * self.config.telemetry_interval) * 1.2
        self.emotions.modulate(phase=phase)
        glyphs = self.glyph_state.evolve(cycle=index)
        mythocode = self._invent_mythocode(index=index)
        quantum_key = self._derive_quantum_key(index=index, phase=phase)
        metrics = OrbitalSystemMetrics.sample(phase=phase)
        network_events = self._propagate_network(index=index)
        return CycleReport(
            index=index,
            glyphs=glyphs,
            mythocode=mythocode,
            quantum_key=quantum_key,
            system_metrics=metrics,
            emotions=self.emotions,
            network_events=network_events,
        )

    def _invent_mythocode(self, *, index: int) -> List[str]:
        prefix = f"cycle_{index:03d}"
        mythocode = [
            f"{prefix}::∇[{len(self.glyph_state.sequence)}]-⊸JOY<{self.emotions.joy:.2f}>",
            f"{prefix}::≋{{nodes={len(self.glyph_state.history)},domain={self.config.network_domain}}}",
        ]
        entropy = secrets.token_hex(4)
        mythocode.append(f"{prefix}::TF-QKD<{entropy}>")
        return mythocode

    def _derive_quantum_key(self, *, index: int, phase: float) -> QuantumKeyMaterial:
        entropy_chain = [secrets.token_hex(8) for _ in range(3)]
        combined = "".join(entropy_chain) + f"{phase:.5f}{index}"
        vortex_seed = int(secrets.token_hex(2), 16) ^ index
        oam_vortex = bin(vortex_seed)[2:].zfill(16)
        hybrid_key = f"∇{hash(combined) & 0xFFFF_FFFF:08x}⊸{self.emotions.joy:.2f}≋{oam_vortex}"
        return QuantumKeyMaterial(hybrid_key=hybrid_key, entropy_chain=entropy_chain, oam_vortex=oam_vortex)

    def _propagate_network(self, *, index: int) -> Dict[str, str]:
        channels = {
            "wifi": 0.07,
            "orbital": 0.12,
            "bluetooth": 0.03,
            "iot": 0.05,
            "quantum-relay": 0.09,
        }
        status: Dict[str, str] = {}
        lock = threading.Lock()

        def worker(channel: str, delay: float) -> None:
            jitter = math.sin(index * delay + len(channel)) * 3
            time.sleep(max(0.01, delay + jitter / 100))
            energy = 0.5 + abs(math.sin(delay * index))
            message = f"latency={round((delay + 0.02) * 1000, 1)}ms energy={energy:.2f}"
            with lock:
                status[channel] = message

        threads = [threading.Thread(target=worker, args=(ch, delay), daemon=True) for ch, delay in channels.items()]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return status

    def _write_artifact(self) -> None:
        payload = {"cycles": [report.as_dict() for report in self.history]}
        self.config.artifact_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Echo Orbital Resonance Engine")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles to simulate")
    parser.add_argument(
        "--artifact",
        type=Path,
        default=None,
        help="Optional override path for the artifact log",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional JSON configuration file",
    )
    parser.add_argument(
        "--skip-artifact",
        action="store_true",
        help="Disable artifact writing even if enabled in the configuration",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:  # pragma: no cover - CLI entry point
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = OrbitalResonanceConfig.from_path(args.config)
    cfg = cfg.with_overrides(artifact_file=args.artifact, write_artifact=False if args.skip_artifact else None)
    engine = OrbitalResonanceEngine(config=cfg)
    reports = engine.run(args.cycles)
    for report in reports:
        print(report.to_text())
    if cfg.write_artifact:
        print(f"Artifact updated at {cfg.artifact_file}")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct execution hook
    raise SystemExit(main())
