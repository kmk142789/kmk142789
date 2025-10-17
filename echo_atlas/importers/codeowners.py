"""Importer for CODEOWNERS."""

from __future__ import annotations

from pathlib import Path

from ..domain import Edge, EntityType, Node, RelationType
from ..utils import slugify
from .base import AtlasImporter, ImportBatch


class CodeownersImporter(AtlasImporter):
    """Parse CODEOWNERS to build ownership edges."""

    def run(self) -> ImportBatch:
        path = self.root / ".github" / "CODEOWNERS"
        batch = ImportBatch()
        if not path.exists():
            return batch

        repo_id = slugify("repo", "echo")
        repo_node = Node(
            identifier=repo_id,
            name="Echo",
            entity_type=EntityType.REPO,
            metadata={"source": "CODEOWNERS"},
        )
        batch.nodes.append(repo_node)

        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            _, *owners = parts
            for owner in owners:
                if not owner.startswith("@"):
                    continue
                handle = owner[1:]
                node = Node(
                    identifier=slugify("person", handle),
                    name=handle,
                    entity_type=EntityType.PERSON,
                    metadata={"handle": owner},
                )
                batch.nodes.append(node)
                edge = Edge(
                    identifier=slugify("owns", handle, repo_id, parts[0]),
                    source=node.identifier,
                    target=repo_id,
                    relation=RelationType.OWNS,
                    metadata={"path": parts[0], "source": "CODEOWNERS"},
                )
                batch.edges.append(edge)
        return batch
