"""Content-addressable storage services."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Dict, Iterable, Iterator, Mapping, MutableMapping, Optional

from ..models import ChangeRecord, IntegrityReport, VaultItem


@dataclass
class StoredObject:
    content: bytes
    metadata: Dict[str, str]
    created_at: datetime
    version: int = 1


class ContentAddressableStore:
    """In-memory store keyed by content hash with deduplication."""

    def __init__(self) -> None:
        self._objects: MutableMapping[str, StoredObject] = {}
        self._history: list[ChangeRecord] = []
        self._lock = Lock()

    @staticmethod
    def _address(payload: bytes) -> str:
        digest = hashlib.sha256(payload).hexdigest()
        return f"vault://{digest}"

    def store(self, payload: bytes, metadata: Optional[Mapping[str, str]] = None) -> VaultItem:
        metadata = dict(metadata or {})
        address = self._address(payload)
        with self._lock:
            existing = self._objects.get(address)
            if existing:
                existing.version += 1
                existing.metadata.update(metadata)
                self._history.append(
                    ChangeRecord(
                        event="deduplicated",
                        reference=address,
                        timestamp=datetime.utcnow(),
                        payload={"version": existing.version},
                    )
                )
                stored = existing
            else:
                stored = StoredObject(
                    content=payload,
                    metadata=metadata,
                    created_at=datetime.utcnow(),
                )
                self._objects[address] = stored
                self._history.append(
                    ChangeRecord(
                        event="stored",
                        reference=address,
                        timestamp=stored.created_at,
                        payload={"metadata": metadata},
                    )
                )
        return VaultItem(
            address=address,
            content=stored.content,
            metadata=stored.metadata,
            created_at=stored.created_at,
            version=stored.version,
        )

    def fetch(self, address: str) -> Optional[VaultItem]:
        obj = self._objects.get(address)
        if obj is None:
            return None
        return VaultItem(address, obj.content, obj.metadata, obj.created_at, obj.version)

    def iter_items(self) -> Iterator[VaultItem]:
        for address, obj in self._objects.items():
            yield VaultItem(address, obj.content, obj.metadata, obj.created_at, obj.version)

    def log_event(self, record: ChangeRecord) -> None:
        with self._lock:
            self._history.append(record)

    def history(self) -> Iterable[ChangeRecord]:
        return list(self._history)

    def verify_integrity(self) -> IntegrityReport:
        mismatches: list[str] = []
        for address, obj in self._objects.items():
            if address != self._address(obj.content):
                mismatches.append(address)
        return IntegrityReport(scanned=len(self._objects), mismatches=mismatches)

    def clear(self) -> None:
        with self._lock:
            self._objects.clear()
            self._history.clear()
