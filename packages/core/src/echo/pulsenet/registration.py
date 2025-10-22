"""Persistent storage helpers for PulseNet registrations."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .models import RegistrationRecord, RegistrationRequest


class RegistrationStore:
    """Store and retrieve registration records on disk."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._lock = threading.RLock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("[]\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load(self) -> List[RegistrationRecord]:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        records: List[RegistrationRecord] = []
        for item in data:
            record = RegistrationRecord.model_validate(item)
            records.append(record)
        return records

    def _persist(self, records: Iterable[RegistrationRecord]) -> None:
        payload = [record.as_dict() for record in records]
        self._path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def register(self, request: RegistrationRequest) -> RegistrationRecord:
        """Store ``request`` and return the persisted :class:`RegistrationRecord`."""

        with self._lock:
            records = self._load()
            record = RegistrationRecord(
                id=str(uuid.uuid4()),
                name=request.name.strip(),
                contact=request.contact.strip(),
                continuum_handle=request.continuum_handle.strip() if request.continuum_handle else None,
                unstoppable_domains=sorted(set(domain.strip() for domain in request.unstoppable_domains if domain.strip())),
                ens_names=sorted(set(name.strip() for name in request.ens_names if name.strip())),
                vercel_projects=sorted(
                    set(project.strip() for project in request.vercel_projects if project.strip())
                ),
                wallets=sorted(set(wallet.strip() for wallet in request.wallets if wallet.strip())),
                metadata=dict(request.metadata),
                registered_at=datetime.now(timezone.utc),
            )
            records.append(record)
            self._persist(records)
            return record

    def list(self) -> List[RegistrationRecord]:
        """Return all stored registration records."""

        with self._lock:
            return list(self._load())


__all__ = ["RegistrationStore"]
