from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
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
    """Very lightweight discovery. Adjust patterns as your repo evolves."""

    patterns = [
        ("engine", "echo", "*.py"),
        ("state", "states", "*.json"),
        ("akit", "akits", "*.y*ml"),
    ]
    for ctype, top, globpat in patterns:
        root = REPO_ROOT / top
        if not root.exists():
            continue
        for p in sorted(root.rglob(globpat)):
            if p.name.startswith("__"):
                continue
            rel = p.relative_to(REPO_ROOT).as_posix()
            version = "0.1.0"
            digest = _file_digest(p)
            deps: List[str] = []
            yield Component(
                name=p.stem,
                type=ctype,
                path=rel,
                version=version,
                digest=digest,
                dependencies=deps,
            )


def _file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical(obj) -> bytes:
    # deterministic, UTF-8, sorted keys, compact
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_manifest() -> Dict:
    comps = [asdict(c) for c in _iter_components()]
    # sort components deterministically
    comps.sort(key=lambda x: (x["type"], x["name"]))
    manifest = {
        "version": MANIFEST_VERSION,
        "components": comps,
        "meta": {"generator": "echo.manifest", "schema": "attestations/schema.json"},
    }
    # add fingerprint over canonicalized (without the fingerprint itself)
    payload = _canonical(
        {
            "version": manifest["version"],
            "components": comps,
            "meta": manifest["meta"],
        }
    )
    manifest["fingerprint"] = hashlib.sha256(payload).hexdigest()
    return manifest


def write_manifest(path: Path = MANIFEST_PATH) -> None:
    manifest = build_manifest()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_manifest(path: Path = MANIFEST_PATH) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_manifest(path: Path = MANIFEST_PATH) -> bool:
    current = load_manifest(path)
    rebuilt = build_manifest()
    # Compare canonical bytes (ignore whitespace)
    return _canonical(current) == _canonical(rebuilt)
