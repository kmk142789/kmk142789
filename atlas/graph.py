"""Core data structures for the Atlas federation graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List
import json


@dataclass(slots=True)
class ArtifactNode:
    """Represents a single artifact from a universe shard."""

    node_id: str
    universe: str
    artifact_id: str
    source: str
    metadata: Dict[str, Any]
    content: str
    dependencies: List[str] = field(default_factory=list)
    timestamp: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "universe": self.universe,
            "artifact_id": self.artifact_id,
            "source": self.source,
            "metadata": self.metadata,
            "content": self.content,
            "dependencies": list(self.dependencies),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ArtifactNode":
        return cls(
            node_id=payload["node_id"],
            universe=payload["universe"],
            artifact_id=payload["artifact_id"],
            source=payload["source"],
            metadata=dict(payload.get("metadata", {})),
            content=payload.get("content", ""),
            dependencies=list(payload.get("dependencies", [])),
            timestamp=payload.get("timestamp"),
        )


@dataclass(slots=True)
class Edge:
    """Represents a dependency edge between artifacts."""

    source: str
    target: str
    relation: str = "depends_on"

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "target": self.target, "relation": self.relation}

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Edge":
        return cls(source=payload["source"], target=payload["target"], relation=payload.get("relation", "depends_on"))


@dataclass
class FederationGraph:
    """Graph of artifacts collected from multiple universes."""

    universes: Dict[str, Dict[str, Any]]
    artifacts: List[ArtifactNode]
    edges: List[Edge]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "universes": self.universes,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "edges": [edge.to_dict() for edge in self.edges],
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "FederationGraph":
        universes = {key: dict(value) for key, value in payload.get("universes", {}).items()}
        artifacts = [ArtifactNode.from_dict(item) for item in payload.get("artifacts", [])]
        edges = [Edge.from_dict(item) for item in payload.get("edges", [])]
        return cls(universes=universes, artifacts=artifacts, edges=edges)

    @classmethod
    def load(cls, path: Path) -> "FederationGraph":
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return cls.from_dict(payload)

    def neighbors(self, node_id: str) -> List[ArtifactNode]:
        """Return downstream neighbors for *node_id*."""

        targets = {edge.target for edge in self.edges if edge.source == node_id}
        return [artifact for artifact in self.artifacts if artifact.node_id in targets]

    def sources(self, node_id: str) -> List[ArtifactNode]:
        """Return upstream sources for *node_id*."""

        sources = {edge.source for edge in self.edges if edge.target == node_id}
        return [artifact for artifact in self.artifacts if artifact.node_id in sources]

    def iter_universe(self, universe: str) -> Iterable[ArtifactNode]:
        """Iterate over nodes belonging to *universe*."""

        return (artifact for artifact in self.artifacts if artifact.universe == universe)

    def artifact_map(self) -> Dict[str, ArtifactNode]:
        """Return mapping of node ids to artifact instances."""

        return {artifact.node_id: artifact for artifact in self.artifacts}
