"""Repository abstraction for the Echo Atlas storage layer."""

from __future__ import annotations

import json
from typing import Iterable, List, Mapping, Optional, Sequence

from ..domain import Edge, EntityType, Node, RelationType
from ..utils import utcnow
from ..adapters.base import AtlasAdapter


class AtlasRepository:
    """High-level persistence helpers."""

    def __init__(self, adapter: AtlasAdapter) -> None:
        self.adapter = adapter

    def apply(self, sql: str, parameters: Sequence[object] | Mapping[str, object] = ()) -> None:
        with self.adapter.context() as conn:
            conn.execute(sql, parameters)

    def executemany(self, sql: str, parameters: Iterable[Sequence[object]]) -> None:
        with self.adapter.context() as conn:
            conn.executemany(sql, parameters)

    def fetchall(self, sql: str, parameters: Sequence[object] | Mapping[str, object] = ()):  # type: ignore[override]
        with self.adapter.context() as conn:
            return conn.execute(sql, parameters).fetchall()

    def upsert_node(self, node: Node) -> None:
        payload = json.dumps(node.metadata, sort_keys=True)
        timestamp = utcnow()
        with self.adapter.context() as conn:
            conn.execute(
                """
                INSERT INTO atlas_nodes (id, name, entity_type, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    entity_type=excluded.entity_type,
                    metadata=excluded.metadata,
                    updated_at=excluded.updated_at
                """,
                (node.identifier, node.name, node.entity_type.value, payload, timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO atlas_change_log (timestamp, change_type, entity_type, entity_id, payload)
                VALUES (?, 'UPSERT_NODE', ?, ?, ?)
                """,
                (timestamp, node.entity_type.value, node.identifier, payload),
            )

    def upsert_edge(self, edge: Edge) -> None:
        payload = json.dumps(edge.metadata, sort_keys=True)
        timestamp = utcnow()
        with self.adapter.context() as conn:
            conn.execute(
                """
                INSERT INTO atlas_edges (id, source, target, relation, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    relation=excluded.relation,
                    metadata=excluded.metadata,
                    updated_at=excluded.updated_at
                """,
                (
                    edge.identifier,
                    edge.source,
                    edge.target,
                    edge.relation.value,
                    payload,
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute(
                """
                INSERT INTO atlas_change_log (timestamp, change_type, entity_type, entity_id, payload)
                VALUES (?, 'UPSERT_EDGE', 'Edge', ?, ?)
                """,
                (timestamp, edge.identifier, payload),
            )

    def list_nodes(self) -> List[Node]:
        rows = self.fetchall(
            "SELECT id, name, entity_type, metadata FROM atlas_nodes ORDER BY name ASC"
        )
        return [
            Node(
                identifier=row["id"],
                name=row["name"],
                entity_type=EntityType(row["entity_type"]),
                metadata=json.loads(row["metadata"] or "{}"),
            )
            for row in rows
        ]

    def list_edges(self) -> List[Edge]:
        rows = self.fetchall(
            "SELECT id, source, target, relation, metadata FROM atlas_edges ORDER BY id"
        )
        return [
            Edge(
                identifier=row["id"],
                source=row["source"],
                target=row["target"],
                relation=RelationType(row["relation"]),
                metadata=json.loads(row["metadata"] or "{}"),
            )
            for row in rows
        ]

    def recent_changes(self, limit: int = 20) -> List[Mapping[str, object]]:
        rows = self.fetchall(
            """
            SELECT timestamp, change_type, entity_type, entity_id, payload
            FROM atlas_change_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        result: List[Mapping[str, object]] = []
        for row in rows:
            payload = row["payload"]
            result.append(
                {
                    "timestamp": row["timestamp"],
                    "change_type": row["change_type"],
                    "entity_type": row["entity_type"],
                    "entity_id": row["entity_id"],
                    "payload": json.loads(payload) if payload else None,
                }
            )
        return result

    def export_graph(self) -> Mapping[str, object]:
        nodes = [node.as_dict() for node in self.list_nodes()]
        edges = [edge.as_dict() for edge in self.list_edges()]
        return {
            "generated_at": utcnow(),
            "nodes": nodes,
            "edges": edges,
            "change_log": self.recent_changes(limit=50),
        }

    def find_node_by_name(self, name: str) -> Optional[Node]:
        rows = self.fetchall(
            """
            SELECT id, name, entity_type, metadata
            FROM atlas_nodes
            WHERE lower(name) = lower(?)
            LIMIT 1
            """,
            (name,),
        )
        if not rows:
            return None
        row = rows[0]
        return Node(
            identifier=row["id"],
            name=row["name"],
            entity_type=EntityType(row["entity_type"]),
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def edges_for(self, identifier: str) -> List[Edge]:
        rows = self.fetchall(
            """
            SELECT id, source, target, relation, metadata
            FROM atlas_edges
            WHERE source = ? OR target = ?
            ORDER BY relation
            """,
            (identifier, identifier),
        )
        return [
            Edge(
                identifier=row["id"],
                source=row["source"],
                target=row["target"],
                relation=RelationType(row["relation"]),
                metadata=json.loads(row["metadata"] or "{}"),
            )
            for row in rows
        ]

    def count_by_entity(self) -> Mapping[str, int]:
        rows = self.fetchall(
            """
            SELECT entity_type, COUNT(*) as total
            FROM atlas_nodes
            GROUP BY entity_type
            ORDER BY entity_type
            """
        )
        return {row["entity_type"]: int(row["total"]) for row in rows}

    def count_by_relation(self) -> Mapping[str, int]:
        rows = self.fetchall(
            """
            SELECT relation, COUNT(*) as total
            FROM atlas_edges
            GROUP BY relation
            ORDER BY relation
            """
        )
        return {row["relation"]: int(row["total"]) for row in rows}

    def store_highlight(self, text: str) -> None:
        timestamp = utcnow()
        with self.adapter.context() as conn:
            conn.execute(
                """
                INSERT INTO atlas_highlights (created_at, content)
                VALUES (?, ?)
                """,
                (timestamp, text),
            )

    def latest_highlight(self) -> Optional[str]:
        rows = self.fetchall(
            "SELECT content FROM atlas_highlights ORDER BY id DESC LIMIT 1"
        )
        if not rows:
            return None
        return rows[0]["content"]
