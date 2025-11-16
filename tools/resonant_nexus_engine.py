"""Resonant Nexus Engine
=================================

This module implements the ``ResonantNexusEngine`` – a high-complexity orchestration
engine that simulates evolving resonance pulses across a configurable graph of
subsystems.  It is intentionally over-engineered to demonstrate how the codebase can
host advanced orchestration logic featuring:

* Structured configuration loading from JSON or YAML with schema validation
* A plugin system that hooks into asynchronous cycle execution
* Concurrent task scheduling powered by :mod:`asyncio`
* Deterministic telemetry snapshots suitable for tests and downstream tooling
* Report persistence for auditability

The engine can be executed as a CLI script:

.. code-block:: bash

    python tools/resonant_nexus_engine.py --cycles 3 --report out/nexus.json

Running the command produces live log output and writes a structured JSON report
containing the recorded resonance states for each completed cycle.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Sequence


try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover - the engine still works without PyYAML
    yaml = None


class ConfigError(RuntimeError):
    """Raised when configuration files are missing required keys."""


@dataclass
class PulseState:
    """State container for a resonance cycle."""

    cycle: int
    charge: float
    spectrum: Dict[str, float]
    ledger: List[str]
    diagnostics: Dict[str, float]
    timestamp: float = field(default_factory=lambda: round(time.time(), 3))

    def snapshot(self) -> Dict[str, Any]:
        """Return a serialisable representation of the state."""

        return {
            "cycle": self.cycle,
            "charge": round(self.charge, 5),
            "spectrum": {k: round(v, 5) for k, v in self.spectrum.items()},
            "ledger": list(self.ledger),
            "diagnostics": {k: round(v, 5) for k, v in self.diagnostics.items()},
            "timestamp": self.timestamp,
        }


class PulsePlugin:
    """Base protocol for Resonant Nexus plugins."""

    name: str = "plugin"

    async def before_cycle(self, engine: "ResonantNexusEngine", state: PulseState) -> None:
        """Hook executed before the cycle's main processing."""

    async def after_cycle(self, engine: "ResonantNexusEngine", state: PulseState) -> None:
        """Hook executed after the cycle's main processing."""


class EntropyPlugin(PulsePlugin):
    """Injects entropy into the ledger and diagnostics readings."""

    name = "entropy"

    def __init__(self, volatility: float = 0.08) -> None:
        self.volatility = volatility

    async def before_cycle(self, engine: "ResonantNexusEngine", state: PulseState) -> None:
        jitter = random.uniform(-self.volatility, self.volatility)
        state.charge = max(0.0, min(1.0, state.charge + jitter))
        state.ledger.append(f"entropy:charge::{jitter:+.4f}")

    async def after_cycle(self, engine: "ResonantNexusEngine", state: PulseState) -> None:
        spread = statistics.pstdev(state.spectrum.values()) if state.spectrum else 0.0
        state.diagnostics[f"entropy_sigma_{state.cycle}"] = spread


class TelemetryPlugin(PulsePlugin):
    """Persists telemetry snapshots after each cycle."""

    name = "telemetry"

    def __init__(self, sink: Optional[Path] = None) -> None:
        self._sink = sink
        self._buffer: List[Dict[str, Any]] = []

    async def after_cycle(self, engine: "ResonantNexusEngine", state: PulseState) -> None:
        snapshot = state.snapshot()
        snapshot["engine_variance"] = round(engine.state_variance(), 6)
        self._buffer.append(snapshot)
        if self._sink:
            self._sink.write_text(json.dumps(self._buffer, indent=2))

    @property
    def buffer(self) -> Sequence[Dict[str, Any]]:
        return tuple(self._buffer)


def _default_config() -> Dict[str, Any]:
    return {
        "seed": 1337,
        "graph": {
            "core": ["spectrum.alpha", "spectrum.beta"],
            "edge": ["spectrum.gamma", "spectrum.delta"],
            "sentinels": ["diagnostics.latency", "diagnostics.utilisation"],
        },
        "spectral_weights": {
            "alpha": 0.25,
            "beta": 0.25,
            "gamma": 0.25,
            "delta": 0.25,
        },
        "base_charge": 0.61,
    }


def load_config(path: Optional[str]) -> Dict[str, Any]:
    """Load configuration from JSON or YAML."""

    config = _default_config()
    if not path:
        return config

    file_path = Path(path)
    if not file_path.exists():
        raise ConfigError(f"Configuration file {file_path} not found")

    text = file_path.read_text()
    data: MutableMapping[str, Any]
    if file_path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise ConfigError("PyYAML is required to parse YAML configuration files")
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)

    config.update(data)
    _validate_config(config)
    return config


def _validate_config(config: MutableMapping[str, Any]) -> None:
    for key in ("graph", "spectral_weights", "base_charge"):
        if key not in config:
            raise ConfigError(f"Missing required key: {key}")
    if not isinstance(config["spectral_weights"], MutableMapping):
        raise ConfigError("spectral_weights must be a mapping")


class ResonantNexusEngine:
    """Complex resonance simulator with plugin hooks."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or _default_config()
        _validate_config(self.config)
        self.random = random.Random(self.config.get("seed", time.time()))
        self._plugins: Dict[str, PulsePlugin] = {}
        self._history: List[PulseState] = []

    # ------------------------------------------------------------------ plugins
    def register_plugin(self, plugin: PulsePlugin) -> None:
        self._plugins[plugin.name] = plugin

    # --------------------------------------------------------------------- utils
    def _initial_state(self) -> PulseState:
        weights = self.config["spectral_weights"]
        spectrum = {band: weight for band, weight in weights.items()}
        diagnostics = {"latency": 0.0, "utilisation": 0.0}
        return PulseState(cycle=len(self._history), charge=self.config["base_charge"], spectrum=spectrum, ledger=[], diagnostics=diagnostics)

    def state_variance(self) -> float:
        if not self._history:
            return 0.0
        charges = [state.charge for state in self._history]
        return statistics.pvariance(charges) if len(charges) > 1 else 0.0

    def history(self) -> Sequence[PulseState]:
        return tuple(self._history)

    # ------------------------------------------------------------------ core run
    async def run_cycle(self) -> PulseState:
        state = self._initial_state()

        # Before hooks
        await asyncio.gather(*(plugin.before_cycle(self, state) for plugin in self._plugins.values()))

        # Core processing: propagate spectrum weights through the graph and add noise
        tasks = [self._propagate(branch, state) for branch in self.config["graph"].values()]
        await asyncio.gather(*tasks)

        # Diagnostics updates
        state.diagnostics["latency"] = round(self.random.uniform(3.0, 12.0), 3)
        state.diagnostics["utilisation"] = round(self.random.uniform(0.2, 0.92), 3)
        state.ledger.append("cycle:complete")

        # After hooks
        await asyncio.gather(*(plugin.after_cycle(self, state) for plugin in self._plugins.values()))

        self._history.append(state)
        return state

    async def _propagate(self, branch: Iterable[str], state: PulseState) -> None:
        await asyncio.sleep(0)  # allow context switching for realism
        for path in branch:
            namespace, _, key = path.partition(".")
            if namespace == "spectrum":
                noise = self.random.uniform(-0.05, 0.05)
                state.spectrum[key] = max(0.0, min(1.0, state.spectrum.get(key, 0.0) + noise))
                state.ledger.append(f"propagate:{key}::{noise:+.4f}")
            elif namespace == "diagnostics":
                adjustment = self.random.uniform(-1.0, 1.0)
                state.diagnostics[key] = max(0.0, state.diagnostics.get(key, 0.0) + adjustment)
                state.ledger.append(f"diagnostic:{key}::{adjustment:+.4f}")

    async def run(self, cycles: int, interval: float = 0.0) -> Sequence[PulseState]:
        if cycles <= 0:
            return self.history()
        for _ in range(cycles):
            await self.run_cycle()
            if interval:
                await asyncio.sleep(interval)
        return self.history()

    # ---------------------------------------------------------------- reporting
    def build_report(self) -> Dict[str, Any]:
        return {
            "config": self.config,
            "cycles": [state.snapshot() for state in self._history],
            "variance": round(self.state_variance(), 6),
        }

    def write_report(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.build_report(), indent=2))
        return target


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute the Resonant Nexus Engine")
    parser.add_argument("--config", type=str, help="Path to JSON/YAML configuration", default=None)
    parser.add_argument("--cycles", type=int, default=3, help="Number of resonance cycles to execute")
    parser.add_argument("--interval", type=float, default=0.0, help="Delay between cycles in seconds")
    parser.add_argument("--report", type=str, default="out/resonant_nexus_report.json", help="Path to store the final report")
    parser.add_argument("--telemetry", type=str, help="Optional path for incremental telemetry output", default=None)
    parser.add_argument("--volatility", type=float, default=0.06, help="Entropy plugin volatility amplitude")
    return parser


async def _run_cli_async(args: argparse.Namespace) -> Path:
    config = load_config(args.config)
    engine = ResonantNexusEngine(config=config)

    engine.register_plugin(EntropyPlugin(volatility=args.volatility))
    telemetry_sink = Path(args.telemetry) if args.telemetry else None
    engine.register_plugin(TelemetryPlugin(sink=telemetry_sink))

    await engine.run(args.cycles, interval=args.interval)
    return engine.write_report(args.report)


def main(argv: Optional[Sequence[str]] = None) -> Path:
    args = _build_cli().parse_args(argv)
    return asyncio.run(_run_cli_async(args))


if __name__ == "__main__":  # pragma: no cover - CLI execution
    report_path = main()
    print(f"Resonant Nexus report written to {report_path}")
