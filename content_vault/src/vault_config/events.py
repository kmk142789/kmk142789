"""Configuration event registry and helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional


@dataclass
class ConfigEvent:
    """Represents a configuration mutation."""

    identifier: str
    type: str
    payload: Dict[str, Any]
    recorded_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConfigVersion:
    """Metadata describing a configuration version."""

    version: int
    source: Path
    checksum: str
    events: List[ConfigEvent]
    dependencies: List[Dict[str, str]]
    previous: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "source": str(self.source),
            "checksum": self.checksum,
            "events": [event.__dict__ for event in self.events],
            "dependencies": self.dependencies,
            "previous": self.previous,
        }


class ConfigRegistry:
    """In-memory registry of configuration versions with rollback support."""

    def __init__(self) -> None:
        self._versions: MutableMapping[int, ConfigVersion] = {}
        self._latest: Optional[int] = None

    @property
    def latest(self) -> Optional[ConfigVersion]:
        if self._latest is None:
            return None
        return self._versions[self._latest]

    def register(self, version: int, source: Path, config: Dict[str, Any]) -> ConfigVersion:
        checksum = hashlib.sha256(json.dumps(config, sort_keys=True).encode("utf-8")).hexdigest()
        events = [
            ConfigEvent(identifier=event["id"], type=event["type"], payload=event.get("payload", {}))
            for event in config.get("events", [])
        ]
        dependencies = [dict(dep) for dep in config.get("dependencies", [])]
        record = ConfigVersion(
            version=version,
            source=source,
            checksum=checksum,
            events=events,
            dependencies=dependencies,
            previous=self._latest,
        )
        self._versions[version] = record
        self._latest = version
        return record

    def rollback(self, version: int) -> Dict[str, Any]:
        if version not in self._versions:
            raise KeyError(f"version {version} not registered")
        target = self._versions[version]
        return {
            "version": target.version,
            "source": str(target.source),
            "dependencies": target.dependencies,
            "events": [event.__dict__ for event in target.events],
        }

    def iter_versions(self) -> Iterable[ConfigVersion]:
        ordered = sorted(self._versions.values(), key=lambda v: v.version)
        for version in ordered:
            yield version
