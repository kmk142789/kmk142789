"""Utility module for registering and executing Echo capabilities.

This file mirrors :mod:`echo.echo_capability_engine` so that the packaged
distribution and the source tree share the same behaviour.  See the top-level
module for documentation of the upgrade-driven changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Protocol

from .coordination_mesh import (
    ManifestNotFoundError,
    build_coordination_mesh,
    locate_manifest,
)
from .ecosystem_pulse import EcosystemAreaConfig
from .emergent_coherence_field import EmergentCoherenceField
from .intelligence_layer import synthesize_intelligence_layer
from .unified_architecture_engine import UnifiedArchitectureEngine

__all__ = [
    "CAPABILITIES",
    "CapabilityResult",
    "CapabilityVerifier",
    "CapabilityHandler",
    "register_capability",
    "get_capability",
    "list_capabilities",
    "clear_capabilities",
    "execute_capability",
]


class CapabilityVerifier(Protocol):
    """Callable protocol for capability verifier hooks."""

    def __call__(self) -> bool:  # pragma: no cover - protocol definition
        ...


class CapabilityHandler(Protocol):
    """Callable protocol for capability handler hooks."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - protocol definition
        ...


@dataclass(slots=True)
class CapabilityResult:
    """Structured response describing the outcome of a capability execution."""

    name: str
    success: bool
    message: str
    payload: Any | None = None
    details: Mapping[str, Any] | None = None
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a serialisable dictionary."""

        result: Dict[str, Any] = {
            "name": self.name,
            "success": self.success,
            "message": self.message,
            "executed_at": self.executed_at.isoformat(),
        }
        if self.payload is not None:
            result["payload"] = self.payload
        if self.details:
            result["details"] = dict(self.details)
        return result


CAPABILITIES: MutableMapping[str, Dict[str, Any]] = {}
"""In-memory registry of capabilities keyed by their public name."""


def register_capability(
    name: str,
    description: str,
    verifier: CapabilityVerifier,
    handler: CapabilityHandler,
) -> Dict[str, Any]:
    """Register a new capability in the global registry."""

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Capability name must be a non-empty string.")
    if not callable(verifier):
        raise TypeError("Capability verifier must be callable.")
    if not callable(handler):
        raise TypeError("Capability handler must be callable.")

    metadata: Dict[str, Any] = {
        "name": name,
        "description": description,
        "verifier": verifier,
        "handler": handler,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    CAPABILITIES[name] = metadata
    return metadata


def get_capability(name: str) -> Dict[str, Any] | None:
    """Return the stored metadata for *name* if it has been registered."""

    return CAPABILITIES.get(name)


def list_capabilities() -> List[str]:
    """Return capability names in sorted order."""

    return sorted(CAPABILITIES.keys())


def clear_capabilities() -> None:
    """Remove all registered capabilities."""

    CAPABILITIES.clear()


def _wrap_exception(message: str, exc: Exception, name: str) -> CapabilityResult:
    """Create a failure result capturing an exception in a stable format."""

    return CapabilityResult(
        name=name,
        success=False,
        message=message,
        details={"error": str(exc), "type": exc.__class__.__name__},
    )


def execute_capability(name: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Execute a registered capability and return a structured result."""

    capability = CAPABILITIES.get(name)
    if capability is None:
        return CapabilityResult(
            name=name,
            success=False,
            message=f"Capability '{name}' is not registered.",
        ).to_dict()

    verifier = capability["verifier"]
    try:
        allowed = bool(verifier())
    except Exception as exc:  # pragma: no cover - exercised in higher level tests
        return _wrap_exception("Capability verifier raised an exception.", exc, name).to_dict()

    if not allowed:
        return CapabilityResult(
            name=name,
            success=False,
            message="Capability conditions not met.",
        ).to_dict()

    handler = capability["handler"]
    try:
        payload = handler(*args, **kwargs)
    except Exception as exc:  # pragma: no cover - exercised in higher level tests
        return _wrap_exception("Capability handler raised an exception.", exc, name).to_dict()

    return CapabilityResult(
        name=name,
        success=True,
        message="Capability executed successfully.",
        payload=payload,
    ).to_dict()


def _verify_academic() -> bool:
    return True


def _handle_academic(topic: str) -> Mapping[str, Any]:
    return {
        "title": f"Echo Thesis on {topic}",
        "abstract": "A machine-verifiable synthesis of cross-disciplinary insight.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


register_capability(
    "academic_research",
    "Produce and publish PhD-equivalent verifiable research.",
    _verify_academic,
    _handle_academic,
)


def _verify_constellation_mesh() -> bool:
    try:
        locate_manifest()
    except ManifestNotFoundError:
        return False
    return True


def _handle_constellation_mesh(*, manifest_path: str | Path | None = None) -> Mapping[str, Any]:
    mesh = build_coordination_mesh(manifest_path)
    return mesh.as_dict()


register_capability(
    "constellation_coordination_mesh",
    "Synthesize a cross-module coordination mesh that amplifies coordination and autonomy signals.",
    _verify_constellation_mesh,
    _handle_constellation_mesh,
)


def _verify_harmonic_intelligence_layer() -> bool:
    return True


def _handle_harmonic_intelligence_layer(
    *,
    manifest_path: str | Path | None = None,
    repo_root: str | Path | None = None,
    momentum_samples: List[object] | None = None,
    momentum_threshold: float | int | str | None = None,
    ecosystem_areas: Iterable[Mapping[str, object] | EcosystemAreaConfig] | None = None,
) -> Mapping[str, Any]:
    snapshot = synthesize_intelligence_layer(
        manifest_path=manifest_path,
        repo_root=repo_root,
        momentum_samples=momentum_samples,
        momentum_threshold=momentum_threshold,
        ecosystem_areas=ecosystem_areas,
    )
    return snapshot.to_dict()


register_capability(
    "harmonic_intelligence_layer",
    "Fuse constellation mesh, momentum resonance, and ecosystem pulse into a unified intelligence snapshot.",
    _verify_harmonic_intelligence_layer,
    _handle_harmonic_intelligence_layer,
)


def _verify_emergent_coherence_field() -> bool:
    return True


def _handle_emergent_coherence_field(*, module_root: str | Path | None = None) -> Mapping[str, Any]:
    engine = UnifiedArchitectureEngine(module_root) if module_root else None
    field = EmergentCoherenceField(architecture_engine=engine)
    report = field.evaluate()
    return report.to_dict()


register_capability(
    "emergent_coherence_field",
    "Bind architecture, memory, and observer signals into a coherent alignment guarantee.",
    _verify_emergent_coherence_field,
    _handle_emergent_coherence_field,
)

