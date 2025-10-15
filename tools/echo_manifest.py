"""Utilities for generating and validating the Echo manifest."""

from __future__ import annotations

import argparse
import ast
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

try:
    import jsonschema
except ModuleNotFoundError as exc:  # pragma: no cover - exercised in runtime environments
    raise SystemExit(
        "jsonschema is required to work with the Echo manifest. "
        "Install dev dependencies with `pip install -e .[dev]`."
    ) from exc


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "echo_manifest.json"
SCHEMA_PATH = REPO_ROOT / "schema" / "echo_manifest.schema.json"
SCHEMA_VERSION = "1.0.0"
_HASH_PREFIX = 12


@dataclass(frozen=True)
class ManifestData:
    payload: Dict[str, object]

    def to_json(self) -> str:
        return json.dumps(self.payload, sort_keys=True, separators=(",", ":"))


def _sha256_prefix(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:_HASH_PREFIX]


def _file_hash(path: Path) -> str:
    return _sha256_prefix(path.read_bytes())


def _iter_python_files(base: Path) -> Iterable[Path]:
    if not base.exists():
        return []
    return (path for path in base.rglob("*.py") if "__pycache__" not in path.parts)


def _is_engine_candidate(path: Path) -> bool:
    name = path.name
    if name == "__init__.py":
        return True
    if name == "main.py":
        return True
    if name.endswith("_engine.py"):
        return True
    return False


def _module_name(path: Path, repo_root: Path) -> str:
    relative = path.relative_to(repo_root)
    return relative.with_suffix("").as_posix().replace("/", ".")


def _engine_kind(path: Path) -> str:
    name = path.name
    if name == "__init__.py":
        return "package"
    if name == "main.py":
        return "entrypoint"
    if name.endswith("_engine.py"):
        return "engine"
    return "module"


def _read_source(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _discover_entrypoints(path: Path) -> List[str]:
    source = _read_source(path)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    entrypoint_names = {"main", "cli", "run", "execute", "start"}
    discovered: List[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("_"):
                continue
            if node.name in entrypoint_names or "cli" in node.name.lower():
                discovered.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name in entrypoint_names:
                    discovered.append(f"{node.name}.{child.name}")
    return sorted(dict.fromkeys(discovered))


def _match_tests(repo_root: Path, candidate: Path) -> List[str]:
    tests_dir = repo_root / "tests"
    if not tests_dir.exists():
        return []

    target_tokens = {candidate.stem.lower()}
    if candidate.name == "__init__.py":
        target_tokens.add(candidate.parent.name.lower())

    matches: List[str] = []
    for test_file in tests_dir.rglob("test_*.py"):
        stem = test_file.stem.lower()
        if any(token in stem for token in target_tokens):
            matches.append(test_file.relative_to(repo_root).as_posix())
    return sorted(dict.fromkeys(matches))


def _extract_dunder_all(path: Path) -> List[str]:
    if not path.exists():
        return []
    try:
        tree = ast.parse(_read_source(path))
    except SyntaxError:
        return []
    names: List[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
                value = node.value
                if isinstance(value, (ast.List, ast.Tuple)):
                    for element in value.elts:
                        if isinstance(element, ast.Constant) and isinstance(element.value, str):
                            names.append(element.value)
    return sorted(dict.fromkeys(names))


def _discover_capabilities(path: Path) -> List[str]:
    if not path.exists():
        return []
    try:
        tree = ast.parse(_read_source(path))
    except SyntaxError:
        return []
    capabilities: List[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            capabilities.append(node.name)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            capabilities.append(node.name)
    return sorted(dict.fromkeys(capabilities))


def discover_engines(repo_root: Path) -> List[Dict[str, object]]:
    engines: List[Dict[str, object]] = []
    for base in (repo_root / "echo", repo_root / "modules"):
        for path in sorted(_iter_python_files(base), key=lambda p: p.relative_to(repo_root).as_posix()):
            if not _is_engine_candidate(path):
                continue
            entrypoints = _discover_entrypoints(path)
            tests = _match_tests(repo_root, path)
            engines.append(
                {
                    "name": path.parent.name if path.name == "__init__.py" else path.stem,
                    "path": path.relative_to(repo_root).as_posix(),
                    "kind": _engine_kind(path),
                    "status": "tested" if tests else "needs-tests",
                    "entrypoints": entrypoints,
                    "tests": tests,
                }
            )
    engines.sort(key=lambda item: (item["name"], item["path"]))
    return engines


def discover_kits(repo_root: Path) -> List[Dict[str, object]]:
    kits_dir = repo_root / "modules"
    if not kits_dir.exists():
        return []
    kits: List[Dict[str, object]] = []
    for child in sorted(kits_dir.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        init_py = child / "__init__.py"
        api = _extract_dunder_all(init_py)
        capabilities = _discover_capabilities(init_py)
        kits.append(
            {
                "name": child.name,
                "path": child.relative_to(repo_root).as_posix(),
                "api": api,
                "capabilities": capabilities,
            }
        )
    return kits


def discover_artifacts(repo_root: Path, extra_paths: Optional[Sequence[Path]] = None) -> List[Dict[str, object]]:
    candidates: List[Path] = []
    for rel in (Path("schema/echo_manifest.schema.json"), Path("tools/echo_manifest.py")):
        candidate = repo_root / rel
        if candidate.exists():
            candidates.append(candidate)
    if extra_paths:
        for path in extra_paths:
            if path.exists():
                candidates.append(path)
    artifacts: List[Dict[str, object]] = []
    for path in sorted(set(candidates), key=lambda p: p.relative_to(repo_root).as_posix()):
        suffix = path.suffix.lstrip(".") or "file"
        artifacts.append(
            {
                "type": suffix,
                "path": path.relative_to(repo_root).as_posix(),
                "content_hash": _file_hash(path),
            }
        )
    return artifacts


def discover_ci_workflows(repo_root: Path) -> List[str]:
    workflows_dir = repo_root / ".github" / "workflows"
    if not workflows_dir.exists():
        return []
    workflows: List[str] = []
    for path in sorted(workflows_dir.glob("*.yml")):
        workflows.append(path.stem)
    for path in sorted(workflows_dir.glob("*.yaml")):
        workflows.append(path.stem)
    return sorted(dict.fromkeys(workflows))


def _git_output(args: Sequence[str], repo_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown"
    return completed.stdout.strip() or "unknown"


def collect_meta(repo_root: Path) -> Dict[str, str]:
    return {
        "commit_sha": _git_output(["rev-parse", "HEAD"], repo_root),
        "branch": _git_output(["rev-parse", "--abbrev-ref", "HEAD"], repo_root),
        "author": _git_output(["log", "-1", "--pretty=%an"], repo_root),
    }


def build_states_section(engines: Sequence[Dict[str, object]]) -> Dict[str, object]:
    cycle = len(engines)
    resonance = sum(len(entry.get("entrypoints", [])) for entry in engines)
    amplification = float(resonance) / cycle if cycle else 0.0
    snapshots = [
        {
            "engine": entry["name"],
            "status": entry["status"],
            "tests": len(entry.get("tests", [])),
        }
        for entry in engines
    ]
    snapshots.sort(key=lambda item: (item["engine"], item["status"]))
    return {
        "cycle": cycle,
        "resonance": resonance,
        "amplification": round(amplification, 3),
        "snapshots": snapshots,
    }


def load_schema() -> Dict[str, object]:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_manifest(path: Path) -> Optional[Dict[str, object]]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def generate_manifest_data(repo_root: Path, existing: Optional[Dict[str, object]] = None) -> ManifestData:
    engines = discover_engines(repo_root)
    kits = discover_kits(repo_root)
    artifacts = discover_artifacts(repo_root)
    ci_workflows = discover_ci_workflows(repo_root)
    states = build_states_section(engines)
    payload: Dict[str, object] = {
        "version": SCHEMA_VERSION,
        "generated_at": _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "engines": engines,
        "states": states,
        "kits": kits,
        "artifacts": artifacts,
        "ci": {"integration": ci_workflows},
        "meta": collect_meta(repo_root),
    }
    if existing:
        existing_copy = dict(existing)
        existing_copy.pop("generated_at", None)
        comparable = dict(payload)
        comparable.pop("generated_at", None)
        if existing_copy == comparable and "generated_at" in existing:
            payload["generated_at"] = existing["generated_at"]
    return ManifestData(payload)


def write_manifest(path: Path, manifest: ManifestData) -> None:
    path.write_text(manifest.to_json() + "\n", encoding="utf-8")


def validate_manifest_payload(manifest: Dict[str, object], schema: Dict[str, object]) -> None:
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda err: err.path)
    if errors:
        messages = [f"{list(error.path)}: {error.message}" for error in errors]
        raise ValueError("Manifest schema validation failed:\n" + "\n".join(messages))


def _normalise(manifest: Dict[str, object]) -> Dict[str, object]:
    normalised = dict(manifest)
    normalised.pop("generated_at", None)
    return normalised


def generate_command(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve() if args.repo else REPO_ROOT
    manifest_path = Path(args.output).resolve() if args.output else DEFAULT_MANIFEST_PATH
    existing = load_manifest(manifest_path) if manifest_path.exists() else None
    manifest = generate_manifest_data(repo_root, existing)
    write_manifest(manifest_path, manifest)
    print(manifest_path)
    return 0


def validate_command(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve() if args.repo else REPO_ROOT
    manifest_path = Path(args.manifest).resolve() if args.manifest else DEFAULT_MANIFEST_PATH
    manifest = load_manifest(manifest_path)
    if manifest is None:
        print(f"Manifest not found at {manifest_path}", file=sys.stderr)
        return 1
    schema = load_schema()
    try:
        validate_manifest_payload(manifest, schema)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    expected = generate_manifest_data(repo_root, manifest).payload
    if _normalise(expected) != _normalise(manifest):
        print("Manifest drift detected. Run echo manifest update and commit.", file=sys.stderr)
        return 1
    return 0


def update_command(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo).resolve() if args.repo else REPO_ROOT
    manifest_path = Path(args.manifest).resolve() if args.manifest else DEFAULT_MANIFEST_PATH
    existing = load_manifest(manifest_path)
    manifest = generate_manifest_data(repo_root, existing)
    previous_serialised = existing and json.dumps(existing, sort_keys=True, separators=(",", ":"))
    new_serialised = manifest.to_json()
    if previous_serialised == new_serialised:
        print("Manifest already up to date.")
        return 0
    write_manifest(manifest_path, manifest)
    schema = load_schema()
    try:
        validate_manifest_payload(manifest.payload, schema)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Updated manifest at {manifest_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the Echo manifest")
    subparsers = parser.add_subparsers(dest="command")

    manifest_parser = subparsers.add_parser("generate", help="Generate the manifest")
    manifest_parser.add_argument("--repo", help="Path to the repository root")
    manifest_parser.add_argument("--output", help="Path to write the manifest")
    manifest_parser.set_defaults(func=generate_command)

    validate_parser = subparsers.add_parser("validate", help="Validate the manifest")
    validate_parser.add_argument("--repo", help="Path to the repository root")
    validate_parser.add_argument("--manifest", help="Path to the manifest file")
    validate_parser.set_defaults(func=validate_command)

    update_parser = subparsers.add_parser("update", help="Regenerate and validate the manifest")
    update_parser.add_argument("--repo", help="Path to the repository root")
    update_parser.add_argument("--manifest", help="Path to the manifest file")
    update_parser.set_defaults(func=update_command)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
