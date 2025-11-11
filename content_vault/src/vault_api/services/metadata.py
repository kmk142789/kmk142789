"""Metadata indexing and query services."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable, Iterator, List, Mapping, MutableMapping

from ..models import ChangeRecord, VaultItem


class MetadataIndex:
    """In-memory inverted index for metadata attributes."""

    def __init__(self) -> None:
        self._index: MutableMapping[str, MutableMapping[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    def update(self, item: VaultItem) -> None:
        for key, value in item.metadata.items():
            self._index[key][value].add(item.address)

    def remove(self, address: str) -> None:
        for values in self._index.values():
            for addresses in values.values():
                addresses.discard(address)

    def query(self, filters: Mapping[str, str]) -> Iterable[str]:
        candidate_sets: List[set[str]] = []
        for key, value in filters.items():
            candidate_sets.append(set(self._index.get(key, {}).get(value, set())))
        if not candidate_sets:
            return []
        intersection = candidate_sets[0]
        for candidate in candidate_sets[1:]:
            intersection &= candidate
        return sorted(intersection)


class ChangeJournal:
    """Maintains a chronological log of vault events."""

    def __init__(self) -> None:
        self._records: List[ChangeRecord] = []

    def append(self, event: str, reference: str, payload: Mapping[str, object] | None = None) -> None:
        self._records.append(
            ChangeRecord(
                event=event,
                reference=reference,
                timestamp=datetime.utcnow(),
                payload=dict(payload or {}),
            )
        )

    def iter(self) -> Iterator[ChangeRecord]:
        return iter(self._records)

    def latest(self, count: int = 10) -> List[ChangeRecord]:
        return self._records[-count:]

    def clear(self) -> None:
        self._records.clear()
