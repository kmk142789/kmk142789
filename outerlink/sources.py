from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional


class SourceClassification(str, Enum):
    AUTHORITATIVE = "authoritative"
    SECONDARY = "secondary"
    COMMUNITY = "community"
    LOCAL = "local"
    PLACEHOLDER = "placeholder"


@dataclass
class Citation:
    source_id: str
    title: str
    url: Optional[str]
    classification: SourceClassification
    accessed_at: str
    last_updated: Optional[str] = None
    update_status: Optional[str] = None
    confidence: float = 0.5
    uncertainty: Optional[str] = None
    placeholder: bool = False
    offline: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "url": self.url,
            "classification": self.classification.value,
            "accessed_at": self.accessed_at,
            "last_updated": self.last_updated,
            "update_status": self.update_status,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "placeholder": self.placeholder,
            "offline": self.offline,
            "notes": self.notes,
        }


@dataclass
class SourceRecord:
    source_id: str
    title: str
    url: Optional[str]
    classification: SourceClassification = SourceClassification.SECONDARY
    description: Optional[str] = None
    last_checked: Optional[str] = None
    last_updated: Optional[str] = None
    last_status: Optional[str] = None
    etag: Optional[str] = None
    checksum: Optional[str] = None
    update_frequency_seconds: Optional[int] = None
    notes: List[str] = field(default_factory=list)

    def mark_checked(
        self,
        status: str,
        *,
        checked_at: Optional[str] = None,
        last_updated: Optional[str] = None,
        note: Optional[str] = None,
    ) -> None:
        self.last_checked = checked_at or datetime.now(timezone.utc).isoformat()
        self.last_status = status
        if last_updated:
            self.last_updated = last_updated
        if note:
            self.notes.append(f"{self.last_checked}: {note}")

    def update_awareness(self, ttl_seconds: Optional[int]) -> Dict[str, Optional[object]]:
        if self.update_frequency_seconds is not None:
            ttl_seconds = self.update_frequency_seconds

        if not ttl_seconds or ttl_seconds <= 0:
            return {
                "ttl_seconds": ttl_seconds,
                "last_checked": self.last_checked,
                "stale": False,
                "next_check_due": None,
            }

        if not self.last_checked:
            return {
                "ttl_seconds": ttl_seconds,
                "last_checked": None,
                "stale": True,
                "next_check_due": None,
            }

        try:
            last_checked_dt = datetime.fromisoformat(self.last_checked)
        except ValueError:
            return {
                "ttl_seconds": ttl_seconds,
                "last_checked": self.last_checked,
                "stale": False,
                "next_check_due": None,
            }
        if last_checked_dt.tzinfo is None:
            last_checked_dt = last_checked_dt.replace(tzinfo=timezone.utc)

        next_check = last_checked_dt + timedelta(seconds=ttl_seconds)
        seconds_remaining = int((next_check - datetime.now(timezone.utc)).total_seconds())
        return {
            "ttl_seconds": ttl_seconds,
            "last_checked": self.last_checked,
            "stale": seconds_remaining <= 0,
            "next_check_due": next_check.isoformat(),
            "seconds_remaining": max(0, seconds_remaining),
        }

    def to_dict(self, *, ttl_seconds: Optional[int] = None) -> Dict[str, object]:
        update = self.update_awareness(ttl_seconds)
        return {
            "source_id": self.source_id,
            "title": self.title,
            "url": self.url,
            "classification": self.classification.value,
            "description": self.description,
            "last_checked": self.last_checked,
            "last_updated": self.last_updated,
            "last_status": self.last_status,
            "etag": self.etag,
            "checksum": self.checksum,
            "update_awareness": update,
            "notes": self.notes[-5:],
        }


class ExternalSourceRegistry:
    """Tracks authoritative sources and builds structured citations."""

    def __init__(self, sources: Optional[Iterable[SourceRecord]] = None) -> None:
        self._sources: Dict[str, SourceRecord] = {}
        self.last_loaded: Optional[str] = None
        for record in sources or []:
            self.register(record)

    def register(self, record: SourceRecord) -> None:
        self._sources[record.source_id] = record

    def register_from_payloads(self, payloads: Iterable[Dict[str, object]]) -> None:
        for payload in payloads:
            classification_value = str(
                payload.get("classification", SourceClassification.SECONDARY.value)
            )
            try:
                classification = SourceClassification(classification_value)
            except ValueError:
                classification = SourceClassification.SECONDARY
            record = SourceRecord(
                source_id=str(payload.get("source_id")),
                title=str(payload.get("title")),
                url=payload.get("url"),
                classification=classification,
                description=payload.get("description"),
                last_checked=payload.get("last_checked"),
                last_updated=payload.get("last_updated"),
                last_status=payload.get("last_status"),
                etag=payload.get("etag"),
                checksum=payload.get("checksum"),
                update_frequency_seconds=payload.get("update_frequency_seconds"),
                notes=list(payload.get("notes", [])),
            )
            self.register(record)

    def get(self, source_id: str) -> Optional[SourceRecord]:
        return self._sources.get(source_id)

    def list_sources(self) -> List[SourceRecord]:
        return list(self._sources.values())

    def load_from(self, path: Path) -> None:
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            return
        sources_payload = payload.get("sources", []) if isinstance(payload, dict) else payload
        if isinstance(sources_payload, list):
            self.register_from_payloads(sources_payload)
            self.last_loaded = datetime.now(timezone.utc).isoformat()

    def save_to(self, path: Path) -> None:
        payload = {"sources": [record.to_dict() for record in self._sources.values()]}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2))

    def _build_placeholder(
        self,
        *,
        source_id: str,
        title: str,
        offline: bool,
        reason: Optional[str],
    ) -> Citation:
        uncertainty = reason or "source unavailable"
        return Citation(
            source_id=source_id,
            title=title,
            url=None,
            classification=SourceClassification.PLACEHOLDER,
            accessed_at=datetime.now(timezone.utc).isoformat(),
            update_status="unknown",
            confidence=0.2 if offline else 0.35,
            uncertainty=uncertainty,
            placeholder=True,
            offline=offline,
            notes=["placeholder_reference"],
        )

    def build_citation_bundle(
        self,
        *,
        source_ids: Optional[Iterable[str]] = None,
        online: bool,
        offline_reason: Optional[str],
        ttl_seconds: Optional[int],
    ) -> Dict[str, object]:
        citations: List[Citation] = []
        requested_ids = list(source_ids) if source_ids is not None else list(self._sources.keys())

        if not requested_ids:
            citations.append(
                self._build_placeholder(
                    source_id="offline_context",
                    title="Offline reasoning placeholder",
                    offline=not online,
                    reason=offline_reason or "no external sources configured",
                )
            )

        for source_id in requested_ids:
            record = self._sources.get(source_id)
            if not record:
                citations.append(
                    self._build_placeholder(
                        source_id=source_id,
                        title=f"Unregistered source {source_id}",
                        offline=not online,
                        reason=offline_reason or "source not registered",
                    )
                )
                continue

            update = record.update_awareness(ttl_seconds)
            stale = bool(update.get("stale"))
            update_status = "stale" if stale else "fresh"
            confidence = 0.8 if online and not stale else 0.5
            uncertainty = None
            if not online:
                uncertainty = offline_reason or "offline"
            elif stale:
                uncertainty = "source update overdue"

            citations.append(
                Citation(
                    source_id=record.source_id,
                    title=record.title,
                    url=record.url,
                    classification=record.classification,
                    accessed_at=datetime.now(timezone.utc).isoformat(),
                    last_updated=record.last_updated,
                    update_status=update_status,
                    confidence=confidence,
                    uncertainty=uncertainty,
                    placeholder=False,
                    offline=not online,
                    notes=record.notes[-3:],
                )
            )

        classification_counts: Dict[str, int] = {}
        for record in self._sources.values():
            classification_counts[record.classification.value] = (
                classification_counts.get(record.classification.value, 0) + 1
            )

        update_states = {
            "fresh": len([c for c in citations if c.update_status == "fresh"]),
            "stale": len([c for c in citations if c.update_status == "stale"]),
            "unknown": len([c for c in citations if c.update_status == "unknown"]),
        }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "online": online,
            "offline_reason": offline_reason,
            "sources": [record.to_dict(ttl_seconds=ttl_seconds) for record in self._sources.values()],
            "citations": [citation.to_dict() for citation in citations],
            "classification_summary": classification_counts,
            "update_summary": update_states,
            "reasoning_mode": "online_augmented" if online else "offline_internal",
        }

    def write_artifact(self, destination: Path, bundle: Dict[str, object]) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(bundle, indent=2))
        return destination


__all__ = ["SourceClassification", "Citation", "SourceRecord", "ExternalSourceRegistry"]
