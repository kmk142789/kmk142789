from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "echo_manifest.json"
MANIFEST_VERSION = "1.0"


@dataclass(frozen=True)
class Component:
    name: str
    type: str  # "engine" | "state" | "akit"
    path: str  # repo-relative posix path
    version: str
    digest: str
    dependencies: List[str]


def _iter_components() -> Iterable[Component]:
    """Lightweight discovery across key echo components."""

    patterns = [
        ("engine", "echo", "*.py"),
        ("state", "states", "*.json"),
        ("akit", "akits", "*.y*ml"),
    ]
    for ctype, top, globpat in patterns:
        root = REPO_ROOT / top
        if not root.exists():
            continue
        for path in sorted(root.rglob(globpat)):
            if path.name.startswith("__"):
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            version = "0.1.0"
            digest = _file_digest(path)
            deps: List[str] = []
            yield Component(
                name=path.stem,
                type=ctype,
                path=rel,
                version=version,
                digest=digest,
                dependencies=deps,
            )


def _file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _canonical(obj: object) -> bytes:
    """Return canonical JSON bytes for deterministic hashing."""

    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_manifest() -> Dict[str, object]:
    components = [asdict(component) for component in _iter_components()]
    components.sort(key=lambda item: (item["type"], item["name"]))
    manifest = {
        "version": MANIFEST_VERSION,
        "components": components,
        "meta": {
            "generator": "echo.manifest",
            "schema": "attestations/schema.json",
        },
    }
    payload = _canonical(
        {
            "version": manifest["version"],
            "components": components,
            "meta": manifest["meta"],
        }
    )
    manifest["fingerprint"] = hashlib.sha256(payload).hexdigest()
    return manifest


def write_manifest(path: Path = MANIFEST_PATH) -> None:
    manifest = build_manifest()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_manifest(path: Path = MANIFEST_PATH) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_manifest(path: Path = MANIFEST_PATH) -> bool:
    current = load_manifest(path)
    rebuilt = build_manifest()
    return _canonical(current) == _canonical(rebuilt)
