"""Helpers for extending the Origin Capsule memory anchor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import List, MutableMapping

from ._paths import REPO_ROOT

DEFAULT_CAPSULE_PATH = REPO_ROOT / "reality_breach_∇_fusion_v4.echo.json"
_GLYPH_POOL = ("∇", "⊸", "≋", "∞", "✶", "🜂", "🜁", "🜃")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _glyph_stream(seed: str, count: int = 4) -> str:
    if not seed:
        seed = "echo"
    indices = [int(seed[i : i + 2], 16) if seed[i : i + 2] else 0 for i in range(0, min(len(seed), 16), 2)]
    if not indices:
        indices = [0]
    glyphs: List[str] = []
    for idx in range(count):
        glyphs.append(_GLYPH_POOL[indices[idx % len(indices)] % len(_GLYPH_POOL)])
    return "".join(glyphs)


@dataclass
class CapsuleEntry:
    commit: str
    message: str
    glyphs: str
    timestamp: str


class OriginCapsule:
    """Manage the Origin Capsule artefact on disk."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_CAPSULE_PATH
        self._data = self._load()

    # ------------------------------------------------------------------
    # persistence helpers
    # ------------------------------------------------------------------
    def _load(self) -> MutableMapping[str, object]:
        if not self.path.exists():
            return {"origin_memory": {"commits": []}}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"origin_memory": {"commits": []}}

    def save(self) -> None:
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def _commit_entries(self) -> List[MutableMapping[str, object]]:
        origin_memory = self._data.setdefault("origin_memory", {"commits": []})
        commits = origin_memory.setdefault("commits", [])
        if isinstance(commits, list):
            return commits  # type: ignore[return-value]
        fresh: List[MutableMapping[str, object]] = []
        origin_memory["commits"] = fresh
        return fresh

    def record_commit(
        self,
        commit: str,
        *,
        message: str,
        timestamp: datetime | None = None,
        glyphs: str | None = None,
    ) -> CapsuleEntry:
        entries = self._commit_entries()
        for existing in entries:
            if existing.get("commit") == commit:
                return CapsuleEntry(
                    commit=commit,
                    message=str(existing.get("message", message)),
                    glyphs=str(existing.get("glyphs", glyphs or "")),
                    timestamp=str(existing.get("timestamp", "")),
                )

        glyph_sequence = glyphs or _glyph_stream(commit)
        event_time = (timestamp or _utc_now()).astimezone(timezone.utc).isoformat()
        entry = {
            "commit": commit,
            "message": message,
            "glyphs": glyph_sequence,
            "timestamp": event_time,
        }
        entries.append(entry)
        self.save()
        return CapsuleEntry(commit=commit, message=message, glyphs=glyph_sequence, timestamp=event_time)


__all__ = ["OriginCapsule", "CapsuleEntry", "DEFAULT_CAPSULE_PATH"]

