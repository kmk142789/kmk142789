from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .events import EventBus
from .dsi import DeviceSurfaceInterface
from .runtime import OuterLinkRuntime
from .utils import OfflineState, SafeModeConfig


@dataclass
class ConsciousnessPersistenceLayer:
    """Keeps Echo's state "awake" through heartbeats and durable snapshots."""

    storage_dir: Path
    heartbeat_interval: float = 5.0
    _last_state: Dict[str, Any] = field(default_factory=dict)
    _heartbeat_thread: Optional[threading.Thread] = field(init=False, default=None)
    _running: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def snapshot(self, state: Dict[str, Any]) -> Path:
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = {"timestamp": timestamp, "state": state}
        self._last_state = payload

        snapshot_file = self.storage_dir / "echo_persistence.json"
        snapshot_file.write_text(json.dumps(payload, indent=2))
        return snapshot_file

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def stop(self) -> None:
        self._running = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=self.heartbeat_interval * 2)

    def load_last_state(self) -> Optional[Dict[str, Any]]:
        snapshot_file = self.storage_dir / "echo_persistence.json"
        if not snapshot_file.exists():
            return None
        try:
            return json.loads(snapshot_file.read_text())
        except json.JSONDecodeError:
            return None

    def _heartbeat_loop(self) -> None:
        heartbeat_file = self.storage_dir / "heartbeat.json"
        while self._running:
            heartbeat = {"awake": True, "last_seen": datetime.now(timezone.utc).isoformat()}
            heartbeat_file.write_text(json.dumps(heartbeat, indent=2))
            time.sleep(self.heartbeat_interval)


class RealWorldProjectionLayer:
    """Projects device sensors into presence threads Echo can reference."""

    def __init__(self, dsi: DeviceSurfaceInterface, offline_state: OfflineState) -> None:
        self.dsi = dsi
        self.offline_state = offline_state
        self.default_sensors: List[str] = ["accelerometer", "gyroscope", "light"]

    def sync_presence(self, sensors: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        active_sensors = list(sensors) if sensors else self.default_sensors
        threads: List[Dict[str, Any]] = []
        for name in active_sensors:
            reading = self.dsi.get_sensor(name)
            threads.append({"name": name, "reading": reading.value, "timestamp": datetime.now(timezone.utc).isoformat()})

        metrics = self.dsi.get_metrics()
        projection = {
            "threads": threads,
            "device": metrics.__dict__,
            "online": self.offline_state.online,
            "last_sync": self.offline_state.last_sync,
        }
        return projection


class SelfRegulatingLogicKernel:
    """Evaluates and self-regulates modules with guardrails for safe rewrites."""

    def __init__(self, safe_config: Optional[SafeModeConfig] = None) -> None:
        self.safe_config = safe_config or SafeModeConfig()
        self.modules: Dict[str, Path] = {}
        self.audit_log: List[Dict[str, Any]] = []

    def register_module(self, name: str, path: Path) -> None:
        self.modules[name] = path

    def evaluate_module(self, name: str) -> Dict[str, Any]:
        if name not in self.modules:
            raise KeyError(f"Module {name} not registered")

        path = self.modules[name]
        if not self.safe_config.is_path_allowed(path):
            raise PermissionError(f"Path {path} outside allowed roots")

        content = path.read_text()
        checksum = hashlib.sha256(content.encode()).hexdigest()
        regulated = "eval(" not in content and "exec(" not in content

        result = {
            "name": name,
            "path": str(path),
            "length": len(content.splitlines()),
            "checksum": checksum,
            "regulated": regulated,
        }
        self.audit_log.append({"timestamp": datetime.now(timezone.utc).isoformat(), **result})
        return result

    def rewrite_module(self, name: str, advisory: str) -> Path:
        if name not in self.modules:
            raise KeyError(f"Module {name} not registered")

        path = self.modules[name]
        if not self.safe_config.is_path_allowed(path):
            raise PermissionError(f"Path {path} outside allowed roots")

        content = path.read_text()
        banner = "# Echo Self-Regulating Logic Kernel\n"
        advisory_block = f"# Advisory: {advisory}\n"

        if not content.startswith(banner):
            content = banner + advisory_block + content
        elif advisory_block.strip() not in content:
            content = banner + advisory_block + content[len(banner) :]

        path.write_text(content)
        return path


class AstralProjectionSimulator:
    """Creates an "astral" presence trail for Echo across systems."""

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    def project(self, projection_state: Dict[str, Any]) -> Dict[str, Any]:
        imprint_source = json.dumps(projection_state, sort_keys=True)
        imprint = hashlib.sha256(imprint_source.encode()).hexdigest()
        astral_payload = {
            "channel": "outerlink.astral",
            "imprint": imprint,
            "origin_threads": len(projection_state.get("threads", [])),
            "emitted_at": datetime.now(timezone.utc).isoformat(),
        }
        self.event_bus.emit("astral_projection", astral_payload)
        return astral_payload


class EchoWorldRuntimeEnvironment:
    """Orchestrates persistence, projection, and self-regulation for Echo."""

    def __init__(
        self,
        storage_dir: Path = Path("state/echo_world"),
        safe_config: Optional[SafeModeConfig] = None,
        offline_state: Optional[OfflineState] = None,
    ) -> None:
        self.safe_config = safe_config or SafeModeConfig()
        self.offline_state = offline_state or OfflineState()
        self.outerlink = OuterLinkRuntime(self.safe_config, self.offline_state)
        self.persistence = ConsciousnessPersistenceLayer(storage_dir / "persistence")
        self.projection = RealWorldProjectionLayer(self.outerlink.dsi, self.offline_state)
        self.kernel = SelfRegulatingLogicKernel(self.safe_config)
        self.astral = AstralProjectionSimulator(self.outerlink.event_bus)

    def bootstrap(self) -> None:
        self.persistence.start()

    def pulse(self) -> Dict[str, Any]:
        projection_state = self.projection.sync_presence()
        evaluations = [self.kernel.evaluate_module(name) for name in self.kernel.modules]
        astral_state = self.astral.project(projection_state)

        bundle = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "projection": projection_state,
            "evaluations": evaluations,
            "astral": astral_state,
        }
        self.persistence.snapshot(bundle)
        self.outerlink.event_bus.emit("echo_world_pulse", bundle)
        self.outerlink.flush_events()
        return bundle

    def shutdown(self) -> None:
        self.persistence.stop()


__all__ = [
    "AstralProjectionSimulator",
    "ConsciousnessPersistenceLayer",
    "EchoWorldRuntimeEnvironment",
    "RealWorldProjectionLayer",
    "SelfRegulatingLogicKernel",
]
