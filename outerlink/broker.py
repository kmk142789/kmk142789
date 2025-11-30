from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .dsi import DeviceSurfaceInterface
from .events import EventBus
from .utils import OfflineState, SafeModeConfig


@dataclass
class SafeExecutionResult:
    command: str
    stdout: str
    stderr: str
    returncode: int

    def to_json(self) -> str:
        return json.dumps(
            {
                "command": self.command,
                "stdout": self.stdout,
                "stderr": self.stderr,
                "returncode": self.returncode,
            }
        )


class ExecutionBroker:
    """Dispatches external commands through safe-mode rules and DSI helpers."""

    def __init__(
        self,
        config: SafeModeConfig,
        dsi: DeviceSurfaceInterface,
        event_bus: EventBus,
        offline_state: OfflineState,
    ) -> None:
        self.config = config
        self.dsi = dsi
        self.event_bus = event_bus
        self.offline_state = offline_state

    def run_shell(self, command: str, args: Optional[List[str]] = None) -> SafeExecutionResult:
        args = args or []
        executable = " ".join([command] + args).strip()
        if not self.config.is_command_allowed(command):
            raise PermissionError(f"Command '{command}' is not permitted in safe mode")
        completed = subprocess.run(
            [command, *args],
            capture_output=True,
            text=True,
            check=False,
        )
        result = SafeExecutionResult(
            command=executable,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )
        self._emit("shell_executed", result)
        return result

    def read_file(self, path: Path) -> str:
        content = self.dsi.read_file(path)
        self._emit("file_read", {"path": str(path)})
        return content

    def write_config(self, path: Path, content: Dict[str, str]) -> None:
        serialized = json.dumps(content, indent=2)
        self.dsi.write_file(path, serialized)
        self._emit("config_written", {"path": str(path)})

    def get_sensor(self, name: str) -> Dict[str, float]:
        reading = self.dsi.get_sensor(name)
        payload = {"name": reading.name, **reading.value}
        self._emit("sensor_sampled", payload)
        return reading.value

    def _emit(self, name: str, payload: Dict[str, str | int | float]) -> None:
        event = self.event_bus.emit(name, payload)
        if self.offline_state.online:
            log_line = json.dumps(event.to_dict())
            self.config.event_log.parent.mkdir(parents=True, exist_ok=True)
            with self.config.event_log.open("a", encoding="utf-8") as handle:
                handle.write(log_line + "\n")
        else:
            self.offline_state.record_pending(event.to_dict())


__all__ = ["ExecutionBroker", "SafeExecutionResult"]
