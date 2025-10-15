"""Echo manifest generator, validator, and updater CLI."""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List, Sequence

import jsonschema


MANIFEST_VERSION = "1.0.0"
DEFAULT_MANIFEST_PATH = "echo_manifest.json"
SCHEMA_PATH = "schema/echo_manifest.schema.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_prefix(path: Path, length: int = 12) -> str:
    digest = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()[:length]


def _git_output(root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _extract_entrypoints(path: Path) -> List[str]:
    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return []
    entrypoints: List[str] = []
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith(("main", "cli")):
            entrypoints.append(node.name)
    return sorted(entrypoints)


def _engine_name(path: Path) -> str:
    if path.name == "__init__.py":
        return path.parent.name
    if path.name == "main.py":
        return path.parent.name or path.stem
    if path.name.endswith("_engine.py"):
        return path.stem.removesuffix("_engine")
    return path.stem


def _engine_kind(path: Path) -> str:
    if path.name == "__init__.py":
        return "package"
    if path.name == "main.py":
        return "entrypoint"
    if path.name.endswith("_engine.py"):
        return "engine"
    return "module"


@dataclass
class EchoManifestGenerator:
    """Encapsulates manifest discovery logic."""

    root: Path

    def __post_init__(self) -> None:
        self.root = self.root.resolve()

    @property
    def tests_root(self) -> Path:
        return self.root / "tests"

    def _collect_tests(self) -> List[Path]:
        if not self.tests_root.exists():
            return []
        return sorted(self.tests_root.glob("test_*.py"))

    def _matching_tests(self, base_name: str, tests: Sequence[Path]) -> List[str]:
        matches = [
            str(test.relative_to(self.root))
            for test in tests
            if base_name in test.stem
        ]
        return sorted(matches)

    def _discover_engine_files(self) -> List[Path]:
        engine_files: List[Path] = []
        for directory in ("echo", "modules"):
            base = self.root / directory
            if not base.exists():
                continue
            for path in base.rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                if path.name in {"__init__.py", "main.py"} or path.name.endswith("_engine.py"):
                    engine_files.append(path)
        return sorted(engine_files, key=lambda p: (str(p.parent.relative_to(self.root)), p.name))

    def _discover_engines(self) -> List[dict]:
        tests = self._collect_tests()
        engines: List[dict] = []
        for path in self._discover_engine_files():
            base_name = _engine_name(path)
            engines.append(
                {
                    "name": base_name,
                    "path": str(path.relative_to(self.root)),
                    "kind": _engine_kind(path),
                    "status": "active",
                    "entrypoints": _extract_entrypoints(path),
                    "tests": self._matching_tests(base_name, tests),
                }
            )
        return engines

    def _discover_kits(self) -> List[dict]:
        kits: List[dict] = []
        modules_dir = self.root / "modules"
        if not modules_dir.exists():
            return kits
        candidates: List[Path] = []
        for path in modules_dir.rglob("__init__.py"):
            if "__pycache__" in path.parts:
                continue
            candidates.append(path.parent)
        for path in modules_dir.glob("*.py"):
            candidates.append(path)
        seen: set[str] = set()
        for candidate in sorted({c for c in candidates}, key=lambda p: str(p.relative_to(self.root))):
            rel = candidate.relative_to(self.root)
            if rel in seen:
                continue
            seen.add(rel)
            if candidate.is_dir():
                capability_files = sorted(candidate.glob("*.py"))
                capabilities = [f.stem for f in capability_files if f.name != "__init__.py"]
                kits.append(
                    {
                        "name": candidate.name,
                        "path": str(rel),
                        "api": candidate.name,
                        "capabilities": capabilities,
                    }
                )
            else:
                kits.append(
                    {
                        "name": candidate.stem,
                        "path": str(rel),
                        "api": candidate.stem,
                        "capabilities": [],
                    }
                )
        return kits

    def _discover_artifacts(self) -> List[dict]:
        artifacts: List[dict] = []
        search_roots: Iterable[Path] = [self.root]
        manifest_dir = self.root / "manifest"
        if manifest_dir.exists():
            search_roots = [self.root, manifest_dir]
        seen: set[Path] = set()
        for base in search_roots:
            for path in sorted(base.glob("*.json")):
                if not path.is_file():
                    continue
                if path.name == DEFAULT_MANIFEST_PATH:
                    continue
                rel = path.relative_to(self.root)
                if rel in seen:
                    continue
                seen.add(rel)
                artifacts.append(
                    {
                        "type": path.suffix.lstrip("."),
                        "path": str(rel),
                        "content_hash": _sha256_prefix(path),
                    }
                )
        return sorted(artifacts, key=lambda item: item["path"])

    def _ci_integrations(self) -> List[str]:
        workflows_dir = self.root / ".github" / "workflows"
        if not workflows_dir.exists():
            return []
        names = [
            path.stem
            for path in workflows_dir.glob("*.yml")
            if path.is_file()
        ]
        names.extend(
            path.stem
            for path in workflows_dir.glob("*.yaml")
            if path.is_file()
        )
        return sorted(set(names))

    def _meta(self) -> dict:
        return {
            "commit_sha": _git_output(self.root, "rev-parse", "HEAD"),
            "branch": _git_output(self.root, "rev-parse", "--abbrev-ref", "HEAD"),
            "author": _git_output(self.root, "log", "-1", "--pretty=%an"),
        }

    def snapshot(self) -> dict:
        engines = self._discover_engines()
        kits = self._discover_kits()
        artifacts = self._discover_artifacts()
        states = self._build_states(engines, kits)
        return {
            "version": MANIFEST_VERSION,
            "engines": engines,
            "states": states,
            "kits": kits,
            "artifacts": artifacts,
            "ci": {"integration": self._ci_integrations()},
            "meta": self._meta(),
        }

    def _build_states(self, engines: Sequence[dict], kits: Sequence[dict]) -> dict:
        resonance = sum(len(engine["tests"]) for engine in engines)
        snapshots = [
            {
                "engine": engine["name"],
                "tests": len(engine["tests"]),
                "entrypoints": len(engine["entrypoints"]),
            }
            for engine in engines
        ]
        return {
            "cycle": len(engines),
            "resonance": resonance,
            "amplification": len(kits),
            "snapshots": snapshots,
        }

    def build(self, *, generated_at: str | None = None, previous: dict | None = None) -> dict:
        manifest = self.snapshot()
        if previous is not None:
            manifest_without_generated_at = json.loads(json.dumps(manifest, sort_keys=True))
            manifest_without_generated_at.pop("meta", None)
            previous_clone = previous.copy()
            previous_clone.pop("generated_at", None)
            previous_clone.pop("meta", None)
            if manifest_without_generated_at == previous_clone:
                manifest["generated_at"] = previous.get("generated_at", generated_at or _utc_now())
                manifest["meta"] = previous.get("meta", manifest["meta"])
                return manifest
        manifest["generated_at"] = generated_at or _utc_now()
        return manifest


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"Manifest not found at {path}") from None


def _dump_json(data: dict, path: Path) -> None:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    path.write_text(payload + "\n", encoding="utf-8")


def _sync_docs_manifest(root: Path, manifest: dict) -> None:
    docs_manifest = root / "docs" / DEFAULT_MANIFEST_PATH
    if not docs_manifest.parent.exists():
        return
    try:
        existing = json.loads(docs_manifest.read_text(encoding="utf-8"))
    except FileNotFoundError:
        existing = None
    if existing is None or json.dumps(existing, sort_keys=True) != json.dumps(manifest, sort_keys=True):
        _dump_json(manifest, docs_manifest)


def _load_schema(schema_path: Path) -> dict:
    try:
        return json.loads(schema_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"Schema not found at {schema_path}") from None


def _validate_schema(manifest: dict, schema: dict) -> None:
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda e: e.path)
    if errors:
        message = "\n".join(error.message for error in errors)
        raise ValueError(f"Manifest validation failed:\n{message}")


def generate_manifest(root: Path, manifest_path: Path, *, reuse_timestamp: bool = False) -> dict:
    generator = EchoManifestGenerator(root)
    previous = None
    if reuse_timestamp and manifest_path.exists():
        previous = _load_json(manifest_path)
    manifest = generator.build(previous=previous if reuse_timestamp else None)
    _dump_json(manifest, manifest_path)
    default_manifest_path = (root / DEFAULT_MANIFEST_PATH).resolve()
    if manifest_path == default_manifest_path:
        _sync_docs_manifest(root, manifest)
    return manifest


def validate_manifest(root: Path, manifest_path: Path, schema_path: Path) -> None:
    manifest = _load_json(manifest_path)
    schema = _load_schema(schema_path)
    _validate_schema(manifest, schema)
    generator = EchoManifestGenerator(root)
    expected = generator.build(previous=manifest)
    comparable_new = json.loads(json.dumps(expected, sort_keys=True))
    comparable_old = manifest.copy()
    comparable_old.pop("generated_at", None)
    comparable_old.pop("meta", None)
    comparable_new.pop("generated_at", None)
    comparable_new.pop("meta", None)
    if comparable_new != comparable_old:
        raise ValueError("Manifest is stale. Run `echo manifest update` and commit.")


def update_manifest(root: Path, manifest_path: Path, schema_path: Path) -> dict:
    previous = manifest_path.exists() and _load_json(manifest_path) or None
    generator = EchoManifestGenerator(root)
    manifest = generator.build(previous=previous)
    if previous is None or json.dumps(manifest, sort_keys=True) != json.dumps(previous, sort_keys=True):
        _dump_json(manifest, manifest_path)
    _sync_docs_manifest(root, manifest)
    validate_manifest(root, manifest_path, schema_path)
    return manifest


def _default_root(path: str | None) -> Path:
    return Path(path or os.getcwd()).resolve()


def _default_manifest(root: Path, manifest: str | None) -> Path:
    return (root / (manifest or DEFAULT_MANIFEST_PATH)).resolve()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the Echo manifest")
    parser.add_argument("command", choices=["generate", "validate", "update"], help="Manifest command")
    parser.add_argument("--root", dest="root", help="Repository root", default=None)
    parser.add_argument("--manifest", dest="manifest", help="Manifest path", default=None)
    parser.add_argument("--schema", dest="schema", help="Schema path", default=None)
    parser.add_argument(
        "--reuse-timestamp",
        action="store_true",
        default=False,
        help="Reuse the existing generated_at field when nothing has changed",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)
    root = _default_root(args.root)
    manifest_path = _default_manifest(root, args.manifest)
    schema_path = (root / (args.schema or SCHEMA_PATH)).resolve()

    try:
        if args.command == "generate":
            generate_manifest(root, manifest_path, reuse_timestamp=args.reuse_timestamp)
        elif args.command == "validate":
            validate_manifest(root, manifest_path, schema_path)
        elif args.command == "update":
            update_manifest(root, manifest_path, schema_path)
    except Exception as exc:  # pragma: no cover - CLI error presentation
        parser.exit(1, f"{exc}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
