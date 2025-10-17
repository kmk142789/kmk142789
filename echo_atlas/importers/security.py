"""Importer for SECURITY.md data."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Set

from ..models import AtlasNode, ChannelKind, EntityType, RelationType, make_identifier
from ..repository import AtlasRepository
from .base import AtlasImporter, ImporterResult


EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class SecurityImporter(AtlasImporter):
    name = "security"

    def run(self, repository: AtlasRepository, root: Path) -> ImporterResult:
        path = root / "SECURITY.md"
        if not path.exists():
            return ImporterResult(self.name, nodes=0, edges=0)

        text = path.read_text(encoding="utf-8")
        channel_node = AtlasNode(
            identifier=make_identifier(EntityType.CHANNEL, "SECURITY.md"),
            name="SECURITY.md",
            entity_type=EntityType.CHANNEL,
            attributes={"path": str(path), "kind": ChannelKind.WEB.value},
        )
        repository.upsert_node(channel_node)
        nodes = 1
        edges = 0

        emails: Set[str] = set(EMAIL_PATTERN.findall(text))
        for email in sorted(emails):
            node = AtlasNode(
                identifier=make_identifier(EntityType.KEY_REF, email),
                name=email,
                entity_type=EntityType.KEY_REF,
                attributes={"kind": "email", "source": "SECURITY.md"},
            )
            repository.upsert_node(node)
            repository.ensure_edge(
                channel_node.identifier,
                RelationType.MENTIONS,
                node.identifier,
                attributes={"context": "reporting"},
            )
            nodes += 1
            edges += 1

        expectations = self._extract_expectations(text)
        for item in expectations:
            node = AtlasNode(
                identifier=make_identifier(EntityType.SERVICE, item),
                name=item,
                entity_type=EntityType.SERVICE,
                attributes={"source": "SECURITY.md", "category": "expectation"},
            )
            repository.upsert_node(node)
            repository.ensure_edge(
                channel_node.identifier,
                RelationType.TRUSTS,
                node.identifier,
                attributes={"context": "expectation"},
            )
            nodes += 1
            edges += 1

        return ImporterResult(self.name, nodes=nodes, edges=edges)

    def _extract_expectations(self, text: str) -> Iterable[str]:
        capture = False
        items: Set[str] = set()
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("## Expectations"):
                capture = True
                continue
            if capture:
                if line.startswith("## "):
                    break
                if line.startswith("- "):
                    items.add(line[2:].strip())
        return sorted(items)
