"""Importer for CODEOWNERS metadata."""

from __future__ import annotations

from pathlib import Path
from typing import List

from ..models import AtlasNode, EntityType, RelationType, make_identifier
from ..repository import AtlasRepository
from .base import AtlasImporter, ImporterResult


class CodeOwnersImporter(AtlasImporter):
    name = "codeowners"

    def run(self, repository: AtlasRepository, root: Path) -> ImporterResult:
        path = root / ".github" / "CODEOWNERS"
        if not path.exists():
            return ImporterResult(self.name, nodes=0, edges=0)

        nodes = 0
        edges = 0
        seen_patterns: set[str] = set()
        seen_entities: set[str] = set()
        for pattern, owners in self._parse(path):
            repo_node = AtlasNode(
                identifier=make_identifier(EntityType.REPO, pattern),
                name=pattern,
                entity_type=EntityType.REPO,
                attributes={"source": "CODEOWNERS"},
            )
            repository.upsert_node(repo_node)
            if pattern not in seen_patterns:
                nodes += 1
                seen_patterns.add(pattern)
            for owner in owners:
                entity_type = EntityType.BOT if owner.endswith("bot") else EntityType.PERSON
                owner_node = AtlasNode(
                    identifier=make_identifier(entity_type, owner),
                    name=owner,
                    entity_type=entity_type,
                    attributes={"source": "CODEOWNERS"},
                )
                repository.upsert_node(owner_node)
                if owner_node.identifier not in seen_entities:
                    nodes += 1
                    seen_entities.add(owner_node.identifier)
                repository.ensure_edge(
                    owner_node.identifier,
                    RelationType.OWNS,
                    repo_node.identifier,
                    attributes={"pattern": pattern},
                )
                edges += 1
        return ImporterResult(self.name, nodes=nodes, edges=edges)

    def _parse(self, path: Path) -> List[tuple[str, List[str]]]:
        entries: List[tuple[str, List[str]]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 2:
                continue
            pattern = parts[0]
            owners = [owner.lstrip("@") for owner in parts[1:]]
            entries.append((pattern, owners))
        return entries
