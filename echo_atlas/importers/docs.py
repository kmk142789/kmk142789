"""Importer for docs directory."""

from __future__ import annotations

from pathlib import Path

from ..domain import Edge, EntityType, Node, RelationType
from ..utils import slugify
from .base import AtlasImporter, ImportBatch


class DocsImporter(AtlasImporter):
    """Create channel nodes for published docs."""

    def run(self) -> ImportBatch:
        docs_path = self.root / "docs"
        batch = ImportBatch()
        if not docs_path.exists():
            return batch

        for path in docs_path.rglob("*.md"):
            relative = path.relative_to(self.root)
            identifier = slugify("doc", str(relative))
            node = Node(
                identifier=identifier,
                name=relative.as_posix(),
                entity_type=EntityType.CHANNEL,
                metadata={"kind": "web", "path": str(relative)},
            )
            batch.nodes.append(node)
            repo_id = slugify("repo", "echo")
            batch.edges.append(
                Edge(
                    identifier=slugify("mentions", repo_id, identifier),
                    source=repo_id,
                    target=identifier,
                    relation=RelationType.MENTIONS,
                    metadata={"source": "docs"},
                )
            )
        return batch
