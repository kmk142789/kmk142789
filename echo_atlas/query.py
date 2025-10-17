"""Query utilities for the Echo Atlas graph."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from .models import AtlasEdge, AtlasNode, EntityType, RelationType
from .repository import AtlasRepository


@dataclass(slots=True)
class EntityRollup:
    """Relationships grouped by relation type for a single entity."""

    node: AtlasNode
    relations: Dict[RelationType, List[AtlasEdge]]

    def to_dict(self) -> Dict[str, object]:
        data = {
            "entity": self.node.as_dict(),
            "relations": {},
        }
        for relation, edges in self.relations.items():
            data["relations"][relation.value] = [edge.as_dict() for edge in edges]
        return data


class AtlasQuery:
    """Read-only helpers for exploring the atlas graph."""

    def __init__(self, repository: AtlasRepository) -> None:
        self.repository = repository

    def ownership_summary(self) -> Dict[str, List[Dict[str, object]]]:
        """Return grouped entities and their relations."""

        grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
        edges = list(self.repository.iter_edges())
        for node in self.repository.iter_nodes():
            if node.entity_type in {EntityType.PERSON, EntityType.BOT}:
                rollup = self.rollup_for_entity(node.identifier, edges)
                grouped[node.entity_type.value].append(rollup.to_dict())
        return dict(grouped)

    def rollup_for_entity(
        self,
        identifier: str,
        edges: Optional[Iterable[AtlasEdge]] = None,
    ) -> EntityRollup:
        """Compute the relation rollup for a node."""

        node = self.repository.get_node(identifier)
        if not node:
            raise KeyError(f"Unknown entity: {identifier}")
        relation_map: Dict[RelationType, List[AtlasEdge]] = defaultdict(list)
        for edge in edges or self.repository.iter_edges():
            if edge.source_id == identifier:
                relation_map[edge.relation].append(edge)
        return EntityRollup(node=node, relations=relation_map)

    def entity_by_name(self, name: str) -> Optional[AtlasNode]:
        target = name.lower()
        for node in self.repository.iter_nodes():
            if node.name.lower() == target:
                return node
        return None

    def summary_snapshot(self) -> Dict[str, object]:
        """High-level snapshot for reports and diagnostics."""

        nodes = list(self.repository.iter_nodes())
        edges = list(self.repository.iter_edges())
        counts = defaultdict(int)
        for node in nodes:
            counts[node.entity_type.value] += 1
        relation_counts = defaultdict(int)
        for edge in edges:
            relation_counts[edge.relation.value] += 1
        return {
            "nodes": counts,
            "edges": relation_counts,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "recent_changes": [change.as_dict() for change in self.repository.recent_changes(10)],
        }
