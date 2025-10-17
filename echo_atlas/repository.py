"""Repository helpers for Echo Atlas persistence."""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional

from .adapters.base import StorageAdapter
from .adapters.sqlite import SQLiteAdapter
from .migrations import apply_migrations
from .models import AtlasEdge, AtlasNode, ChangeRecord, RelationType, edge_identifier


@dataclass(slots=True)
class RepositoryConfig:
    """Configuration for repository creation."""

    database_url: str = "sqlite:///data/atlas.db"

    @classmethod
    def from_env(cls) -> "RepositoryConfig":
        return cls(database_url=os.getenv("ATLAS_DATABASE_URL", "sqlite:///data/atlas.db"))


def _adapter_from_url(url: str) -> StorageAdapter:
    if url.startswith("sqlite:///"):
        path = Path(url.removeprefix("sqlite:///"))
        return SQLiteAdapter(path)
    raise ValueError(f"Unsupported atlas database url: {url}")


class AtlasRepository:
    """High level repository orchestrating adapters and change logging."""

    def __init__(self, adapter: StorageAdapter | None = None, *, config: RepositoryConfig | None = None) -> None:
        self.config = config or RepositoryConfig.from_env()
        self.adapter = adapter or _adapter_from_url(self.config.database_url)
        self.adapter.initialise()
        apply_migrations(self.adapter)

    @contextmanager
    def context(self) -> Iterator["AtlasRepository"]:
        try:
            yield self
        finally:
            self.adapter.close()

    def upsert_node(self, node: AtlasNode, *, change_type: str = "upsert") -> AtlasNode:
        stored = self.adapter.upsert_node(node)
        self._log_change(stored.identifier, stored.entity_type.value, change_type, stored.as_dict())
        return stored

    def upsert_edge(self, edge: AtlasEdge, *, change_type: str = "upsert") -> AtlasEdge:
        stored = self.adapter.upsert_edge(edge)
        self._log_change(stored.identifier, "edge", change_type, stored.as_dict())
        return stored

    def ensure_edge(
        self,
        source_id: str,
        relation: RelationType,
        target_id: str,
        attributes: Optional[Dict[str, object]] = None,
    ) -> AtlasEdge:
        identifier = edge_identifier(source_id, relation, target_id)
        edge = AtlasEdge(
            identifier=identifier,
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            attributes=attributes or {},
        )
        return self.upsert_edge(edge)

    def remove_edge(self, identifier: str) -> None:
        self.adapter.remove_edge(identifier)
        self._log_change(identifier, "edge", "delete", {"id": identifier})

    def get_node(self, identifier: str) -> Optional[AtlasNode]:
        return self.adapter.get_node(identifier)

    def iter_nodes(self) -> Iterator[AtlasNode]:
        yield from self.adapter.iter_nodes()

    def iter_edges(self) -> Iterator[AtlasEdge]:
        yield from self.adapter.iter_edges()

    def get_edges_for(self, identifier: str) -> Iterable[AtlasEdge]:
        return self.adapter.get_edges_for(identifier)

    def recent_changes(self, limit: int = 20) -> Iterable[ChangeRecord]:
        return self.adapter.recent_changes(limit)

    def _log_change(self, entity_id: str, entity_type: str, change_type: str, payload: Dict[str, object]) -> None:
        record = ChangeRecord(
            identifier=str(uuid.uuid4()),
            entity_id=entity_id,
            entity_type=entity_type,
            change_type=change_type,
            payload=payload,
            created_at=datetime.now(tz=timezone.utc),
        )
        self.adapter.log_change(record)
