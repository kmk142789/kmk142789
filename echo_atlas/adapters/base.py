"""Storage adapter interfaces for the Echo Atlas."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Iterator, Optional

from ..models import AtlasEdge, AtlasNode, ChangeRecord


class StorageAdapter(ABC):
    """Abstract base class for atlas storage backends."""

    @abstractmethod
    def initialise(self) -> None:
        """Create the necessary schema objects if they do not exist."""

    @abstractmethod
    def upsert_node(self, node: AtlasNode) -> AtlasNode:
        """Persist ``node`` and return the stored record."""

    @abstractmethod
    def upsert_edge(self, edge: AtlasEdge) -> AtlasEdge:
        """Persist ``edge`` and return the stored record."""

    @abstractmethod
    def remove_edge(self, identifier: str) -> None:
        """Delete an edge by identifier."""

    @abstractmethod
    def iter_nodes(self) -> Iterator[AtlasNode]:
        """Iterate over all nodes."""

    @abstractmethod
    def iter_edges(self) -> Iterator[AtlasEdge]:
        """Iterate over all edges."""

    @abstractmethod
    def get_node(self, identifier: str) -> Optional[AtlasNode]:
        """Retrieve a node by identifier."""

    @abstractmethod
    def get_edges_for(self, identifier: str) -> Iterable[AtlasEdge]:
        """Return edges connected to a node."""

    @abstractmethod
    def log_change(self, change: ChangeRecord) -> None:
        """Record a change event."""

    @abstractmethod
    def recent_changes(self, limit: int = 20) -> Iterable[ChangeRecord]:
        """Return the most recent change records."""

    @abstractmethod
    def close(self) -> None:
        """Release any open resources."""
