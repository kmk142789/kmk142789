"""Command line utilities for maintaining the Echo manifest."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_MANIFEST_PATH = _REPO_ROOT / "echo_manifest.json"
_LEDGER_ENV_VAR = "ECHO_MANIFEST_LEDGER"


def _ledger_path_override() -> Path | None:
    override = os.environ.get(_LEDGER_ENV_VAR)
    return Path(override).resolve() if override else None

_ENGINE_SPECS: Tuple[str, ...] = (
    "echo.bridge_emitter:BridgeEmitter",
    "echo.autonomy:DecentralizedAutonomyEngine",
    "cognitive_harmonics.harmonix_bridge:EchoBridgeHarmonix",
    "cognitive_harmonics.harmonix_evolver:EchoEvolver",
    "echo.evolver:EchoEvolver",
    "modules.echo-memory.memory_engine:EchoMemoryEngine",
    "echo.pulse:EchoPulseEngine",
    "echo.resonance:EchoResonanceEngine",
    "cognitive_harmonics.harmonix_bridge:PolicyEngine",
)

_STATE_SPECS: Tuple[str, ...] = (
    "echo.autonomy:AutonomyDecision",
    "echo.autonomy:AutonomyNode",
    "cognitive_harmonics.harmonix_bridge:BridgeSignals",
    "echo.bridge_emitter:BridgeState",
    "cognitive_harmonics.harmonix_bridge:BridgeTuning",
    "cognitive_harmonics.harmonix_evolver:EchoState",
    "echo.evolver:EmotionalDrive",
    "echo.evolver:EvolverState",
    "cognitive_harmonics.harmonix_bridge:HarmonixBridgeState",
    "modules.echo-memory.memory_engine:MemorySnapshot",
    "echo.orbital_loop:OrbitalState",
    "echo.pulse:Pulse",
    "echo.pulse:PulseEvent",
    "cognitive_harmonics.harmonix_evolver:SystemMetrics",
    "echo.evolver:SystemMetrics",
)

_ASSISTANT_KIT_PATHS: Tuple[str, ...] = (
    "modules/echo-bridge",
    "modules/echo-harmonics",
    "modules/echo-ledger-visualizer",
    "modules/echo-memory",
)


class ManifestError(RuntimeError):
    """Raised when the manifest cannot be constructed."""


def _default_ledger_path() -> Path:
    override = _ledger_path_override()
    return override if override is not None else _REPO_ROOT / "ledger" / "manifest_history.jsonl"


def _ensure_ledger_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _current_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return "UNKNOWN"
    return result.stdout.strip() or "UNKNOWN"


def _ledger_payload(entry: Dict[str, Any]) -> bytes:
    payload = {key: value for key, value in entry.items() if key != "ledger_seal"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _load_manifest_ledger(path: Path | None = None) -> List[Dict[str, Any]]:
    ledger_path = path or _default_ledger_path()
    if not ledger_path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with ledger_path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise ManifestError(
                    f"Invalid ledger entry at line {index} in {ledger_path}: {exc}"
                ) from exc
            entries.append(payload)
    return entries


def _append_manifest_ledger_entry(
    manifest_path: Path,
    manifest_digest: str,
    ledger_path: Path | None = None,
    manifest_written: bool | None = None,
) -> Dict[str, Any]:
    ledger_file = ledger_path or _default_ledger_path()
    _ensure_ledger_directory(ledger_file)
    existing_entries = _load_manifest_ledger(ledger_file)
    previous_seal = existing_entries[-1].get("ledger_seal") if existing_entries else None
    try:
        manifest_reference = str(manifest_path.relative_to(_REPO_ROOT))
    except ValueError:
        manifest_reference = str(manifest_path)
    entry: Dict[str, Any] = {
        "sequence": len(existing_entries) + 1,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifest_path": manifest_reference,
        "manifest_digest": manifest_digest,
        "commit": _current_commit_hash(),
        "ledger_prev": previous_seal,
    }
    if manifest_written is not None:
        entry["manifest_written"] = manifest_written
    entry["ledger_seal"] = hashlib.sha256(_ledger_payload(entry)).hexdigest()
    with ledger_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def _verify_commit_signature(commit_hash: str) -> bool | None:
    if not commit_hash or commit_hash == "UNKNOWN":
        return None
    if shutil.which("gpg") is None:
        return None
    try:
        subprocess.run(
            ["git", "verify-commit", commit_hash],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return False
    except OSError:  # pragma: no cover - platform specific
        return None
    return True


def _stable_digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_manifest_bytes(payload: Dict[str, Any]) -> bytes:
    manifest_body = dict(payload)
    manifest_body.pop("manifest_digest", None)
    return json.dumps(manifest_body, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _load_module(module_path: str) -> ModuleType:
    """Import a module, falling back to manual loading for dashed paths."""

    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError:
        pass

    relative = Path(*module_path.split("."))
    candidates = [
        _REPO_ROOT / (str(relative) + ".py"),
        _REPO_ROOT / relative / "__init__.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            module_name = module_path.replace("-", "_")
            spec = importlib.util.spec_from_file_location(module_name, candidate)
            if spec is None or spec.loader is None:
                raise ManifestError(f"Unable to load module specification for {module_path}")
            module = importlib.util.module_from_spec(spec)
            loader = spec.loader
            assert loader is not None
            loader.exec_module(module)
            return module
    raise ManifestError(f"Unable to locate module {module_path}")


def _resolve_object(spec: str) -> Tuple[Any, str]:
    """Return the object referenced by ``spec`` and the module spec string."""

    if ":" not in spec:
        raise ManifestError(f"Invalid spec {spec!r}")
    module_path, attr_path = spec.split(":", 1)
    module = _load_module(module_path)
    obj: Any = module
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj, module_path


def _docstring_summary(doc: str) -> str:
    paragraphs = [chunk.strip() for chunk in doc.split("\n\n") if chunk.strip()]
    return paragraphs[0] if paragraphs else ""


def _public_methods(obj: Any) -> List[str]:
    methods: List[str] = []
    for name, member in inspect.getmembers(obj, inspect.isfunction):
        qualname = getattr(member, "__qualname__", "")
        if not qualname.startswith(getattr(obj, "__qualname__", "")):
            continue
        if name.startswith("_"):
            continue
        methods.append(name)
    return sorted(dict.fromkeys(methods))


def _source_digest(obj: Any) -> str:
    try:
        source = inspect.getsource(obj)
    except (OSError, TypeError):
        source = ""
    return _stable_digest(source.encode("utf-8"))


def _build_engine_entry(spec: str) -> Dict[str, Any]:
    obj, module_spec = _resolve_object(spec)
    doc = inspect.getdoc(obj) or ""
    entry = {
        "name": getattr(obj, "__name__", str(obj)),
        "module": getattr(obj, "__module__", module_spec.replace("-", "_")),
        "module_spec": module_spec,
        "qualname": getattr(obj, "__qualname__", getattr(obj, "__name__", "")),
        "summary": _docstring_summary(doc),
        "doc_digest": _stable_digest(doc.encode("utf-8")),
        "source_digest": _source_digest(obj),
        "public_methods": _public_methods(obj),
    }
    return entry


def _build_state_entry(spec: str) -> Dict[str, Any]:
    obj, module_spec = _resolve_object(spec)
    doc = inspect.getdoc(obj) or ""
    is_data = is_dataclass(obj)
    field_names: List[str] = []
    if is_data:
        field_names = [field.name for field in fields(obj)]
    entry = {
        "name": getattr(obj, "__name__", str(obj)),
        "module": getattr(obj, "__module__", module_spec.replace("-", "_")),
        "module_spec": module_spec,
        "dataclass": is_data,
        "fields": field_names,
        "field_count": len(field_names),
        "summary": _docstring_summary(doc),
        "doc_digest": _stable_digest(doc.encode("utf-8")),
        "source_digest": _source_digest(obj),
    }
    return entry


def _digest_directory(path: Path) -> Tuple[str, int]:
    hasher = hashlib.sha256()
    count = 0
    for item in sorted(path.rglob("*")):
        if item.is_dir():
            continue
        if item.name.endswith((".pyc", ".pyo")) or item.name == "__pycache__":
            continue
        count += 1
        relative = item.relative_to(path)
        hasher.update(str(relative.as_posix()).encode("utf-8"))
        hasher.update(item.read_bytes())
    return hasher.hexdigest(), count


def _parse_module_docstring(path: Path) -> Tuple[str, List[str]]:
    if not path.exists():
        return "", []
    module = ast.parse(path.read_text(encoding="utf-8"))
    doc = ast.get_docstring(module) or ""
    exports: List[str] = []
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        exports = [
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        ]
    return doc, exports


def _build_assistant_entry(path_str: str) -> Dict[str, Any]:
    path = (_REPO_ROOT / path_str).resolve()
    if not path.exists():
        raise ManifestError(f"Assistant kit directory {path_str} does not exist")
    digest, file_count = _digest_directory(path)
    init_path = path / "__init__.py"
    doc, exports = _parse_module_docstring(init_path)
    entry = {
        "name": path.name,
        "path": path_str,
        "summary": _docstring_summary(doc),
        "doc_digest": _stable_digest(doc.encode("utf-8")),
        "exports": exports,
        "file_count": file_count,
        "digest": digest,
    }
    return entry


def build_manifest() -> Dict[str, Any]:
    """Construct the canonical manifest dictionary."""

    engines = sorted((_build_engine_entry(spec) for spec in _ENGINE_SPECS), key=lambda item: (item["name"], item["module_spec"]))
    states = sorted((_build_state_entry(spec) for spec in _STATE_SPECS), key=lambda item: (item["name"], item["module_spec"]))
    kits = sorted((_build_assistant_entry(path) for path in _ASSISTANT_KIT_PATHS), key=lambda item: item["name"])
    manifest = {
        "format": "echo.manifest/v2",
        "engines": engines,
        "states": states,
        "assistant_kits": kits,
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest["manifest_digest"] = _stable_digest(canonical)
    return manifest


def _write_manifest(path: Path, manifest: Dict[str, Any]) -> bool:
    text = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == text:
        print(f"Manifest already up to date at {path}")
        return False
    path.write_text(text, encoding="utf-8")
    print(f"Manifest written to {path}")
    return True


def refresh_manifest(path: Path | None = None, ledger_path: Path | None = None) -> Path:
    """Rebuild the manifest JSON file and append a ledger entry."""

    manifest = build_manifest()
    output_path = path or _DEFAULT_MANIFEST_PATH
    written = _write_manifest(output_path, manifest)
    _append_manifest_ledger_entry(
        output_path,
        manifest["manifest_digest"],
        ledger_path=ledger_path,
        manifest_written=written,
    )
    return output_path


def verify_manifest(path: Path | None = None) -> bool:
    """Validate that the manifest matches the current repository state."""

    expected = build_manifest()
    manifest_path = path or _DEFAULT_MANIFEST_PATH
    if not manifest_path.exists():
        print(f"Manifest missing at {manifest_path}")
        return False
    try:
        on_disk = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        print(f"Failed to parse manifest {manifest_path}: {exc}")
        return False
    if on_disk != expected:
        on_disk_text = json.dumps(on_disk, indent=2, sort_keys=True, ensure_ascii=False).splitlines()
        expected_text = json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False).splitlines()
        diff = "\n".join(
            line for line in _unified_diff(on_disk_text, expected_text)
        )
        print("Manifest drift detected. Run 'echo manifest refresh' to update.")
        if diff:
            print(diff)
        return False
    return True


def load_manifest_ledger(path: Path | None = None) -> List[Dict[str, Any]]:
    """Return all manifest ledger entries."""

    return _load_manifest_ledger(path)


def manifest_status(
    manifest_path: Path | None = None,
    ledger_path: Path | None = None,
) -> Dict[str, Any]:
    """Return status information comparing the manifest to the ledger."""

    manifest_file = manifest_path or _DEFAULT_MANIFEST_PATH
    ledger_file = ledger_path or _default_ledger_path()
    entries = load_manifest_ledger(ledger_file)
    manifest_exists = manifest_file.exists()
    manifest_digest = None
    manifest_payload: Dict[str, Any] | None = None
    if manifest_exists:
        try:
            manifest_payload = json.loads(manifest_file.read_text(encoding="utf-8"))
            canonical = _canonical_manifest_bytes(manifest_payload)
            manifest_digest = hashlib.sha256(canonical).hexdigest()
        except json.JSONDecodeError:
            manifest_exists = False
    latest_entry = entries[-1] if entries else None
    ledger_match = bool(
        manifest_exists
        and latest_entry is not None
        and latest_entry.get("manifest_digest") == manifest_digest
    )
    return {
        "manifest_path": manifest_file,
        "ledger_path": ledger_file,
        "ledger_entries": len(entries),
        "manifest_exists": manifest_exists,
        "manifest_digest": manifest_digest,
        "manifest_payload": manifest_payload,
        "latest_entry": latest_entry,
        "ledger_match": ledger_match,
    }


def verify_manifest_ledger(
    manifest_path: Path | None = None,
    ledger_path: Path | None = None,
    *,
    require_gpg: bool = False,
) -> bool:
    """Validate that the manifest ledger is an append-only seal of the manifest."""

    status = manifest_status(manifest_path, ledger_path)
    ledger_file = status["ledger_path"]
    entries = load_manifest_ledger(ledger_file)
    if not entries:
        print(f"Manifest ledger missing at {ledger_file}")
        return False

    expected_prev = None
    for index, entry in enumerate(entries, 1):
        if entry.get("sequence") != index:
            print(
                f"Ledger sequence mismatch at entry {index}:"
                f" expected {index}, found {entry.get('sequence')}"
            )
            return False
        payload_hash = hashlib.sha256(_ledger_payload(entry)).hexdigest()
        if entry.get("ledger_seal") != payload_hash:
            print(f"Ledger seal mismatch at entry {index}")
            return False
        if entry.get("ledger_prev") != expected_prev:
            print(f"Ledger chain break detected at entry {index}")
            return False
        expected_prev = payload_hash

    if not status["manifest_exists"] or status["manifest_digest"] is None:
        print(f"Manifest missing or unreadable at {status['manifest_path']}")
        return False
    latest_entry = status["latest_entry"] or {}
    if latest_entry.get("manifest_digest") != status["manifest_digest"]:
        print("Ledger digest does not match current manifest")
        return False

    commit_hash = latest_entry.get("commit", "")
    gpg_result = _verify_commit_signature(str(commit_hash))
    if require_gpg and gpg_result is not True:
        print("GPG verification required but failed or unavailable")
        return False
    if gpg_result is False:
        print("Warning: Commit signature verification failed")
        return True
    return True


def _unified_diff(a: Iterable[str], b: Iterable[str]) -> List[str]:
    import difflib

    return list(difflib.unified_diff(list(a), list(b), fromfile="on-disk", tofile="expected", lineterm=""))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="echo", description="Echo command line utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest", help="Maintain the Echo manifest")
    manifest_sub = manifest_parser.add_subparsers(dest="manifest_command", required=True)

    refresh_parser = manifest_sub.add_parser("refresh", help="Regenerate the manifest JSON deterministically")
    refresh_parser.add_argument("--path", type=Path, help="Optional output path")
    refresh_parser.add_argument("--ledger", type=Path, help="Optional ledger path")
    refresh_parser.set_defaults(
        func=lambda args: 0
        if refresh_manifest(args.path, ledger_path=args.ledger)
        else 1
    )

    verify_parser = manifest_sub.add_parser("verify", help="Validate the manifest digests and structure")
    verify_parser.add_argument("--path", type=Path, help="Optional manifest path")
    verify_parser.set_defaults(func=lambda args: 0 if verify_manifest(args.path) else 1)

    status_parser = manifest_sub.add_parser("status", help="Show manifest and ledger status")
    status_parser.add_argument("--path", type=Path, help="Optional manifest path")
    status_parser.add_argument("--ledger", type=Path, help="Optional ledger path")

    def _status_cmd(args: argparse.Namespace) -> int:
        info = manifest_status(args.path, args.ledger)
        latest = info["latest_entry"]
        print(f"Manifest: {info['manifest_path']}")
        print(f"Ledger:   {info['ledger_path']}")
        print(f"Ledger entries: {info['ledger_entries']}")
        if latest:
            print(f"Latest digest: {latest['manifest_digest']}")
            print(f"Latest commit: {latest['commit']}")
            print(f"Ledger seal:  {latest['ledger_seal']}")
        else:
            print("Ledger empty")
        if info["ledger_match"]:
            print("Manifest digest matches latest ledger entry")
            return 0
        print("Manifest digest does not match ledger entry")
        return 1

    status_parser.set_defaults(func=_status_cmd)

    ledger_parser = manifest_sub.add_parser("ledger", help="Inspect the manifest ledger history")
    ledger_parser.add_argument("--path", type=Path, help="Optional manifest path")
    ledger_parser.add_argument("--ledger", type=Path, help="Optional ledger path")
    ledger_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of entries to display (0 for all)",
    )
    ledger_parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify ledger hash chain and manifest seal",
    )
    ledger_parser.add_argument(
        "--require-gpg",
        action="store_true",
        help="Require commit signature verification when using --verify",
    )

    def _ledger_cmd(args: argparse.Namespace) -> int:
        entries = load_manifest_ledger(args.ledger)
        to_show = entries if args.limit == 0 else entries[-args.limit :]
        for entry in to_show:
            print(json.dumps(entry, sort_keys=True))
        if not entries:
            return 0
        if args.verify:
            ok = verify_manifest_ledger(
                manifest_path=args.path,
                ledger_path=args.ledger,
                require_gpg=args.require_gpg,
            )
            return 0 if ok else 1
        return 0

    ledger_parser.set_defaults(func=_ledger_cmd)

    args = parser.parse_args(list(argv) if argv is not None else None)
    func = getattr(args, "func", None)
    if func is None:  # pragma: no cover - argparse should enforce
        parser.print_help()
        return 1
    return func(args)


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
