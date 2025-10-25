"""High-level orchestration utilities for :mod:`echo.hypernova`."""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, MutableMapping, Optional, Sequence

from .architecture import HypernovaBlueprint, assemble_blueprint
from .renderers import HypernovaAsciiRenderer, HypernovaJsonRenderer, HypernovaTextRenderer
from .saga import HypernovaSagaBuilder


@dataclass(slots=True)
class OrchestrationConfig:
    """Configuration options accepted by :class:`HypernovaOrchestrator`."""

    domain_names: Sequence[str] = ("Aurora", "Quantum Veil", "Echo Bridge")
    include_ascii_map: bool = True
    include_text_registry: bool = True
    include_saga: bool = True
    metadata: MutableMapping[str, str] = field(default_factory=dict)

    def enriched_metadata(self) -> Mapping[str, str]:
        payload = dict(self.metadata)
        payload.setdefault("generated_at", _dt.datetime.utcnow().isoformat() + "Z")
        payload.setdefault("domain_count", str(len(self.domain_names)))
        return payload


class HypernovaOrchestrator:
    """Facade that spins up the full hypernova generation pipeline."""

    def __init__(self, config: Optional[OrchestrationConfig] = None) -> None:
        self.config = config or OrchestrationConfig()
        self.blueprint: Optional[HypernovaBlueprint] = None

    # ------------------------------------------------------------------
    # Pipeline assembly
    # ------------------------------------------------------------------

    def _ensure_blueprint(self) -> HypernovaBlueprint:
        if self.blueprint is None:
            self.blueprint = assemble_blueprint(self.config.domain_names)
        return self.blueprint

    def build_blueprint(self) -> HypernovaBlueprint:
        return self._ensure_blueprint()

    def build_saga(self) -> List[str]:
        blueprint = self._ensure_blueprint()
        if not self.config.include_saga:
            return []
        saga = HypernovaSagaBuilder(blueprint)
        return [beat.to_text() for beat in saga.build_saga()]

    def render_ascii_map(self, *, width: int = 80, height: int = 24) -> Optional[str]:
        if not self.config.include_ascii_map:
            return None
        blueprint = self._ensure_blueprint()
        renderer = HypernovaAsciiRenderer(blueprint=blueprint, width=width, height=height)
        return renderer.render()

    def render_text_registry(self) -> Optional[str]:
        if not self.config.include_text_registry:
            return None
        blueprint = self._ensure_blueprint()
        renderer = HypernovaTextRenderer(blueprint=blueprint)
        registry = [renderer.render_overview(), "", renderer.render_nodes()]
        return "\n\n".join(registry)

    def render_json_payload(self) -> str:
        blueprint = self._ensure_blueprint()
        renderer = HypernovaJsonRenderer(blueprint=blueprint)
        payload = {
            "metadata": self.config.enriched_metadata(),
            "hypernova": json.loads(renderer.render()),
        }
        return json.dumps(payload, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Composite artifact
    # ------------------------------------------------------------------

    def compose_artifact(self) -> Dict[str, object]:
        blueprint = self._ensure_blueprint()
        saga_builder = HypernovaSagaBuilder(blueprint)
        saga_beats = saga_builder.build_saga() if self.config.include_saga else []
        artifact = {
            "metadata": self.config.enriched_metadata(),
            "domains": [domain.name for domain in blueprint.domains],
            "strata": [stratum.name for stratum in blueprint.strata],
            "pulse_streams": [stream.stream_id for stream in blueprint.pulse_streams],
            "chronicle_topics": saga_builder.chronicle_topics(),
            "saga": [beat.to_text() for beat in saga_beats],
        }
        if self.config.include_ascii_map:
            artifact["ascii_map"] = HypernovaAsciiRenderer(blueprint).render()
        if self.config.include_text_registry:
            text_renderer = HypernovaTextRenderer(blueprint)
            artifact["text_registry"] = {
                "overview": text_renderer.render_overview(),
                "nodes": text_renderer.render_nodes(),
            }
        return artifact

    def render_artifact_text(self) -> str:
        artifact = self.compose_artifact()
        metadata_lines = [f"{key}: {value}" for key, value in sorted(artifact["metadata"].items())]
        sections = ["# Hypernova Artifact", "", "## Metadata", *metadata_lines, ""]
        if "ascii_map" in artifact:
            sections.extend(["## ASCII Map", artifact["ascii_map"], ""])
        if "text_registry" in artifact:
            registry = artifact["text_registry"]
            sections.extend(["## Overview", registry["overview"], "", "## Nodes", registry["nodes"], ""])
        if artifact.get("saga"):
            sections.append("## Saga")
            sections.extend(artifact["saga"])
        return "\n".join(sections).strip()


__all__ = ["HypernovaOrchestrator", "OrchestrationConfig"]
