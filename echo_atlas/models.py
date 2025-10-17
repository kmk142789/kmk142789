"""Domain models for the Echo Atlas graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional


class EntityType(str, Enum):
    """Supported atlas node entity types."""

    PERSON = "person"
    BOT = "bot"
    SERVICE = "service"
    REPO = "repo"
    KEY_REF = "key_ref"
    CHANNEL = "channel"


class ChannelKind(str, Enum):
    """Different channel modes for channel entities."""

    WEB = "web"
    CLI = "cli"
    WEBHOOK = "webhook"


class RelationType(str, Enum):
    """Relationship verbs captured in the atlas graph."""

    CONNECTS_TO = "CONNECTS_TO"
    OWNS = "OWNS"
    OPERATES = "OPERATES"
    DEPLOYS = "DEPLOYS"
    TRUSTS = "TRUSTS"
    MENTIONS = "MENTIONS"


@dataclass(slots=True)
class AtlasNode:
    """A graph node describing an entity within the atlas."""

    identifier: str
    name: str
    entity_type: EntityType
    attributes: Dict[str, object] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def as_dict(self) -> Dict[str, object]:
        """Return a serialisable representation of the node."""

        return {
            "id": self.identifier,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass(slots=True)
class AtlasEdge:
    """A directional relation between two nodes."""

    identifier: str
    source_id: str
    target_id: str
    relation: RelationType
    attributes: Dict[str, object] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def as_dict(self) -> Dict[str, object]:
        """Return a serialisable representation of the edge."""

        return {
            "id": self.identifier,
            "source": self.source_id,
            "target": self.target_id,
            "relation": self.relation.value,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass(slots=True)
class ChangeRecord:
    """Audit entry capturing modifications to the atlas graph."""

    identifier: str
    entity_id: str
    entity_type: str
    change_type: str
    payload: Dict[str, object]
    created_at: datetime

    def as_dict(self) -> Dict[str, object]:
        return {
            "id": self.identifier,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "change_type": self.change_type,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }


def normalise_name(name: str) -> str:
    """Normalise entity names for deterministic identifiers."""

    return "-".join(part for part in name.lower().replace("@", "at").split() if part)


def make_identifier(entity_type: EntityType, name: str, suffix: Optional[str] = None) -> str:
    """Construct a stable identifier for a node."""

    base = f"{entity_type.value}:{normalise_name(name)}"
    return f"{base}:{suffix}" if suffix else base


def edge_identifier(source_id: str, relation: RelationType, target_id: str) -> str:
    """Construct deterministic edge identifiers."""

    return f"edge:{source_id}:{relation.value}:{target_id}"


def ensure_iterable(value: Optional[Iterable[str]]) -> List[str]:
    """Convert ``value`` to a list, filtering empties."""

    if not value:
        return []
    return [item for item in value if item]
