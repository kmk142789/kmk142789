"""Importer for SECURITY.md."""

from __future__ import annotations

from ..domain import Edge, EntityType, Node, RelationType
from ..utils import slugify
from .base import AtlasImporter, ImportBatch


class SecurityImporter(AtlasImporter):
    """Create nodes for security documentation and trust relationships."""

    def run(self) -> ImportBatch:
        path = self.root / "SECURITY.md"
        batch = ImportBatch()
        if not path.exists():
            return batch

        doc_node = Node(
            identifier=slugify("doc", "security"),
            name="SECURITY.md",
            entity_type=EntityType.REPO,
            metadata={"path": str(path)},
        )
        channel_node = Node(
            identifier=slugify("channel", "security", "web"),
            name="Security Contact",
            entity_type=EntityType.CHANNEL,
            metadata={"kind": "web", "contact": "security@example.org"},
        )
        batch.nodes.extend([doc_node, channel_node])
        batch.edges.append(
            Edge(
                identifier=slugify("mentions", doc_node.identifier, channel_node.identifier),
                source=doc_node.identifier,
                target=channel_node.identifier,
                relation=RelationType.MENTIONS,
                metadata={"source": "SECURITY.md"},
            )
        )
        return batch
