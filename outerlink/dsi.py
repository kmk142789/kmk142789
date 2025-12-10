from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import shutil

from .utils import SafeModeConfig


@dataclass
class SensorReading:
    name: str
    value: Dict[str, float]


@dataclass
class DeviceMetrics:
    battery: Optional[int]
    wifi_strength: Optional[int]
    bluetooth_enabled: bool
    storage_free_mb: Optional[int]


class DeviceSurfaceInterface:
    """Provides safe access to local files and lightweight device information."""

    def __init__(self, config: SafeModeConfig) -> None:
        self.config = config

    def read_file(self, path: Path) -> str:
        if not self.config.is_path_allowed(path):
            raise PermissionError(f"Access to {path} is outside allowed roots")
        return path.read_text()

    def write_file(self, path: Path, content: str) -> None:
        if not self.config.is_path_allowed(path):
            raise PermissionError(f"Access to {path} is outside allowed roots")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def get_sensor(self, name: str) -> SensorReading:
        # Stubbed sensor values suitable for offline mode.
        simulated = {
            "accelerometer": {"x": 0.0, "y": 0.0, "z": 9.81},
            "gyroscope": {"x": 0.01, "y": 0.02, "z": 0.03},
            "light": {"lux": 120.0},
        }
        data = simulated.get(name, {"value": 0.0})
        return SensorReading(name=name, value=data)

    def get_metrics(self) -> DeviceMetrics:
        # Lightweight metrics with placeholders for offline-first contexts.
        storage_free = None
        try:
            root = self.config.allowed_roots[0]
            usage = shutil.disk_usage(root)
            storage_free = int(usage.free / (1024 * 1024))
        except (OSError, IndexError):
            storage_free = None
        return DeviceMetrics(
            battery=None,
            wifi_strength=None,
            bluetooth_enabled=False,
            storage_free_mb=storage_free,
        )


__all__ = ["DeviceSurfaceInterface", "SensorReading", "DeviceMetrics"]
