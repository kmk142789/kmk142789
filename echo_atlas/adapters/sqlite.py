"""SQLite storage adapter for the Echo Atlas."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Optional

from ..models import AtlasEdge, AtlasNode, ChangeRecord, EntityType, RelationType
from .base import StorageAdapter

_DEFAULT_DB_PATH = Path("data/atlas.db")


def _row_to_node(row: sqlite3.Row) -> AtlasNode:
    return AtlasNode(
        identifier=row["id"],
        name=row["name"],
        entity_type=EntityType(row["entity_type"]),
        attributes=json.loads(row["attributes"] or "{}"),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _row_to_edge(row: sqlite3.Row) -> AtlasEdge:
    return AtlasEdge(
        identifier=row["id"],
        source_id=row["source_id"],
        target_id=row["target_id"],
        relation=RelationType(row["relation"]),
        attributes=json.loads(row["attributes"] or "{}"),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _row_to_change(row: sqlite3.Row) -> ChangeRecord:
    return ChangeRecord(
        identifier=row["id"],
        entity_id=row["entity_id"],
        entity_type=row["entity_type"],
        change_type=row["change_type"],
        payload=json.loads(row["payload"] or "{}"),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class SQLiteAdapter(StorageAdapter):
    """Concrete ``StorageAdapter`` backed by SQLite."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _DEFAULT_DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.connection.row_factory = sqlite3.Row

    def initialise(self) -> None:
        cursor = self.connection.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                attributes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                attributes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(source_id, relation, target_id)
            );

            CREATE TABLE IF NOT EXISTS changes (
                id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                change_type TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def upsert_node(self, node: AtlasNode) -> AtlasNode:
        now = datetime.utcnow().isoformat()
        payload = json.dumps(node.attributes)
        self.connection.execute(
            """
            INSERT INTO nodes(id, name, entity_type, attributes, created_at, updated_at)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                entity_type=excluded.entity_type,
                attributes=excluded.attributes,
                updated_at=excluded.updated_at
            """,
            (node.identifier, node.name, node.entity_type.value, payload, now, now),
        )
        self.connection.commit()
        stored = self.get_node(node.identifier)
        assert stored is not None  # pragma: no cover - defensive
        return stored

    def upsert_edge(self, edge: AtlasEdge) -> AtlasEdge:
        now = datetime.utcnow().isoformat()
        payload = json.dumps(edge.attributes)
        self.connection.execute(
            """
            INSERT INTO edges(id, source_id, target_id, relation, attributes, created_at, updated_at)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                attributes=excluded.attributes,
                updated_at=excluded.updated_at
            """,
            (
                edge.identifier,
                edge.source_id,
                edge.target_id,
                edge.relation.value,
                payload,
                now,
                now,
            ),
        )
        self.connection.commit()
        stored = next((e for e in self.get_edges_for(edge.source_id) if e.identifier == edge.identifier), None)
        assert stored is not None  # pragma: no cover - defensive
        return stored

    def remove_edge(self, identifier: str) -> None:
        self.connection.execute("DELETE FROM edges WHERE id=?", (identifier,))
        self.connection.commit()

    def iter_nodes(self) -> Iterator[AtlasNode]:
        cursor = self.connection.execute("SELECT * FROM nodes ORDER BY name")
        for row in cursor:
            yield _row_to_node(row)

    def iter_edges(self) -> Iterator[AtlasEdge]:
        cursor = self.connection.execute("SELECT * FROM edges ORDER BY created_at")
        for row in cursor:
            yield _row_to_edge(row)

    def get_node(self, identifier: str) -> Optional[AtlasNode]:
        cursor = self.connection.execute("SELECT * FROM nodes WHERE id=?", (identifier,))
        row = cursor.fetchone()
        return _row_to_node(row) if row else None

    def get_edges_for(self, identifier: str) -> Iterable[AtlasEdge]:
        cursor = self.connection.execute(
            "SELECT * FROM edges WHERE source_id=? OR target_id=? ORDER BY created_at",
            (identifier, identifier),
        )
        return [_row_to_edge(row) for row in cursor.fetchall()]

    def log_change(self, change: ChangeRecord) -> None:
        self.connection.execute(
            """
            INSERT INTO changes(id, entity_id, entity_type, change_type, payload, created_at)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                change.identifier,
                change.entity_id,
                change.entity_type,
                change.change_type,
                json.dumps(change.payload),
                change.created_at.isoformat(),
            ),
        )
        self.connection.commit()

    def recent_changes(self, limit: int = 20) -> Iterable[ChangeRecord]:
        cursor = self.connection.execute(
            "SELECT * FROM changes ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [_row_to_change(row) for row in cursor.fetchall()]

    def close(self) -> None:
        self.connection.close()
