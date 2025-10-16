"""Generate and validate the auto-maintained Echo manifest."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Mapping, MutableMapping, Sequence

import jsonschema


MANIFEST_VERSION = "1.0.0"
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_OUTPUT = _REPO_ROOT / "echo_manifest.json"
_SCHEMA_PATH = _REPO_ROOT / "schema" / "echo_manifest.schema.json"


class ManifestError(RuntimeError):
    """Base error raised for manifest generation and validation issues."""


class ManifestValidationError(ManifestError):
    """Raised when the manifest fails schema or freshness validation."""


@dataclass(frozen=True)
class EngineRecord:
    name: str
    path: str
    kind: str
    status: str
    entrypoints: tuple[str, ...]
    tests: tuple[str, ...]

    def to_dict(self) -> MutableMapping[str, object]:
        return {
            "name": self.name,
            "path": self.path,
            "kind": self.kind,
            "status": self.status,
            "entrypoints": list(self.entrypoints),
            "tests": list(self.tests),
        }


@dataclass(frozen=True)
class KitRecord:
    name: str
    path: str
    api: str
    capabilities: tuple[str, ...]

    def to_dict(self) -> MutableMapping[str, object]:
        return {
            "name": self.name,
            "path": self.path,
            "api": self.api,
            "capabilities": list(self.capabilities),
        }


@dataclass(frozen=True)
class ArtifactRecord:
    type: str
    path: str
    content_hash: str

    def to_dict(self) -> MutableMapping[str, object]:
        return {
            "type": self.type,
            "path": self.path,
            "content_hash": self.content_hash,
        }


def _git(args: Sequence[str], repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def _generated_at(repo_root: Path) -> str:
    commit_time = _git(["log", "-1", "--format=%cI"], repo_root)
    if commit_time:
        return commit_time
    return "1970-01-01T00:00:00Z"


def _git_meta(repo_root: Path) -> Mapping[str, str]:
    return {
        "commit_sha": _git(["rev-parse", "HEAD"], repo_root) or "UNKNOWN",
        "branch": _git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root) or "UNKNOWN",
        "author": _git(["log", "-1", "--format=%an"], repo_root) or "UNKNOWN",
    }


def _sha256_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _short_digest(path: Path) -> str:
    return _sha256_digest(path)[:12]


def _engine_candidates(repo_root: Path) -> Iterator[Path]:
    for base in (repo_root / "echo", repo_root / "modules"):
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if path.name in {"__init__.py", "main.py"} or path.name.endswith("_engine.py"):
                yield path


def _module_name(path: Path, repo_root: Path) -> str:
    relative = path.relative_to(repo_root)
    if path.name == "__init__.py":
        relative = relative.parent
    else:
        relative = relative.with_suffix("")
    parts = [part for part in relative.parts if part != "__pycache__"]
    return ".".join(parts)


def _engine_kind(path: Path) -> str:
    if path.name == "__init__.py":
        return "package"
    if path.name == "main.py":
        return "app"
    if path.name.endswith("_engine.py"):
        return "engine"
    return "module"


def _engine_entrypoints(module_name: str, path: Path) -> tuple[str, ...]:
    if not module_name:
        return tuple()
    if path.name == "main.py":
        return (f"python -m {module_name}",)
    if path.name == "__init__.py":
        return (module_name,) if module_name else tuple()
    return (module_name,)


def _matching_tests(repo_root: Path, module_name: str) -> tuple[str, ...]:
    tests_root = repo_root / "tests"
    if not tests_root.exists():
        return tuple()
    base_token = module_name.split(".")[-1]
    matches: List[str] = []
    for path in sorted(tests_root.rglob("test_*.py")):
        try:
            contents = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if module_name in contents or base_token in path.stem or base_token in contents:
            matches.append(path.relative_to(repo_root).as_posix())
    return tuple(matches)


def _discover_engines(repo_root: Path) -> list[EngineRecord]:
    engines: list[EngineRecord] = []
    for candidate in _engine_candidates(repo_root):
        module_name = _module_name(candidate, repo_root)
        if not module_name:
            continue
        record = EngineRecord(
            name=module_name,
            path=candidate.relative_to(repo_root).as_posix(),
            kind=_engine_kind(candidate),
            status="active",
            entrypoints=_engine_entrypoints(module_name, candidate),
            tests=_matching_tests(repo_root, module_name),
        )
        engines.append(record)
    engines.sort(key=lambda item: (item.name, item.path))
    return engines


def _collect_symbols(path: Path) -> set[str]:
    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    names: set[str] = set()
    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def _discover_kits(repo_root: Path) -> list[KitRecord]:
    kits_dir = repo_root / "echo" / "akit"
    if not kits_dir.exists():
        return []
    kits: list[KitRecord] = []
    candidates: list[Path] = []
    if (kits_dir / "__init__.py").exists():
        candidates.append(kits_dir)
    candidates.extend(sorted(p for p in kits_dir.iterdir() if p.is_dir()))
    for package_dir in candidates:
        if package_dir.is_dir() and not (package_dir / "__init__.py").exists():
            continue
        module_name = ".".join(package_dir.relative_to(repo_root).parts)
        symbols: set[str] = set()
        for py_file in sorted(package_dir.glob("*.py")):
            symbols.update(_collect_symbols(py_file))
        record = KitRecord(
            name=package_dir.name,
            path=package_dir.relative_to(repo_root).as_posix(),
            api=module_name,
            capabilities=tuple(sorted(symbols)),
        )
        kits.append(record)
    kits.sort(key=lambda item: item.name)
    return kits


def _discover_artifacts(repo_root: Path) -> list[ArtifactRecord]:
    bases = [repo_root / "manifest", repo_root / "proofs"]
    artifacts: list[ArtifactRecord] = []
    for base in bases:
        if not base.exists():
            continue
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            artifacts.append(
                ArtifactRecord(
                    type=path.suffix.lstrip(".") or "file",
                    path=path.relative_to(repo_root).as_posix(),
                    content_hash=_short_digest(path),
                )
            )
    artifacts.sort(key=lambda item: item.path)
    return artifacts


def _load_pulse_history(repo_root: Path) -> list[dict]:
    history_path = repo_root / "pulse_history.json"
    if not history_path.exists():
        return []
    try:
        payload = json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    snapshots: list[dict] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        timestamp = entry.get("timestamp")
        try:
            iso_timestamp = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
        except (TypeError, ValueError):
            continue
        message = str(entry.get("message", ""))
        hash_value = str(entry.get("hash", ""))
        snapshots.append(
            {
                "timestamp": iso_timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "message": message,
                "hash": hash_value,
            }
        )
    snapshots.sort(key=lambda item: item["timestamp"])
    return snapshots


def _states_block(repo_root: Path, engines: Sequence[EngineRecord], kits: Sequence[KitRecord]) -> dict:
    snapshots = _load_pulse_history(repo_root)
    cycle = len(snapshots) if snapshots else len(engines)
    unique_tests = sorted({test for engine in engines for test in engine.tests})
    resonance = round(len(engines) / max(1, len(kits) or 1), 3)
    amplification = round(len(unique_tests) / max(1, len(engines)), 3)
    return {
        "cycle": cycle,
        "resonance": resonance,
        "amplification": amplification,
        "snapshots": snapshots,
    }


def _discover_ci_workflows(repo_root: Path) -> list[str]:
    workflows_dir = repo_root / ".github" / "workflows"
    if not workflows_dir.exists():
        return []
    names = [path.stem for path in sorted(workflows_dir.glob("*.yml"))]
    names.extend(path.stem for path in sorted(workflows_dir.glob("*.yaml")))
    return sorted(dict.fromkeys(names))


def _load_schema() -> Mapping[str, object]:
    if not _SCHEMA_PATH.exists():
        raise ManifestError(f"Schema not found at {_SCHEMA_PATH}")
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def generate_manifest(repo_root: Path | None = None) -> dict:
    root = repo_root or _REPO_ROOT
    engines = _discover_engines(root)
    kits = _discover_kits(root)
    artifacts = _discover_artifacts(root)
    manifest = {
        "version": MANIFEST_VERSION,
        "generated_at": _generated_at(root),
        "engines": [engine.to_dict() for engine in engines],
        "states": _states_block(root, engines, kits),
        "kits": [kit.to_dict() for kit in kits],
        "artifacts": [artifact.to_dict() for artifact in artifacts],
        "ci": {"integration": _discover_ci_workflows(root)},
        "meta": dict(_git_meta(root)),
    }
    return manifest


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def write_manifest(manifest: Mapping[str, object], output_path: Path | None = None) -> Path:
    path = output_path or _DEFAULT_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    text = _canonical_json(manifest)
    path.write_text(text, encoding="utf-8")
    return path


def generate_command(repo_root: Path | None, output_path: Path | None) -> Path:
    manifest = generate_manifest(repo_root)
    path = write_manifest(manifest, output_path)
    return path


def validate_manifest(manifest_path: Path | None = None, repo_root: Path | None = None, *, expected: Mapping[str, object] | None = None) -> None:
    root = repo_root or _REPO_ROOT
    path = manifest_path or _DEFAULT_OUTPUT
    if not path.exists():
        raise ManifestValidationError(f"Manifest file not found at {path}")
    try:
        manifest_on_disk = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestValidationError(f"Manifest file is not valid JSON: {exc}") from exc
    schema = _load_schema()
    try:
        jsonschema.validate(manifest_on_disk, schema)
    except jsonschema.ValidationError as exc:  # pragma: no cover - exercised in tests
        raise ManifestValidationError(f"Manifest failed schema validation: {exc.message}") from exc
    expected_manifest = dict(expected) if expected is not None else generate_manifest(root)
    if _canonical_json(manifest_on_disk) != _canonical_json(expected_manifest):
        raise ManifestValidationError("Manifest is stale. Run `echo manifest update`.")


def update_manifest(manifest_path: Path | None = None, repo_root: Path | None = None) -> Path:
    root = repo_root or _REPO_ROOT
    path = manifest_path or _DEFAULT_OUTPUT
    manifest = generate_manifest(root)
    text = _canonical_json(manifest)
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if current == text:
            validate_manifest(path, root, expected=manifest)
            return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    validate_manifest(path, root, expected=manifest)
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and validate the Echo manifest")
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT, help="Repository root")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate manifest and write to disk")
    gen.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT, help="Manifest output path")

    val = sub.add_parser("validate", help="Validate manifest against schema and expected payload")
    val.add_argument("--manifest", type=Path, default=_DEFAULT_OUTPUT, help="Manifest path to validate")

    upd = sub.add_parser("update", help="Regenerate manifest if stale and validate")
    upd.add_argument("--manifest", type=Path, default=_DEFAULT_OUTPUT, help="Manifest path to update")

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "generate":
            path = generate_command(args.repo_root, args.output)
            print(f"Manifest generated at {path}")
        elif args.command == "validate":
            validate_manifest(args.manifest, args.repo_root)
            print("Manifest is valid and up to date")
        elif args.command == "update":
            path = update_manifest(args.manifest, args.repo_root)
            print(f"Manifest updated at {path}")
        else:  # pragma: no cover - defensive
            parser.print_help()
            return 1
    except ManifestValidationError as exc:
        print(str(exc))
        return 1
    except ManifestError as exc:
        print(str(exc))
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
