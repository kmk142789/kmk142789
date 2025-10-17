"""Importer for CONTROL.md metadata."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, Tuple

from ..models import AtlasNode, ChannelKind, EntityType, RelationType, make_identifier
from ..repository import AtlasRepository
from .base import AtlasImporter, ImporterResult


class ControlImporter(AtlasImporter):
    name = "control"

    def run(self, repository: AtlasRepository, root: Path) -> ImporterResult:
        path = root / "CONTROL.md"
        if not path.exists():
            return ImporterResult(self.name, nodes=0, edges=0)

        lines = list(self.read_lines(path))
        inventory = self._parse_inventory(lines)
        channel_node = AtlasNode(
            identifier=make_identifier(EntityType.CHANNEL, "CONTROL.md"),
            name="CONTROL.md",
            entity_type=EntityType.CHANNEL,
            attributes={"path": str(path), "kind": ChannelKind.WEB.value},
        )
        repository.upsert_node(channel_node)
        node_count = 1
        edge_count = 0
        for category, entries in inventory.items():
            for entry in entries:
                node = AtlasNode(
                    identifier=make_identifier(entry[0], entry[1]),
                    name=entry[1],
                    entity_type=entry[0],
                    attributes={"source": "CONTROL.md", "category": category},
                )
                repository.upsert_node(node)
                repository.ensure_edge(
                    channel_node.identifier,
                    RelationType.MENTIONS,
                    node.identifier,
                    attributes={"category": category},
                )
                node_count += 1
                edge_count += 1
        return ImporterResult(self.name, nodes=node_count, edges=edge_count)

    def _parse_inventory(
        self, lines: Iterable[str]
    ) -> Dict[str, Tuple[Tuple[EntityType, str], ...]]:
        capture = False
        parsed: Dict[str, Tuple[Tuple[EntityType, str], ...]] = {}
        for raw in lines:
            line = raw.strip()
            if line.startswith("## Ownership"):
                capture = True
                continue
            if capture and line.startswith("---"):
                break
            if capture and line.startswith("- ") and ":" in line:
                heading, items = line[2:].split(":", 1)
                category = heading.strip().lower()
                parsed[category] = tuple(self._parse_items(category, items))
        return parsed

    def _parse_items(self, category: str, text: str) -> Iterable[Tuple[EntityType, str]]:
        entity_type = {
            "orgs": EntityType.SERVICE,
            "ci": EntityType.SERVICE,
            "bots": EntityType.BOT,
            "external": EntityType.SERVICE,
        }.get(category, EntityType.SERVICE)
        for raw_item in text.split(","):
            cleaned = raw_item.strip()
            if not cleaned:
                continue
            name = re.sub(r"\s*\(.*?\)", "", cleaned).strip()
            yield entity_type, name
