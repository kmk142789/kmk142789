"""Deterministic manifest builder for Echo components."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence

from .provenance import canonical_json

ROOT_DIR = Path(__file__).resolve().parent.parent
_COMPONENT_DIRS = {
    "engines": "engine",
    "states": "state",
    "akits": "akit",
}


class ManifestError(RuntimeError):
    """Raised when manifest generation encounters inconsistent metadata."""


@dataclass(frozen=True, slots=True)
class Component:
    """Normalized component metadata used to render the manifest."""

    name: str
    type: str
    path: Path
    version: str
    dependencies: Sequence[str]

    def to_dict(self) -> Mapping[str, object]:
        data: MutableMapping[str, object] = OrderedDict()
        data["name"] = self.name
        data["type"] = self.type
        data["path"] = self.path.as_posix()
        data["version"] = self.version
        data["digest"] = digest_for_path(self.path)
        data["dependencies"] = sorted(self.dependencies)
        return data


def _iter_descriptor_files(base: Path) -> Iterable[Path]:
    if not base.exists():
        return []
    descriptors: List[Path] = []
    for path in base.iterdir():
        if path.is_dir():
            candidate = path / "component.json"
            if candidate.exists():
                descriptors.append(candidate)
        elif path.suffix == ".json":
            descriptors.append(path)
    return sorted(descriptors)


def _load_descriptor(path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, Mapping):  # pragma: no cover - guard
        raise ManifestError(f"Descriptor at {path} did not contain an object")
    return data


def _normalize_component(
    descriptor: Mapping[str, object],
    *,
    component_type: str,
    root: Path,
    descriptor_path: Path,
) -> Component:
    try:
        name = str(descriptor["name"])
        version = str(descriptor["version"])
        source_path = Path(str(descriptor["path"]))
        dependencies_raw = descriptor.get("dependencies", [])
    except KeyError as exc:  # pragma: no cover - validation guard
        raise ManifestError(f"Missing required field in {descriptor_path}: {exc}") from exc

    if not isinstance(dependencies_raw, Iterable):  # pragma: no cover - guard
        raise ManifestError(f"Dependencies for {name} must be iterable")

    dependencies = [str(dep) for dep in dependencies_raw]
    resolved_path = (root / source_path).resolve()
    if not resolved_path.exists():
        raise ManifestError(f"Component {name} references missing path {source_path}")
    if not resolved_path.is_relative_to(root):  # type: ignore[attr-defined]
        raise ManifestError(f"Component {name} path escapes repository root: {source_path}")
    return Component(
        name=name,
        type=component_type,
        path=resolved_path.relative_to(root),
        version=version,
        dependencies=tuple(dependencies),
    )


def digest_for_path(path: Path) -> str:
    target = (ROOT_DIR / path).resolve() if not path.is_absolute() else path
    if target.is_dir():
        hasher = sha256()
        for entry in sorted(target.rglob("*")):
            if entry.is_file():
                relative = entry.relative_to(target)
                hasher.update(relative.as_posix().encode("utf-8"))
                with entry.open("rb") as handle:
                    hasher.update(handle.read())
        return hasher.hexdigest()
    if target.is_file():
        with target.open("rb") as handle:
            return sha256(handle.read()).hexdigest()
    raise ManifestError(f"Cannot compute digest for missing path {path}")


def build_manifest(*, root: Path | None = None) -> Mapping[str, object]:
    repo_root = root or ROOT_DIR
    components: List[Mapping[str, object]] = []
    for directory, component_type in sorted(_COMPONENT_DIRS.items()):
        base = repo_root / directory
        for descriptor_path in _iter_descriptor_files(base):
            descriptor = _load_descriptor(descriptor_path)
            component = _normalize_component(
                descriptor,
                component_type=component_type,
                root=repo_root,
                descriptor_path=descriptor_path,
            )
            components.append(component.to_dict())
    components.sort(key=lambda item: (item["type"], item["name"]))
    manifest: MutableMapping[str, object] = OrderedDict()
    manifest["version"] = "1.0"
    manifest["components"] = components
    manifest["fingerprint"] = fingerprint(manifest)
    return manifest


def fingerprint(manifest: Mapping[str, object]) -> str:
    payload = dict(manifest)
    payload.pop("fingerprint", None)
    canonical = canonical_json(payload)
    return sha256(canonical).hexdigest()


def verify_manifest(path: str | os.PathLike[str] = "echo_manifest.json") -> int:
    repo_root = ROOT_DIR
    manifest_path = (repo_root / Path(path)).resolve()
    rebuilt = build_manifest(root=repo_root)
    canonical_expected = canonical_json(rebuilt)
    if not manifest_path.exists():
        raise ManifestError(f"Manifest {manifest_path} is missing; run refresh")
    with manifest_path.open("rb") as handle:
        on_disk = handle.read()
    try:
        on_disk_data = json.loads(on_disk)
    except json.JSONDecodeError as exc:  # pragma: no cover - guard
        raise ManifestError(f"Manifest {manifest_path} is not valid JSON") from exc
    canonical_actual = canonical_json(on_disk_data)
    if canonical_actual == canonical_expected:
        return 0
    return 1
