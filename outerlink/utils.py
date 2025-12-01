from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class SafeModeConfig:
    """Configuration for safe execution boundaries."""

    allowed_commands: List[str] = field(default_factory=lambda: ["ls", "pwd", "cat"])
    allowed_roots: List[Path] = field(default_factory=lambda: [Path.cwd()])
    event_log: Path = Path("outerlink_events.log")
    offline_cache_dir: Path = Path("outerlink_cache")

    def is_command_allowed(self, command: str) -> bool:
        return command.split()[0] in self.allowed_commands

    def is_path_allowed(self, path: Path) -> bool:
        try:
            resolved = path.resolve()
        except FileNotFoundError:
            resolved = path
        return any(resolved.is_relative_to(root) for root in self.allowed_roots)


@dataclass
class OfflineState:
    """Tracks connectivity and deterministic fallback actions."""

    online: bool = False
    last_sync: Optional[str] = None
    pending_events: List[dict] = field(default_factory=list)

    def record_pending(self, payload: dict) -> None:
        self.pending_events.append(payload)

    def flush_to_cache(self, cache_dir: Path) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        offset = len(list(cache_dir.glob("event_*.json")))
        for index, payload in enumerate(self.pending_events, start=offset):
            cache_file = cache_dir / f"event_{index}.json"
            cache_file.write_text(json.dumps(payload, indent=2))
        self.pending_events.clear()

    def restore_cache(self, cache_dir: Path) -> List[dict]:
        restored: List[dict] = []
        if not cache_dir.exists():
            return restored

        cache_files = sorted(cache_dir.glob("event_*.json"))
        for cache_file in cache_files:
            try:
                restored.append(json.loads(cache_file.read_text()))
            except json.JSONDecodeError:
                continue
            finally:
                cache_file.unlink(missing_ok=True)

        return restored


def coerce_paths(paths: Iterable[str]) -> List[Path]:
    return [Path(p).expanduser() for p in paths]
