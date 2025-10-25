"""Adapters for translating Harmonix cycle snapshots into Atlas shards."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Sequence
import json


DEFAULT_UNIVERSE = "Harmonix"


@dataclass(slots=True)
class HarmonixCycleArtifact:
    """Materialised representation of a Harmonix cycle snapshot."""

    universe: str
    artifact_id: str
    content: str
    metadata: Dict[str, Any]
    dependencies: List[str]
    timestamp: str | None
    generated_at: str | None


def iter_harmonix_payloads(root: Path, *, default_universe: str = DEFAULT_UNIVERSE) -> Iterator[Dict[str, Any]]:
    """Yield shard-style payloads derived from Harmonix snapshots.

    Parameters
    ----------
    root:
        Directory containing Harmonix cycle snapshots. Files are discovered
        recursively and may contain either a single cycle record or multiple
        cycles (for example the CLI ``run_cycles`` output).
    default_universe:
        Fallback universe label when snapshots do not provide an explicit one.

    Yields
    ------
    Dict[str, Any]
        Payload compatible with Cosmos/Fractal shards. Each payload contains a
        ``universe`` field along with ``artifacts`` describing the cycle
        snapshots for that universe.
    """

    if not root.exists():
        return

    universes: Dict[str, Dict[str, Any]] = {}

    for path in sorted(p for p in root.rglob("*.json") if p.is_file()):
        for cycle in _load_cycles(path, root=root, default_universe=default_universe):
            payload = universes.setdefault(
                cycle.universe,
                {"universe": cycle.universe, "artifacts": [], "generated_at": None},
            )
            artifact = {
                "id": cycle.artifact_id,
                "content": cycle.content,
                "metadata": cycle.metadata,
                "dependencies": cycle.dependencies,
                "timestamp": cycle.timestamp,
            }
            payload["artifacts"].append(artifact)
            if cycle.generated_at:
                current = payload.get("generated_at")
                if current is None or str(cycle.generated_at) > str(current):
                    payload["generated_at"] = cycle.generated_at

    for payload in universes.values():
        payload["artifacts"].sort(key=lambda item: item.get("id", ""))
        if payload.get("generated_at") is None:
            payload.pop("generated_at")
        yield payload


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_cycles(path: Path, *, root: Path, default_universe: str) -> Iterator[HarmonixCycleArtifact]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    for index, record in enumerate(_expand_records(data), start=1):
        cycle = _parse_cycle(record, path=path, root=root, default_universe=default_universe, index=index)
        if cycle is not None:
            yield cycle


def _expand_records(data: Any) -> Iterator[Dict[str, Any]]:
    if isinstance(data, dict):
        found_collection = False
        for key in ("cycles", "reports", "snapshots"):
            value = data.get(key)
            if isinstance(value, list):
                found_collection = True
                for entry in value:
                    if isinstance(entry, dict):
                        yield entry
        if not found_collection:
            yield data
    elif isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict):
                yield entry


def _parse_cycle(
    record: Dict[str, Any],
    *,
    path: Path,
    root: Path,
    default_universe: str,
    index: int,
) -> HarmonixCycleArtifact | None:
    containers: List[Dict[str, Any]] = [record]
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    if payload:
        containers.append(payload)
    state = record.get("state") if isinstance(record.get("state"), dict) else {}
    if state:
        containers.append(state)
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    if metadata:
        containers.append(metadata)
    payload_metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    if payload_metadata:
        containers.append(payload_metadata)

    universe = _first_value(containers, "universe") or default_universe
    universe = str(universe)

    cycle_value = _first_value(containers, "cycle")
    cycle_number = _coerce_int(cycle_value)

    artifact_id = _first_value(containers, "artifact_id") or _first_value(containers, "id")
    if not artifact_id:
        if cycle_number is not None:
            artifact_id = f"cycle-{cycle_number:04d}"
        elif cycle_value:
            artifact_id = str(cycle_value)
        else:
            artifact_id = f"{path.stem}-{index:04d}"
    artifact_id = str(artifact_id)

    timestamp = _coerce_str(
        _first_value(containers, "timestamp")
        or _first_value(containers, "generated_at")
        or record.get("time")
    )
    generated_at = _coerce_str(_first_value(containers, "generated_at")) or timestamp

    content = (
        _coerce_str(_first_value(containers, "summary"))
        or _coerce_str(_first_value(containers, "content"))
        or _coerce_str(_first_value(containers, "narrative"))
        or ""
    )

    harmonix_metadata: Dict[str, Any] = {}
    for source in (metadata, payload_metadata):
        harmonix_metadata.update(_clone_dict(source))
    if state:
        harmonix_metadata.setdefault("state", _clone_dict(state))
    if cycle_number is not None:
        harmonix_metadata.setdefault("cycle", cycle_number)
    harmonix_metadata.setdefault("snapshot_path", str(_relative_path(path, root)))

    dependency_sources: Sequence[Dict[str, Any]] = [container for container in containers if container]
    lineage_values = _extract_values(dependency_sources, "cycle_lineage") + _extract_values(
        dependency_sources, "lineage"
    )
    puzzle_values = _extract_values(dependency_sources, "puzzle_references")
    chronos_values = _extract_values(dependency_sources, "chronos_anchors")
    direct_dependencies = _extract_values(dependency_sources, "dependencies")

    lineage_dependencies = _normalise_dependency_values(lineage_values, default_universe=universe)
    puzzle_dependencies = _normalise_dependency_values(puzzle_values, default_universe="Puzzles")
    chronos_dependencies = _normalise_dependency_values(chronos_values, default_universe="Chronos")
    primary_dependencies = _normalise_dependency_values(direct_dependencies, default_universe=universe)

    dependencies = _dedupe(primary_dependencies + lineage_dependencies + puzzle_dependencies + chronos_dependencies)

    if lineage_dependencies:
        harmonix_metadata["normalized_cycle_lineage"] = lineage_dependencies
    if puzzle_dependencies:
        harmonix_metadata["normalized_puzzle_references"] = puzzle_dependencies
    if chronos_dependencies:
        harmonix_metadata["normalized_chronos_anchors"] = chronos_dependencies

    return HarmonixCycleArtifact(
        universe=universe,
        artifact_id=artifact_id,
        content=content,
        metadata=harmonix_metadata,
        dependencies=dependencies,
        timestamp=timestamp,
        generated_at=generated_at,
    )


def _relative_path(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def _clone_dict(value: Dict[str, Any] | None) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _extract_values(containers: Sequence[Dict[str, Any]], key: str) -> List[Any]:
    results: List[Any] = []
    for container in containers:
        if not isinstance(container, dict):
            continue
        value = container.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            results.extend(value)
        else:
            results.append(value)
    return results


def _normalise_dependency_values(values: Iterable[Any], *, default_universe: str) -> List[str]:
    normalised: List[str] = []
    for value in values:
        dependency = _normalise_dependency_value(value, default_universe=default_universe)
        if dependency:
            normalised.append(dependency)
    return normalised


def _normalise_dependency_value(value: Any, *, default_universe: str) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if "::" in stripped:
            return stripped
        if ":" in stripped:
            universe, artifact_id = stripped.split(":", 1)
            return f"{universe}::{artifact_id}"
        return f"{default_universe}::{stripped}"

    if isinstance(value, int):
        return f"{default_universe}::{value}"

    if isinstance(value, dict):
        node_id = value.get("node_id") or value.get("target") or value.get("id") or value.get("artifact_id")
        universe = value.get("universe") or value.get("source") or value.get("domain") or default_universe
        if node_id:
            node_id = str(node_id)
            if "::" in node_id:
                return node_id
            return f"{universe}::{node_id}"
        cycle = value.get("cycle")
        if cycle is not None:
            try:
                cycle_int = int(cycle)
            except (TypeError, ValueError):
                cycle_int = None
            artifact_id = value.get("artifact") or value.get("artifact_id")
            if not artifact_id and cycle_int is not None:
                artifact_id = f"cycle-{cycle_int:04d}"
            if artifact_id:
                return f"{universe}::{artifact_id}"
    return None


def _dedupe(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _first_value(containers: Sequence[Dict[str, Any]], key: str) -> Any:
    for container in containers:
        if not isinstance(container, dict):
            continue
        value = container.get(key)
        if value not in (None, ""):
            return value
    return None


def _coerce_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)

