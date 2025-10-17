"""Persistence helpers for Pulse Weaver."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Mapping

from ..adapters.base import PulseWeaverAdapter
from ..core import LinkRecord, WeaveFragment


class PulseWeaverRepository:
    """Encapsulates SQL queries for the Pulse Weaver tables."""

    def __init__(self, adapter: PulseWeaverAdapter) -> None:
        self.adapter = adapter

    def record_event(
        self,
        *,
        cycle: str,
        key: str,
        status: str,
        message: str,
        proof: str | None,
        echo: str | None,
        metadata: Mapping[str, object],
    ) -> WeaveFragment:
        created_at = datetime.now(timezone.utc)
        with self.adapter.context() as conn:
            conn.execute(
                """
                INSERT INTO pulse_weaver_events (cycle, key, status, message, proof, echo, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cycle,
                    key,
                    status,
                    message,
                    proof,
                    echo,
                    json.dumps(dict(metadata), sort_keys=True),
                    created_at.isoformat(),
                ),
            )
        return WeaveFragment(
            key=key,
            status=status,
            message=message,
            cycle=cycle,
            proof=proof,
            echo=echo,
            created_at=created_at,
            metadata=dict(metadata),
        )

    def record_link(
        self,
        *,
        key: str,
        atlas_node: str | None,
        phantom_trace: str | None,
    ) -> None:
        if not atlas_node and not phantom_trace:
            return
        created_at = datetime.now(timezone.utc).isoformat()
        with self.adapter.context() as conn:
            conn.execute(
                """
                INSERT INTO pulse_weaver_links (key, atlas_node, phantom_trace, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (key, atlas_node, phantom_trace, created_at),
            )

    def list_recent_events(self, limit: int = 20) -> List[WeaveFragment]:
        with self.adapter.context() as conn:
            rows = conn.execute(
                """
                SELECT key, status, message, cycle, proof, echo, metadata, created_at
                FROM pulse_weaver_events
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        fragments: List[WeaveFragment] = []
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            fragments.append(
                WeaveFragment(
                    key=row["key"],
                    status=row["status"],
                    message=row["message"],
                    cycle=row["cycle"],
                    proof=row["proof"],
                    echo=row["echo"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    metadata=metadata,
                )
            )
        return fragments

    def counts_by_status(self) -> Dict[str, int]:
        with self.adapter.context() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as total FROM pulse_weaver_events GROUP BY status"
            ).fetchall()
        return {row["status"]: int(row["total"]) for row in rows}

    def list_links(self) -> List[LinkRecord]:
        with self.adapter.context() as conn:
            rows = conn.execute(
                """
                SELECT key, atlas_node, phantom_trace, created_at
                FROM pulse_weaver_links
                ORDER BY datetime(created_at) DESC, id DESC
                """
            ).fetchall()
        links: List[LinkRecord] = []
        for row in rows:
            links.append(
                LinkRecord(
                    key=row["key"],
                    atlas_node=row["atlas_node"],
                    phantom_trace=row["phantom_trace"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )
        return links

    def atlas_link_counts(self) -> Dict[str, int]:
        with self.adapter.context() as conn:
            rows = conn.execute(
                """
                SELECT atlas_node, COUNT(*) AS total
                FROM pulse_weaver_links
                WHERE atlas_node IS NOT NULL
                GROUP BY atlas_node
                """
            ).fetchall()
        return {row["atlas_node"]: int(row["total"]) for row in rows if row["atlas_node"]}

    def phantom_link_counts(self) -> Dict[str, int]:
        with self.adapter.context() as conn:
            rows = conn.execute(
                """
                SELECT phantom_trace, COUNT(*) AS total
                FROM pulse_weaver_links
                WHERE phantom_trace IS NOT NULL
                GROUP BY phantom_trace
                """
            ).fetchall()
        return {row["phantom_trace"]: int(row["total"]) for row in rows if row["phantom_trace"]}


__all__ = ["PulseWeaverRepository"]
