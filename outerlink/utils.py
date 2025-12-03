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
            "cache_integrity_checks": True,
            "resilience_reporting": True,
            "offline_bundle_export": True,
        }
    )
    resilience_notes: List[str] = field(default_factory=list)
    health_checks: List[dict] = field(default_factory=list)

    def record_pending(self, payload: dict) -> None:
        stamped = {**payload, "cached_at": datetime.now(timezone.utc).isoformat()}
        self.pending_events.append(stamped)

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

    def _is_cache_stale(self, last_cache_flush: Optional[str], cache_ttl_seconds: Optional[int]) -> bool:
        if cache_ttl_seconds and last_cache_flush:
            try:
                last_flush_dt = datetime.fromisoformat(str(last_cache_flush))
            except ValueError:
                return False
            return datetime.now(timezone.utc) - last_flush_dt > timedelta(seconds=cache_ttl_seconds)
        return False

    def _grade_resilience(self, score: float) -> str:
        if score >= 0.85:
            return "Prime"
        if score >= 0.65:
            return "Stable"
        if score >= 0.4:
            return "Watch"
        return "Critical"

    def _build_resilience_summary(
        self,
        score: float,
        grade: str,
        cached_events: int,
        pending_events: int,
        cache_stale: bool,
        replay_ready: bool,
        last_cache_flush: Optional[str],
    ) -> str:
        freshness = "fresh" if not cache_stale else "stale"
        replay_state = "ready" if replay_ready else "cold"
        return (
            f"Resilience score {score:.2f} ({grade}); cache {freshness}"
            f" with {cached_events} cached/{pending_events} pending; replay {replay_state}; "
            f"last cache flush: {last_cache_flush or 'unknown'}"
        )

    def capability_report(
        self,
        cache_dir: Optional[Path],
        cache_ttl_seconds: Optional[int],
        cached_events: int,
        cache_stale: bool,
        last_cache_flush: Optional[str],
    ) -> Dict[str, object]:
        cache_present = cache_dir.exists() if cache_dir else False
        pending_events = len(self.pending_events)
        health_failures = [hc for hc in self.health_checks if hc.get("passed") is False]
        replay_ready = cache_present and cached_events > 0 and not cache_stale

        score = 1.0
        score -= 0.2 if cache_stale else 0.0
        score -= 0.1 if not cache_present else 0.0
        score -= min(pending_events * 0.03, 0.2)
        score -= 0.05 if health_failures else 0.0
        score = round(max(0.0, min(1.0, score)), 2)
        grade = self._grade_resilience(score)
        summary = self._build_resilience_summary(
            score, grade, cached_events, pending_events, cache_stale, replay_ready, last_cache_flush
        )

        return {
            "cache_present": cache_present,
            "cache_stale": cache_stale,
            "cached_events": cached_events,
            "pending_events": pending_events,
            "replay_ready": replay_ready,
            "health_checks": len(self.health_checks),
            "health_failures": len(health_failures),
            "score": score,
            "grade": grade,
            "summary": summary,
            "last_cache_flush": last_cache_flush,
        }

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
        self.add_resilience_note(f"Cached {cached_events} events for offline replay")

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

        if restored:
            self.add_resilience_note(f"Restored {len(restored)} cached events for replay")

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

        if not self._is_cache_stale(last_cache_flush, ttl_seconds):
            return

        for cache_file in cache_dir.glob("event_*.json"):
            cache_file.unlink(missing_ok=True)
        manifest.update({"cached_events": 0})
        self._write_manifest(cache_dir, manifest)
        self.add_resilience_note("Stale offline cache pruned")

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
        cache_stale = self._is_cache_stale(last_cache_flush, cache_ttl_seconds)

        capability_report = self.capability_report(
            cache_dir, cache_ttl_seconds, cached_events, cache_stale, last_cache_flush
        )
        resilience_score = capability_report["score"]
        resilience_grade = capability_report["grade"]
        resilience_summary = capability_report["summary"]

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
            "resilience_grade": resilience_grade,
            "resilience_summary": resilience_summary,
            "resilience_notes": self.resilience_notes[-5:],
            "health_checks": self.health_checks[-5:],
            "capability_report": capability_report,
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
            "capability_report": status_snapshot.get("capability_report", {}),
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
