"""Meta causal awareness engine for Echo cognition modules."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Callable, Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Tuple
from uuid import uuid4

from .pipelines import DEFAULT_PIPELINES, InferencePipeline
from .types import CausalLink, InferenceResult, MetaCausalSnapshot, Observation


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalise_tags(tags: Iterable[str] | None) -> Tuple[str, ...]:
    if not tags:
        return ()
    seen: MutableMapping[str, None] = {}
    for tag in tags:
        if not isinstance(tag, str):
            raise TypeError("tags must be strings")
        seen.setdefault(tag, None)
    return tuple(sorted(seen))


class MetaCausalAwarenessEngine:
    """Evolving causal graph that tracks awareness signals."""

    def __init__(
        self,
        *,
        anchor: str = "Our Forever Love",
        time_source: Optional[Callable[[], datetime]] = None,
        id_factory: Optional[Callable[[], str]] = None,
        register_default_pipelines: bool = True,
    ) -> None:
        self.anchor = anchor
        self._time_source = time_source or _utcnow
        self._id_factory = id_factory or (lambda: uuid4().hex)
        self._observations: Dict[str, Observation] = {}
        self._forward_edges: Dict[str, Dict[str, CausalLink]] = defaultdict(dict)
        self._reverse_edges: Dict[str, Dict[str, CausalLink]] = defaultdict(dict)
        self._pipelines: Dict[str, InferencePipeline] = {}
        self._inference_history: List[InferenceResult] = []
        self._snapshot_cache: MetaCausalSnapshot | None = None

        if register_default_pipelines:
            for name, pipeline in DEFAULT_PIPELINES.items():
                self.register_pipeline(name, pipeline)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    def current_time(self) -> datetime:
        """Return the engine's notion of *now*."""

        moment = self._time_source()
        if moment.tzinfo is None:
            return moment.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc)

    def available_pipelines(self) -> Tuple[str, ...]:
        return tuple(sorted(self._pipelines))

    def inference_history(self) -> Tuple[InferenceResult, ...]:
        return tuple(self._inference_history)

    # ------------------------------------------------------------------
    # Observation Management
    # ------------------------------------------------------------------
    def record_observation(
        self,
        source: str,
        signal: str,
        *,
        confidence: float = 1.0,
        tags: Iterable[str] | None = None,
        context: Mapping[str, Any] | None = None,
        moment: Optional[datetime] = None,
    ) -> Observation:
        """Record a new observation and return the stored dataclass."""

        if not isinstance(source, str) or not source:
            raise ValueError("source must be a non-empty string")
        if not isinstance(signal, str) or not signal:
            raise ValueError("signal must be a non-empty string")
        if not isinstance(confidence, (int, float)):
            raise TypeError("confidence must be numeric")

        created_at = moment or self.current_time()
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        observation = Observation(
            id=self._id_factory(),
            created_at=created_at.astimezone(timezone.utc),
            source=source,
            signal=signal,
            confidence=float(confidence),
            tags=_normalise_tags(tags),
            context=dict(sorted((context or {}).items())),
        )
        self._observations[observation.id] = observation
        self._snapshot_cache = None
        return observation

    def get_observation(self, observation_id: str) -> Observation:
        return self._observations[observation_id]

    # ------------------------------------------------------------------
    # Causal Links
    # ------------------------------------------------------------------
    def link(
        self,
        cause_id: str,
        effect_id: str,
        *,
        weight: float = 1.0,
        rationale: str = "",
    ) -> CausalLink:
        """Create a directed causal link between two observations."""

        if cause_id not in self._observations:
            raise KeyError(f"Unknown cause observation '{cause_id}'")
        if effect_id not in self._observations:
            raise KeyError(f"Unknown effect observation '{effect_id}'")
        if not isinstance(weight, (int, float)):
            raise TypeError("weight must be numeric")

        link = CausalLink(
            cause=cause_id,
            effect=effect_id,
            weight=float(weight),
            rationale=rationale,
            created_at=self.current_time(),
        )
        self._forward_edges[cause_id][effect_id] = link
        self._reverse_edges[effect_id][cause_id] = link
        self._snapshot_cache = None
        return link

    def iter_links(self) -> Iterator[CausalLink]:
        seen = set()
        for cause, edges in self._forward_edges.items():
            for effect, link in edges.items():
                if (cause, effect) in seen:
                    continue
                seen.add((cause, effect))
                yield link

    # ------------------------------------------------------------------
    # Pipelines
    # ------------------------------------------------------------------
    def register_pipeline(self, name: str, pipeline: InferencePipeline) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("pipeline name must be a non-empty string")
        if not callable(pipeline):
            raise TypeError("pipeline must be callable")
        self._pipelines[name] = pipeline

    def run_inference(
        self, observation_id: str, *, pipeline: str | None = None
    ) -> Tuple[InferenceResult, ...]:
        if observation_id not in self._observations:
            raise KeyError(f"Unknown observation '{observation_id}'")

        observation = self._observations[observation_id]
        pipelines: Iterable[Tuple[str, InferencePipeline]]
        if pipeline is not None:
            if pipeline not in self._pipelines:
                raise KeyError(f"Pipeline '{pipeline}' is not registered")
            pipelines = ((pipeline, self._pipelines[pipeline]),)
        else:
            pipelines = tuple(self._pipelines.items())

        results: List[InferenceResult] = []
        for name, fn in pipelines:
            try:
                result = fn(observation, self)
                if result.pipeline != name:
                    result = InferenceResult(
                        pipeline=name,
                        observation_id=observation_id,
                        verdict=result.verdict,
                        confidence=result.confidence,
                        created_at=result.created_at,
                        success=result.success,
                        notes=result.notes,
                    )
            except Exception as exc:
                result = InferenceResult(
                    pipeline=name,
                    observation_id=observation_id,
                    verdict="error",
                    confidence=0.0,
                    created_at=self.current_time(),
                    success=False,
                    notes={"error": str(exc), "type": exc.__class__.__name__},
                )
            self._inference_history.append(result)
            results.append(result)
        return tuple(results)

    # ------------------------------------------------------------------
    # Snapshot and Persistence
    # ------------------------------------------------------------------
    def snapshot(self) -> MetaCausalSnapshot:
        if self._snapshot_cache is not None:
            return self._snapshot_cache

        observations = tuple(
            obs.to_dict()
            for obs in sorted(self._observations.values(), key=lambda item: (item.created_at, item.id))
        )
        links = tuple(link.to_dict() for link in sorted(self.iter_links(), key=lambda l: (l.cause, l.effect)))

        metrics = {
            "observation_count": len(observations),
            "link_count": len(links),
            "sources": self._compute_source_metrics(),
            "degrees": self._compute_degrees(),
            "tags": self._compute_tag_metrics(),
            "most_recent_observation": self._most_recent_observation_time(),
        }
        payload = {
            "anchor": self.anchor,
            "observations": observations,
            "links": links,
            "metrics": metrics,
        }
        digest = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        snapshot = MetaCausalSnapshot(
            anchor=self.anchor,
            created_at=self.current_time(),
            observations=observations,
            links=links,
            metrics=metrics,
            digest=digest,
        )
        self._snapshot_cache = snapshot
        return snapshot

    def export_state(self) -> Dict[str, Any]:
        return self.snapshot().to_dict()

    # ------------------------------------------------------------------
    # Safety
    # ------------------------------------------------------------------
    def audit_integrity(self) -> Dict[str, Any]:
        from .safety import audit_integrity as _audit

        return _audit(self)

    def introspection(self) -> Dict[str, Any]:
        """Return a condensed status view of the engine state."""

        snapshot = self.snapshot()
        last_result = self._inference_history[-1] if self._inference_history else None
        return {
            "anchor": snapshot.anchor,
            "observation_count": snapshot.metrics["observation_count"],
            "link_count": snapshot.metrics["link_count"],
            "sources": snapshot.metrics["sources"],
            "tags": snapshot.metrics.get("tags", {}),
            "most_recent_observation": snapshot.metrics.get("most_recent_observation"),
            "last_inference": last_result.to_dict() if last_result else None,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _compute_source_metrics(self) -> Dict[str, Dict[str, Any]]:
        sources: Dict[str, Dict[str, Any]] = {}
        for observation in self._observations.values():
            bucket = sources.setdefault(
                observation.source,
                {"count": 0, "mean_confidence": 0.0},
            )
            bucket["count"] += 1
            bucket["mean_confidence"] += observation.confidence
        for bucket in sources.values():
            count = bucket["count"] or 1
            bucket["mean_confidence"] = bucket["mean_confidence"] / count
        return dict(sorted(sources.items()))

    def _compute_tag_metrics(self) -> Dict[str, Dict[str, Any]]:
        tags: Dict[str, Dict[str, Any]] = {}
        for observation in self._observations.values():
            for tag in observation.tags:
                bucket = tags.setdefault(tag, {"count": 0, "mean_confidence": 0.0})
                bucket["count"] += 1
                bucket["mean_confidence"] += observation.confidence
        for bucket in tags.values():
            count = bucket["count"] or 1
            bucket["mean_confidence"] = bucket["mean_confidence"] / count
        return dict(sorted(tags.items()))

    def _most_recent_observation_time(self) -> str | None:
        if not self._observations:
            return None
        latest = max(self._observations.values(), key=lambda obs: obs.created_at)
        return latest.created_at.astimezone(timezone.utc).isoformat()

    def _compute_degrees(self) -> Dict[str, Dict[str, Any]]:
        degrees: Dict[str, Dict[str, Any]] = {}
        for obs_id in self._observations:
            outgoing = self._forward_edges.get(obs_id, {})
            incoming = self._reverse_edges.get(obs_id, {})
            degrees[obs_id] = {
                "outgoing": len(outgoing),
                "incoming": len(incoming),
                "weight_out": sum(link.weight for link in outgoing.values()),
                "weight_in": sum(link.weight for link in incoming.values()),
            }
        return dict(sorted(degrees.items()))


__all__ = ["MetaCausalAwarenessEngine"]

