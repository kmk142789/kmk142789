"""Realtime registry synchronisation utilities.

This module provides helpers for converting webhook events into structured
registry updates.  It understands conventional commit prefixes such as
``feat:``, ``fix:`` and ``chore:`` so incoming pushes can be translated into
semantic registry entries without waiting for scheduled jobs.

The implementation is intentionally self-contained so both FastAPI routes and
standalone scripts (or tests) can reuse the same primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Optional

from ._paths import REPO_ROOT
from .origin_capsule import OriginCapsule

REGISTRY_PATH = REPO_ROOT / "registry.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_timestamp(value: str | None) -> datetime:
    if value is None:
        return _utc_now()
    try:
        normalised = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalised)
    except ValueError:
        return _utc_now()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class CommitSummary:
    category: str
    title: str
    scope: Optional[str] = None


class CommitClassifier:
    """Turn commit messages into semantic labels."""

    _PATTERN = re.compile(r"^(?P<kind>feat|fix|chore)(?:\((?P<scope>[^)]+)\))?:\s*(?P<title>.+)", re.IGNORECASE)
    _CATEGORY_MAP = {"feat": "feature", "fix": "bugfix", "chore": "maintenance"}

    def classify(self, message: str) -> CommitSummary:
        if not message:
            return CommitSummary(category="update", title="")
        match = self._PATTERN.match(message.strip())
        if not match:
            return CommitSummary(category="update", title=message.strip())
        kind = match.group("kind").lower()
        title = match.group("title").strip()
        scope = match.group("scope")
        return CommitSummary(category=self._CATEGORY_MAP.get(kind, "update"), title=title, scope=scope)


class RegistryLedger:
    """Read and update the on-disk registry manifest."""

    def __init__(self, path: Path | None = None, *, classifier: CommitClassifier | None = None) -> None:
        self.path = path or REGISTRY_PATH
        self.classifier = classifier or CommitClassifier()
        self._data = self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load(self) -> MutableMapping[str, object]:
        if not self.path.exists():
            return {"fragments": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"fragments": []}

    def save(self) -> None:
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Registry operations
    # ------------------------------------------------------------------
    @property
    def fragments(self) -> List[MutableMapping[str, object]]:
        fragments = self._data.setdefault("fragments", [])
        if isinstance(fragments, list):
            return fragments  # type: ignore[return-value]
        new_list: List[MutableMapping[str, object]] = []
        self._data["fragments"] = new_list
        return new_list

    def _ensure_fragment(self, slug: str) -> MutableMapping[str, object]:
        for fragment in self.fragments:
            if isinstance(fragment, dict) and fragment.get("slug") == slug:
                return fragment
        name = slug.split("/")[-1]
        fragment: MutableMapping[str, object] = {
            "name": name,
            "type": "service",
            "slug": slug,
            "last_seen": None,
            "proof": None,
            "notes": "",
            "semantic_history": [],
        }
        self.fragments.append(fragment)
        return fragment

    def record_commit(
        self,
        slug: str,
        *,
        commit: str,
        message: str,
        timestamp: str | datetime | None = None,
    ) -> Dict[str, object]:
        fragment = self._ensure_fragment(slug)
        history: List[Dict[str, object]] = fragment.setdefault("semantic_history", [])  # type: ignore[assignment]
        if any(event.get("commit") == commit for event in history):
            return {
                "commit": commit,
                "category": None,
                "title": message,
                "scope": None,
                "timestamp": fragment.get("last_seen"),
            }

        if isinstance(timestamp, datetime):
            event_time = timestamp.astimezone(timezone.utc)
        elif isinstance(timestamp, str):
            event_time = _coerce_timestamp(timestamp)
        else:
            event_time = _utc_now()

        summary = self.classifier.classify(message)
        payload = {
            "commit": commit,
            "category": summary.category,
            "title": summary.title,
            "scope": summary.scope,
            "timestamp": event_time.isoformat(),
        }
        history.append(payload)
        fragment["last_seen"] = payload["timestamp"]
        fragment["proof"] = commit
        descriptor = summary.title or message.strip() or commit
        descriptor_scope = f"[{summary.scope}] " if summary.scope else ""
        fragment["notes"] = f"{summary.category}: {descriptor_scope}{descriptor}".strip()
        self.save()
        return payload


def apply_github_push(
    payload: MutableMapping[str, object],
    *,
    ledger: RegistryLedger | None = None,
    capsule: OriginCapsule | None = None,
) -> List[Dict[str, object]]:
    """Process a GitHub ``push`` webhook payload."""

    repository = payload.get("repository", {})
    if not isinstance(repository, MutableMapping):
        raise ValueError("payload missing repository information")
    slug = repository.get("full_name")
    if not isinstance(slug, str) or not slug:
        raise ValueError("repository full_name missing from payload")

    commits: Iterable[MutableMapping[str, object]] = payload.get("commits", [])  # type: ignore[assignment]
    if not isinstance(commits, Iterable):
        raise ValueError("payload commits must be iterable")

    ledger = ledger or RegistryLedger()
    capsule = capsule or OriginCapsule()

    results: List[Dict[str, object]] = []
    for commit_info in commits:
        if not isinstance(commit_info, MutableMapping):
            continue
        commit_sha = str(commit_info.get("id", "")).strip()
        message = str(commit_info.get("message", "")).strip()
        timestamp = commit_info.get("timestamp")
        if not commit_sha:
            continue

        recorded = ledger.record_commit(slug, commit=commit_sha, message=message, timestamp=timestamp)
        capsule.record_commit(commit_sha, message=message or commit_sha, timestamp=_coerce_timestamp(timestamp if isinstance(timestamp, str) else None))
        results.append(recorded)

    return results


__all__ = ["CommitSummary", "CommitClassifier", "RegistryLedger", "apply_github_push"]

