"""High-level services for the Echo Atlas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .importers import ImporterResult, run_importers
from .models import AtlasNode, EntityType, RelationType, make_identifier
from .query import AtlasQuery
from .repository import AtlasRepository
from .visualize import AtlasVisualizer


@dataclass(slots=True)
class SyncResult:
    """Aggregate summary of a sync operation."""

    importer_results: List[ImporterResult]
    report_path: Path
    svg_path: Path


class AtlasService:
    """Coordinate imports, reports, and visualisations."""

    def __init__(self, repository: Optional[AtlasRepository] = None, *, root: Optional[Path] = None) -> None:
        self.root = root or Path.cwd()
        self.repository = repository or AtlasRepository()
        self.query = AtlasQuery(self.repository)
        self.visualizer = AtlasVisualizer(self.repository)

    def seed_demo_data(self) -> None:
        """Populate the atlas with a baseline set of nodes."""

        maintainer = AtlasNode(
            identifier=make_identifier(EntityType.PERSON, "echo-maintainers"),
            name="Echo Maintainers",
            entity_type=EntityType.PERSON,
            attributes={"kind": "team", "notes": "Core Echo maintainers"},
        )
        api_service = AtlasNode(
            identifier=make_identifier(EntityType.SERVICE, "echo-api"),
            name="Echo API",
            entity_type=EntityType.SERVICE,
            attributes={"surface": "api", "status": "active"},
        )
        atlas_service = AtlasNode(
            identifier=make_identifier(EntityType.SERVICE, "echo-atlas"),
            name="Echo Atlas",
            entity_type=EntityType.SERVICE,
            attributes={"surface": "internal", "status": "beta"},
        )
        channel = AtlasNode(
            identifier=make_identifier(EntityType.CHANNEL, "atlas-seed"),
            name="Atlas Seed",
            entity_type=EntityType.CHANNEL,
            attributes={"kind": "cli", "source": "seed"},
        )
        for node in [maintainer, api_service, atlas_service, channel]:
            self.repository.upsert_node(node)
        self.repository.ensure_edge(maintainer.identifier, RelationType.OWNS, api_service.identifier)
        self.repository.ensure_edge(maintainer.identifier, RelationType.OPERATES, atlas_service.identifier)
        self.repository.ensure_edge(channel.identifier, RelationType.MENTIONS, maintainer.identifier)

    def sync(self) -> SyncResult:
        """Run all importers, produce artefacts, and return the summary."""

        self.seed_demo_data()
        importer_results = run_importers(self.repository, self.root)
        report_path = self.write_report()
        svg_path = self.generate_visualisations()
        return SyncResult(importer_results=importer_results, report_path=report_path, svg_path=svg_path)

    def write_report(self) -> Path:
        report_path = self.root / "docs" / "ATLAS_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = self.query.summary_snapshot()
        lines = [
            "# Echo Atlas Report",
            "",
            f"_Generated: {datetime.now(tz=timezone.utc).isoformat()}_",
            "",
            "## Ownership",
        ]
        ownership = self.query.ownership_summary()
        if not ownership:
            lines.append("No ownership data available yet.")
        else:
            for group, entries in ownership.items():
                lines.append(f"### {group.title()}")
                for entry in entries:
                    entity = entry["entity"]
                    lines.append(f"- **{entity['name']}** ({entity['entity_type']})")
                    for relation, rel_edges in entry["relations"].items():
                        for rel_edge in rel_edges:
                            target_node = self.repository.get_node(rel_edge["target"])
                            target_name = target_node.name if target_node else rel_edge["target"]
                            lines.append(
                                f"  - {relation} → {target_name}"
                            )
        lines.extend(
            [
                "",
                "## Assets",
                f"- Total nodes: {snapshot['total_nodes']}",
                f"- Total edges: {snapshot['total_edges']}",
                "",
                "## Endpoints & Automations",
            ]
        )
        for edge in self.repository.iter_edges():
            if edge.relation in {RelationType.OPERATES, RelationType.DEPLOYS}:
                source = self.repository.get_node(edge.source_id)
                target = self.repository.get_node(edge.target_id)
                source_name = source.name if source else edge.source_id
                target_name = target.name if target else edge.target_id
                lines.append(f"- {source_name} {edge.relation.value.lower()} {target_name}")
        lines.extend(["", "## Recent Changes"])
        changes = snapshot["recent_changes"]
        if not changes:
            lines.append("No changes recorded yet.")
        else:
            for change in changes:
                lines.append(
                    f"- {change['created_at']}: {change['entity_type']} {change['entity_id']} ({change['change_type']})"
                )
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return report_path

    def generate_visualisations(self) -> Path:
        dot_path = self.root / "artifacts" / "atlas_graph.dot"
        svg_path = self.root / "artifacts" / "atlas_graph.svg"
        self.visualizer.write_assets(dot_path=dot_path, svg_path=svg_path)
        return svg_path

    def entity_summary(self, name: str) -> dict:
        node = self.query.entity_by_name(name)
        if not node:
            raise KeyError(f"Unknown entity: {name}")
        rollup = self.query.rollup_for_entity(node.identifier)
        return rollup.to_dict()
