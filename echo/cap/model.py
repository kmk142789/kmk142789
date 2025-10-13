"""Capability graph primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Set


@dataclass(frozen=True)
class Capability:
    """Definition of a single capability node in the graph."""

    name: str
    version: str = "0.1.0"
    requires: Set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "Capability":
        """Build a capability from a mapping produced by JSON/YAML deserialisers."""

        name = str(payload.get("name"))
        version = str(payload.get("version", "0.1.0"))
        requires_iter: Iterable[str] = payload.get("requires", [])  # type: ignore[assignment]
        requires = {str(dep) for dep in requires_iter}
        return cls(name=name, version=version, requires=requires)


@dataclass
class CapState:
    """Tracks the set of capabilities that are currently provided."""

    provided: Set[str] = field(default_factory=set)

    def has(self, cap: str) -> bool:
        return cap in self.provided


__all__ = ["Capability", "CapState"]
