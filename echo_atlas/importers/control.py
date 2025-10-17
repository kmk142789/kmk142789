"""Importer for CONTROL.md."""

from __future__ import annotations

import re
from typing import List

from ..domain import Edge, EntityType, Node, RelationType
from ..utils import slugify
from .base import AtlasImporter, ImportBatch


class ControlImporter(AtlasImporter):
    """Parse CONTROL.md for ownership and service references."""

    OWNERSHIP_SECTION = re.compile(r"^## Ownership \+ Inventory", re.MULTILINE)

    def run(self) -> ImportBatch:
        path = self.root / "CONTROL.md"
        batch = ImportBatch()
        if not path.exists():
            return batch

        content = path.read_text(encoding="utf-8")
        sections = self._extract_sections(content)
        for category, entries in sections.items():
            for entry in entries:
                kind, value = self._parse_entry(entry)
                if not value:
                    continue
                node = self._node_for_entry(kind, value)
                if node is None:
                    continue
                batch.nodes.append(node)
                repo_id = slugify("repo", "echo")
                repo_node = Node(
                    identifier=repo_id,
                    name="Echo",
                    entity_type=EntityType.REPO,
                    metadata={"source": "CONTROL.md"},
                )
                batch.nodes.append(repo_node)
                relation = self._edge_for_entry(repo_id, node.identifier, kind)
                if relation:
                    batch.edges.append(relation)
        return batch

    def _extract_sections(self, content: str) -> dict[str, List[str]]:
        capture = {}
        current = None
        for line in content.splitlines():
            if line.startswith("## "):
                current = line.replace("##", "").strip()
                capture[current] = []
            elif line.startswith("- ") and current:
                capture[current].append(line[2:].strip())
        return capture

    def _parse_entry(self, entry: str) -> tuple[str, str]:
        if ":" in entry:
            kind, value = entry.split(":", 1)
            return kind.strip(), value.strip()
        return "", entry.strip()

    def _node_for_entry(self, kind: str, value: str) -> Node | None:
        metadata = {"source": "CONTROL.md", "category": kind}
        if kind.lower().startswith("bots"):
            identifier = slugify("bot", value)
            return Node(identifier=identifier, name=value, entity_type=EntityType.BOT, metadata=metadata)
        if kind.lower().startswith("ci"):
            identifier = slugify("service", value)
            return Node(identifier=identifier, name=value, entity_type=EntityType.SERVICE, metadata=metadata)
        if kind.lower().startswith("external"):
            identifier = slugify("service", value)
            return Node(identifier=identifier, name=value, entity_type=EntityType.SERVICE, metadata=metadata)
        if kind.lower().startswith("orgs"):
            identifier = slugify("service", value)
            return Node(identifier=identifier, name=value, entity_type=EntityType.SERVICE, metadata=metadata)
        return None

    def _edge_for_entry(self, repo_id: str, target: str, kind: str) -> Edge | None:
        rel = RelationType.CONNECTS_TO
        if kind.lower().startswith("bots"):
            rel = RelationType.OPERATES
        elif kind.lower().startswith("ci"):
            rel = RelationType.DEPLOYS
        elif kind.lower().startswith("orgs"):
            rel = RelationType.TRUSTS
        identifier = slugify(rel.value, repo_id, target)
        return Edge(
            identifier=identifier,
            source=repo_id,
            target=target,
            relation=rel,
            metadata={"source": "CONTROL.md", "category": kind},
        )
