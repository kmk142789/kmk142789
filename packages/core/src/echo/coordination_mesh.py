"""Utilities for synthesising a coordination mesh across Echo modules.

The coordination mesh is designed to give higher level orchestrators a
single, structured view of how Echo artifacts relate to one another.  It pulls
metadata from :mod:`echo_manifest.json` and shapes it into clusters grouped by
code root, providing counts per category, owner contribution heatmaps, and
category adjacency links.  The resulting payload is used by the
``constellation_coordination_mesh`` capability to strengthen coordination,
autonomy, and cross-module situational awareness.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Tuple

__all__ = [
    "CoordinationMesh",
    "CoordinationCluster",
    "build_coordination_mesh",
    "locate_manifest",
]


MANIFEST_FILENAME = "echo_manifest.json"


@dataclass(slots=True)
class CoordinationCluster:
    """Describe a group of manifest entries rooted in the same code module."""

    module: str
    categories: Dict[str, int]
    owners: Dict[str, int]
    entries: List[Dict[str, object]]


@dataclass(slots=True)
class CoordinationMesh:
    """Composite view of coordination signals derived from the manifest."""

    summary: Dict[str, object]
    clusters: List[CoordinationCluster]
    links: List[Dict[str, object]]
    generated_at: str

    def as_dict(self) -> Dict[str, object]:
        """Return the mesh as a JSON serialisable dictionary."""

        return {
            "summary": self.summary,
            "clusters": [
                {
                    "module": cluster.module,
                    "categories": cluster.categories,
                    "owners": cluster.owners,
                    "entries": cluster.entries,
                }
                for cluster in self.clusters
            ],
            "links": self.links,
            "generated_at": self.generated_at,
        }


class ManifestNotFoundError(FileNotFoundError):
    """Raised when ``echo_manifest.json`` cannot be located."""


def locate_manifest(start: Path | None = None) -> Path:
    """Search upwards from ``start`` for ``echo_manifest.json`` and return it."""

    if start is None:
        start = Path(__file__).resolve()
    elif not start.is_absolute():
        start = (Path(__file__).resolve().parent / start).resolve()

    for parent in (start,) + tuple(start.parents):
        candidate = parent / MANIFEST_FILENAME
        if candidate.exists():
            return candidate
    raise ManifestNotFoundError(MANIFEST_FILENAME)


def _normalise_entry(entry: MutableMapping[str, object], manifest_dir: Path) -> Dict[str, object]:
    path_value = entry.get("path")
    path = Path(str(path_value)) if path_value else None
    module_name = path.parts[0] if path and path.parts else "unbound"

    resolved: Path | None = None
    exists = False
    if path:
        resolved = (manifest_dir / path).resolve()
        exists = resolved.exists()

    owners = entry.get("owners") or []
    if not isinstance(owners, list):
        owners = [str(owners)]

    return {
        "name": entry.get("name"),
        "category": entry.get("category"),
        "path": str(path) if path else None,
        "module": module_name,
        "owners": owners,
        "exists": exists,
        "resolved_path": str(resolved) if resolved else None,
        "tags": entry.get("tags") or [],
    }


def _accumulate_clusters(entries: Iterable[Dict[str, object]]) -> Tuple[
    Dict[str, CoordinationCluster],
    Dict[Tuple[str, str], int],
]:
    clusters: Dict[str, CoordinationCluster] = {}
    adjacency: Dict[Tuple[str, str], int] = defaultdict(int)

    for entry in entries:
        module = str(entry["module"])
        category = str(entry.get("category"))
        owners: List[str] = list(entry.get("owners") or [])

        if module not in clusters:
            clusters[module] = CoordinationCluster(
                module=module,
                categories=defaultdict(int),
                owners=defaultdict(int),
                entries=[],
            )
        cluster = clusters[module]
        cluster.categories[category] += 1
        for owner in owners:
            cluster.owners[owner] += 1
        cluster.entries.append(entry)

        categories = sorted(cluster.categories.keys())
        for index, left in enumerate(categories):
            for right in categories[index + 1 :]:
                adjacency[(left, right)] += 1

    for cluster in clusters.values():
        cluster.categories = dict(sorted(cluster.categories.items()))
        cluster.owners = dict(sorted(cluster.owners.items()))
        cluster.entries.sort(key=lambda item: (str(item.get("category")), str(item.get("name"))))

    return clusters, adjacency


def build_coordination_mesh(manifest_path: Path | str | None = None) -> CoordinationMesh:
    """Return a :class:`CoordinationMesh` aggregated from the manifest."""

    if manifest_path is None:
        manifest_path = locate_manifest()
    manifest = Path(manifest_path)
    if not manifest.exists():
        raise ManifestNotFoundError(str(manifest))

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_dir = manifest.parent

    normalised_entries: List[Dict[str, object]] = []
    category_counts: Dict[str, int] = defaultdict(int)
    owners: set[str] = set()

    for category, items in payload.items():
        if not isinstance(items, list):
            continue
        for raw in items:
            if not isinstance(raw, MutableMapping):
                continue
            entry = _normalise_entry(dict(raw), manifest_dir)
            entry["category"] = category
            normalised_entries.append(entry)
            category_counts[category] += 1
            owners.update(entry.get("owners") or [])

    clusters, adjacency = _accumulate_clusters(normalised_entries)

    total_entries = sum(category_counts.values())
    mesh = CoordinationMesh(
        summary={
            "total_entries": total_entries,
            "categories": dict(sorted(category_counts.items())),
            "modules": len(clusters),
            "owners": sorted(owners),
            "autonomy_index": round(len(owners) / total_entries, 4) if total_entries else 0.0,
        },
        clusters=[clusters[name] for name in sorted(clusters.keys())],
        links=[
            {"source": left, "target": right, "weight": weight}
            for (left, right), weight in sorted(adjacency.items())
        ],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    return mesh

