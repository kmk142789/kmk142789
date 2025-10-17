"""Domain models for the Echo Atlas graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional


class EntityType(str, Enum):
    """Allowed entity types for Atlas nodes."""

    PERSON = "Person"
    BOT = "Bot"
    SERVICE = "Service"
    REPO = "Repo"
    KEYREF = "KeyRef"
    CHANNEL = "Channel"


class ChannelKind(str, Enum):
    """Specific categories for channel entities."""

    WEB = "web"
    CLI = "cli"
    WEBHOOK = "webhook"


class RelationType(str, Enum):
    """Relations that connect Atlas entities."""

    CONNECTS_TO = "CONNECTS_TO"
    OWNS = "OWNS"
    OPERATES = "OPERATES"
    DEPLOYS = "DEPLOYS"
    TRUSTS = "TRUSTS"
    MENTIONS = "MENTIONS"


@dataclass(slots=True)
class Node:
    """A graph node."""

    identifier: str
    name: str
    entity_type: EntityType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        data = dict(self.metadata)
        data.update(
            {
                "id": self.identifier,
                "name": self.name,
                "entity_type": self.entity_type.value,
            }
        )
        return data


@dataclass(slots=True)
class Edge:
    """A directional graph edge."""

    identifier: str
    source: str
    target: str
    relation: RelationType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        data = dict(self.metadata)
        data.update(
            {
                "id": self.identifier,
                "source": self.source,
                "target": self.target,
                "relation": self.relation.value,
            }
        )
        return data


@dataclass(slots=True)
class AtlasSummary:
    """Aggregated snapshot of the atlas state."""

    totals: Mapping[str, int]
    relations: Mapping[str, int]
    recent_changes: list[Mapping[str, Any]]
    highlights: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "totals": dict(self.totals),
            "relations": dict(self.relations),
            "recent_changes": list(self.recent_changes),
            "highlights": self.highlights,
        }
