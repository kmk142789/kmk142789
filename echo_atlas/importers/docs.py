"""Importer for documentation under docs/."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Set

from ..models import AtlasNode, ChannelKind, EntityType, RelationType, make_identifier
from ..repository import AtlasRepository
from .base import AtlasImporter, ImporterResult


HANDLE_RE = re.compile(r"@([A-Za-z0-9_.-]+)")


class DocsImporter(AtlasImporter):
    name = "docs"

    def run(self, repository: AtlasRepository, root: Path) -> ImporterResult:
        docs_dir = root / "docs"
        if not docs_dir.exists():
            return ImporterResult(self.name, nodes=0, edges=0)

        nodes = 0
        edges = 0
        seen_handles: Set[str] = set()
        seen_channels: Set[str] = set()
        for path in docs_dir.rglob("*.md"):
            channel = AtlasNode(
                identifier=make_identifier(EntityType.CHANNEL, str(path.relative_to(root))),
                name=str(path.relative_to(root)),
                entity_type=EntityType.CHANNEL,
                attributes={"path": str(path), "kind": ChannelKind.WEB.value},
            )
            repository.upsert_node(channel)
            if channel.identifier not in seen_channels:
                nodes += 1
                seen_channels.add(channel.identifier)
            handles: Set[str] = set()
            for handle in HANDLE_RE.findall(path.read_text(encoding="utf-8")):
                handles.add(handle)
            for handle in sorted(handles):
                entity_type = EntityType.BOT if handle.endswith("bot") else EntityType.PERSON
                node = AtlasNode(
                    identifier=make_identifier(entity_type, handle),
                    name=handle,
                    entity_type=entity_type,
                    attributes={"source": str(path.relative_to(root))},
                )
                repository.upsert_node(node)
                if node.identifier not in seen_handles:
                    nodes += 1
                    seen_handles.add(node.identifier)
                repository.ensure_edge(
                    channel.identifier,
                    RelationType.MENTIONS,
                    node.identifier,
                    attributes={"context": "docs"},
                )
                edges += 1
        return ImporterResult(self.name, nodes=nodes, edges=edges)
