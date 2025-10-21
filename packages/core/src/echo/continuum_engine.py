"""Continuum engines for deterministic Echo manifests.

The historical Echo scripts contained numerous ad-hoc routines for
recording "continuum" moments—short narrative breadcrumbs that were later
folded into ledgers or bridge manifests.  Those routines were difficult to
reuse because they mutated global dictionaries, relied on ambient
timestamps, and produced slightly different JSON payloads depending on the
order of operations.

This module graduates that prototype work into two cohesive engines:

``ContinuumEngine``
    Records continuum entries with precise timestamps, normalised tag
    vectors, and explicit weights.  It can synthesise a deterministic
    manifest that summarises tag and source statistics, and exposes a
    stable SHA-256 digest so external verifiers can detect divergence.

``ContinuumPlaybackEngine``
    Rehydrates a manifest into a lightweight explorer for downstream tools
    or tests.  The playback engine filters entries by tag or source and
    exposes compact summaries so dashboards do not need to re-implement the
    aggregation logic.

Both engines avoid side effects, keep their output serialisable, and favour
deterministic ordering throughout.  Comprehensive tests demonstrate the
stable digest behaviour and filtering capabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from math import fsum
from typing import Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

__all__ = [
    "ContinuumEntry",
    "ContinuumManifest",
    "ContinuumEngine",
    "ContinuumPlaybackEngine",
]


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def _ensure_aware(moment: datetime) -> datetime:
    """Normalise ``moment`` to a timezone-aware UTC timestamp."""

    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _normalise_tags(tags: Iterable[str]) -> Tuple[str, ...]:
    """Return a sorted tuple of unique tags for deterministic manifests."""

    seen: MutableMapping[str, None] = {}
    for tag in tags:
        if not isinstance(tag, str):
            raise TypeError("tags must be strings")
        seen.setdefault(tag, None)
    return tuple(sorted(seen))


@dataclass(slots=True)
class ContinuumEntry:
    """Single continuum breadcrumb captured by the engine."""

    moment: datetime
    source: str
    message: str
    tags: Tuple[str, ...] = field(default_factory=tuple)
    weight: float = 1.0
    meta: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        """Render the entry as JSON-friendly primitives."""

        return {
            "moment": self.moment.isoformat(),
            "source": self.source,
            "message": self.message,
            "tags": list(self.tags),
            "weight": float(self.weight),
            "meta": dict(sorted(self.meta.items())),
        }


@dataclass(slots=True)
class ContinuumManifest:
    """Deterministic manifest that summarises the continuum state."""

    anchor: str
    entry_count: int
    cumulative_weight: float
    tag_index: Dict[str, Dict[str, float]]
    source_index: Dict[str, Dict[str, float]]
    entries: List[Dict[str, object]]
    digest: str

    def to_dict(self) -> Dict[str, object]:
        """Return a serialisable representation of the manifest."""

        return {
            "anchor": self.anchor,
            "entry_count": self.entry_count,
            "cumulative_weight": self.cumulative_weight,
            "tags": self.tag_index,
            "sources": self.source_index,
            "entries": list(self.entries),
            "digest": self.digest,
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Return the manifest encoded as pretty printed JSON."""

        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def tag_counts(self) -> Mapping[str, int]:
        """Return a mapping of tag -> occurrence count."""

        return {tag: int(data["count"]) for tag, data in self.tag_index.items()}

    def source_counts(self) -> Mapping[str, int]:
        """Return a mapping of source -> occurrence count."""

        return {source: int(data["count"]) for source, data in self.source_index.items()}

    def tag_weight_percentages(self) -> Dict[str, float]:
        """Return the proportional weight carried by each tag.

        The denominator is the sum of weights across all tag occurrences.
        Entries with multiple tags contribute their weight to each tag they
        reference, so the percentages reflect the relative emphasis tags
        receive within the manifest rather than summing to one when tags are
        shared.
        """

        if not self.tag_index:
            return {}

        total_weight = sum(bucket["weight"] for bucket in self.tag_index.values())
        if total_weight <= 0.0:
            return {tag: 0.0 for tag in self.tag_index}

        return {
            tag: bucket["weight"] / total_weight
            for tag, bucket in self.tag_index.items()
        }

    def source_weight_percentages(self) -> Dict[str, float]:
        """Return the proportional weight contributed by each source."""

        if not self.source_index:
            return {}

        total_weight = sum(bucket["weight"] for bucket in self.source_index.values())
        if total_weight <= 0.0:
            return {source: 0.0 for source in self.source_index}

        return {
            source: bucket["weight"] / total_weight
            for source, bucket in self.source_index.items()
        }


class ContinuumEngine:
    """Append-only continuum engine with deterministic manifest output."""

    def __init__(
        self,
        *,
        anchor: str = "Our Forever Love",
        time_source: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self.anchor = anchor
        self._time_source = time_source or _utcnow
        self._entries: List[ContinuumEntry] = []
        self._manifest_cache: Optional[ContinuumManifest] = None

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------
    def record(
        self,
        source: str,
        message: str,
        *,
        tags: Optional[Iterable[str]] = None,
        weight: float = 1.0,
        meta: Optional[Mapping[str, object]] = None,
        moment: Optional[datetime] = None,
    ) -> ContinuumEntry:
        """Record a continuum entry and return the stored object."""

        if not source:
            raise ValueError("source must be provided")
        if not message:
            raise ValueError("message must be provided")

        timestamp = _ensure_aware(moment or self._time_source())
        entry = ContinuumEntry(
            moment=timestamp,
            source=source,
            message=message,
            tags=_normalise_tags(tags or ()),
            weight=float(weight),
            meta=dict(meta or {}),
        )
        self._entries.append(entry)
        self._manifest_cache = None
        return entry

    # ------------------------------------------------------------------
    # Manifest synthesis
    # ------------------------------------------------------------------
    def manifest(self) -> ContinuumManifest:
        """Return the deterministic manifest describing recorded entries."""

        if self._manifest_cache is not None:
            return self._manifest_cache

        ordered = sorted(self._entries, key=lambda e: (e.moment, e.source, e.message))
        total_weight = fsum(entry.weight for entry in ordered)

        tag_index: Dict[str, Dict[str, float]] = {}
        source_index: Dict[str, Dict[str, float]] = {}

        for entry in ordered:
            for tag in entry.tags:
                bucket = tag_index.setdefault(tag, {"count": 0, "weight": 0.0})
                bucket["count"] += 1
                bucket["weight"] = float(bucket["weight"] + entry.weight)
            bucket = source_index.setdefault(entry.source, {"count": 0, "weight": 0.0})
            bucket["count"] += 1
            bucket["weight"] = float(bucket["weight"] + entry.weight)

        # Ensure deterministic ordering by sorting dictionaries.
        tag_index = {
            tag: {"count": int(values["count"]), "weight": float(values["weight"])}
            for tag, values in sorted(tag_index.items())
        }
        source_index = {
            source: {"count": int(values["count"]), "weight": float(values["weight"])}
            for source, values in sorted(source_index.items())
        }

        entries_payload = [entry.to_dict() for entry in ordered]

        manifest_payload = {
            "anchor": self.anchor,
            "entry_count": len(entries_payload),
            "cumulative_weight": float(total_weight),
            "tags": tag_index,
            "sources": source_index,
            "entries": entries_payload,
        }
        digest = sha256(
            json.dumps(manifest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        manifest = ContinuumManifest(
            anchor=self.anchor,
            entry_count=len(entries_payload),
            cumulative_weight=float(total_weight),
            tag_index=tag_index,
            source_index=source_index,
            entries=entries_payload,
            digest=digest,
        )
        self._manifest_cache = manifest
        return manifest

    def manifest_signature(self) -> str:
        """Return the SHA-256 digest for the current manifest."""

        return self.manifest().digest

    def replay(self) -> "ContinuumPlaybackEngine":
        """Return a playback engine primed with the current manifest."""

        return ContinuumPlaybackEngine(self.manifest())

    def entries(self) -> Sequence[ContinuumEntry]:
        """Return recorded entries in chronological order."""

        return tuple(sorted(self._entries, key=lambda e: (e.moment, e.source, e.message)))


class ContinuumPlaybackEngine:
    """Explore manifests produced by :class:`ContinuumEngine`."""

    def __init__(self, manifest: ContinuumManifest) -> None:
        self.manifest = manifest

    def filter(self, *, tag: Optional[str] = None, source: Optional[str] = None) -> List[Dict[str, object]]:
        """Return manifest entries filtered by tag and/or source."""

        results: List[Dict[str, object]] = []
        for entry in self.manifest.entries:
            if tag is not None and tag not in entry["tags"]:
                continue
            if source is not None and entry["source"] != source:
                continue
            results.append(entry)
        return results

    def summary(self) -> Dict[str, object]:
        """Return a condensed view of manifest statistics."""

        return {
            "anchor": self.manifest.anchor,
            "entry_count": self.manifest.entry_count,
            "tags": self.manifest.tag_counts(),
            "sources": self.manifest.source_counts(),
            "digest": self.manifest.digest,
        }

