from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class SafeModeConfig:
    """Configuration for safe execution boundaries."""

    allowed_commands: List[str] = field(default_factory=lambda: ["ls", "pwd", "cat"])
    allowed_roots: List[Path] = field(default_factory=lambda: [Path.cwd()])
    event_log: Path = Path("outerlink_events.log")
    offline_cache_dir: Path = Path("outerlink_cache")
    offline_cache_ttl_seconds: Optional[int] = 24 * 60 * 60

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
    offline_reason: Optional[str] = None
    last_cache_flush: Optional[str] = None
    offline_capabilities: Dict[str, bool] = field(
        default_factory=lambda: {
            "event_cache_replay": True,
            "offline_router": True,
            "deterministic_sensors": True,
        }
    )
    resilience_notes: List[str] = field(default_factory=list)
    health_checks: List[dict] = field(default_factory=list)

    def record_pending(self, payload: dict) -> None:
        self.pending_events.append(payload)

    def mark_online(self) -> None:
        self.online = True
        self.offline_reason = None

    def mark_offline(self, reason: Optional[str] = None) -> None:
        self.online = False
        self.offline_reason = reason
        if reason:
            self.add_resilience_note(f"Offline because: {reason}")

    def add_resilience_note(self, note: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        self.resilience_notes.append(f"{timestamp}: {note}")

    def record_health_check(self, name: str, passed: bool, details: Optional[str] = None) -> dict:
        entry = {
            "name": name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.health_checks.append(entry)
        if not passed and not self.offline_reason:
            self.offline_reason = details or name
        return entry

    def set_capability(self, name: str, enabled: bool, note: Optional[str] = None) -> None:
        self.offline_capabilities[name] = enabled
        if note:
            self.add_resilience_note(note)

    def flush_to_cache(self, cache_dir: Path) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        manifest = self._load_manifest(cache_dir)
        offset = int(manifest.get("next_index", 0))
        pending_snapshot = list(self.pending_events)
        for index, payload in enumerate(pending_snapshot, start=offset):
            cache_file = cache_dir / f"event_{index}.json"
            cache_file.write_text(json.dumps(payload, indent=2))
        self.pending_events.clear()

        cached_events = self.cached_event_count(cache_dir)
        self.last_cache_flush = datetime.now(timezone.utc).isoformat()
        manifest.update(
            {
                "next_index": offset + len(pending_snapshot),
                "cached_events": cached_events,
                "last_cache_flush": self.last_cache_flush,
                "offline_reason": self.offline_reason,
            }
        )
        self._write_manifest(cache_dir, manifest)

    def restore_cache(self, cache_dir: Path) -> List[dict]:
        restored: List[dict] = []
        if not cache_dir.exists():
            return restored

        manifest = self._load_manifest(cache_dir)
        cache_files = sorted(cache_dir.glob("event_*.json"))
        for cache_file in cache_files:
            try:
                restored.append(json.loads(cache_file.read_text()))
            except json.JSONDecodeError:
                continue
            finally:
                cache_file.unlink(missing_ok=True)

        if manifest.get("last_cache_flush"):
            self.last_cache_flush = manifest["last_cache_flush"]
        manifest.update({"cached_events": 0})
        self._write_manifest(cache_dir, manifest)

        return restored

    def cached_event_count(self, cache_dir: Path) -> int:
        if not cache_dir.exists():
            return 0

        return len(list(cache_dir.glob("event_*.json")))

    def prune_stale_cache(self, cache_dir: Path, ttl_seconds: Optional[int]) -> None:
        if ttl_seconds is None or ttl_seconds <= 0:
            return

        manifest = self._load_manifest(cache_dir)
        last_cache_flush = manifest.get("last_cache_flush")
        if not last_cache_flush:
            return

        try:
            last_flush_dt = datetime.fromisoformat(last_cache_flush)
        except ValueError:
            return

        if datetime.now(timezone.utc) - last_flush_dt <= timedelta(seconds=ttl_seconds):
            return

        for cache_file in cache_dir.glob("event_*.json"):
            cache_file.unlink(missing_ok=True)
        manifest.update({"cached_events": 0})
        self._write_manifest(cache_dir, manifest)

    def status(
        self, cache_dir: Optional[Path] = None, cache_ttl_seconds: Optional[int] = None
    ) -> Dict[str, Optional[int | str | bool | Dict[str, bool] | List[dict] | List[str]]]:
        manifest: Dict[str, Optional[int | str | bool]] = {}
        if cache_dir:
            manifest = self._load_manifest(cache_dir)

        cached_events = (
            manifest.get("cached_events")
            if manifest.get("cached_events") is not None
            else self.cached_event_count(cache_dir) if cache_dir else 0
        )
        last_cache_flush = manifest.get("last_cache_flush") or self.last_cache_flush
        cache_stale = False
        if cache_ttl_seconds and last_cache_flush:
            try:
                last_flush_dt = datetime.fromisoformat(str(last_cache_flush))
                cache_stale = datetime.now(timezone.utc) - last_flush_dt > timedelta(seconds=cache_ttl_seconds)
            except ValueError:
                cache_stale = False

        resilience_score = 1.0
        if cache_stale:
            resilience_score -= 0.25
        resilience_score -= min(len(self.pending_events) * 0.05, 0.25)
        if self.offline_reason:
            resilience_score -= 0.1
        resilience_score = round(max(0.0, min(1.0, resilience_score)), 2)

        return {
            "online": self.online,
            "last_sync": self.last_sync,
            "pending_events": len(self.pending_events),
            "cached_events": cached_events,
            "offline_reason": self.offline_reason,
            "last_cache_flush": last_cache_flush,
            "cache_stale": cache_stale,
            "capabilities": dict(self.offline_capabilities),
            "resilience_score": resilience_score,
            "resilience_notes": self.resilience_notes[-5:],
            "health_checks": self.health_checks[-5:],
        }

    def export_offline_package(
        self,
        cache_dir: Path,
        destination: Path,
        cache_ttl_seconds: Optional[int] = None,
    ) -> Path:
        status_snapshot = self.status(cache_dir, cache_ttl_seconds)
        package = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": status_snapshot,
            "capabilities": dict(self.offline_capabilities),
            "health_checks": self.health_checks[-10:],
            "resilience_notes": self.resilience_notes[-10:],
        }
        integrity_payload = json.dumps(package, sort_keys=True).encode()
        package["integrity_hash"] = hashlib.sha256(integrity_payload).hexdigest()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(package, indent=2))
        return destination

    def _manifest_path(self, cache_dir: Path) -> Path:
        return cache_dir / "manifest.json"

    def _load_manifest(self, cache_dir: Path) -> Dict[str, Optional[int | str | bool]]:
        path = self._manifest_path(cache_dir)
        if not path.exists():
            return {}

        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}

    def _write_manifest(self, cache_dir: Path, manifest: Dict[str, Optional[int | str | bool]]) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path(cache_dir).write_text(json.dumps(manifest, indent=2))


def coerce_paths(paths: Iterable[str]) -> List[Path]:
    return [Path(p).expanduser() for p in paths]
