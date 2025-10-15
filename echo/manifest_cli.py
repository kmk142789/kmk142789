"""Command line utilities for maintaining the Echo manifest."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import importlib.util
import inspect
import json
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List, Tuple

from .amplify import AmplificationEngine, AmplifyMetrics, AmplifySnapshot

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_MANIFEST_PATH = _REPO_ROOT / "echo_manifest.json"

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


def _stable_digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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
        "amplification": AmplificationEngine().manifest_summary(),
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest["manifest_digest"] = _stable_digest(canonical)
    return manifest


def _write_manifest(path: Path, manifest: Dict[str, Any]) -> None:
    text = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == text:
        print(f"Manifest already up to date at {path}")
        return
    path.write_text(text, encoding="utf-8")
    print(f"Manifest written to {path}")


def refresh_manifest(path: Path | None = None) -> Path:
    """Rebuild the manifest JSON file."""

    manifest = build_manifest()
    output_path = path or _DEFAULT_MANIFEST_PATH
    _write_manifest(output_path, manifest)
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


def _unified_diff(a: Iterable[str], b: Iterable[str]) -> List[str]:
    import difflib

    return list(difflib.unified_diff(list(a), list(b), fromfile="on-disk", tofile="expected", lineterm=""))


def _amplify_engine() -> AmplificationEngine:
    return AmplificationEngine()


def _empty_snapshot() -> AmplifySnapshot:
    metrics = AmplifyMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return AmplifySnapshot(
        cycle=0,
        metrics=metrics,
        index=0.0,
        timestamp="1970-01-01T00:00:00Z",
        commit_sha="UNKNOWN",
    )


def _handle_manifest_refresh(args: argparse.Namespace) -> int:
    refresh_manifest(args.path)
    return 0


def _handle_manifest_verify(args: argparse.Namespace) -> int:
    return 0 if verify_manifest(args.path) else 1


def _handle_amplify_now(args: argparse.Namespace) -> int:
    engine = _amplify_engine()
    snapshot = engine.latest_snapshot()
    if snapshot is None:
        print("No amplification snapshots recorded yet. Showing placeholder metrics.")
        snapshot = _empty_snapshot()
    print(engine.render_snapshot(snapshot))
    print(snapshot.to_json())
    return 0


def _handle_amplify_log(args: argparse.Namespace) -> int:
    engine = _amplify_engine()
    print(engine.render_log(limit=args.limit))
    snapshots = engine.snapshots()[-args.limit :]
    if snapshots:
        indices = [snapshot.index for snapshot in snapshots]
        print(f"Sparkline: {engine.sparkline(indices)}")
    return 0


def _handle_amplify_gate(args: argparse.Namespace) -> int:
    engine = _amplify_engine()
    minimum = args.minimum
    ok, average = engine.gate_check(minimum)
    snapshot = engine.latest_snapshot()
    if average is None or snapshot is None:
        print("No amplification snapshots available for gate evaluation.")
        return 1
    engine.update_manifest_gate(minimum)
    if ok:
        print(f"Amplify gate satisfied: rolling index {average:.2f} ≥ {minimum:.2f}")
        return 0
    print(f"Amplify gate failed: rolling index {average:.2f} < {minimum:.2f}")
    for nudge in engine.nudges_for_snapshot(snapshot):
        print(f"🔁 {nudge}")
    return 1


def _handle_forecast(args: argparse.Namespace) -> int:
    from .tools.forecast import blended_forecast, render_forecast

    engine = _amplify_engine()
    snapshots = engine.snapshots()
    if not snapshots:
        print("No amplification snapshots recorded yet.")
        return 1
    history = snapshots[-args.cycles :]
    indices = [snapshot.index for snapshot in history]
    cycles = [snapshot.cycle for snapshot in history]
    result = blended_forecast(indices, steps=3)
    last_cycle = cycles[-1] if cycles else 0
    output = render_forecast(
        result,
        cycles=cycles,
        last_cycle=last_cycle,
        include_plot=args.plot,
        sparkline=engine.sparkline,
    )
    print(output)
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="echo", description="Echo command line utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest", help="Maintain the Echo manifest")
    manifest_sub = manifest_parser.add_subparsers(dest="manifest_command", required=True)

    refresh_parser = manifest_sub.add_parser("refresh", help="Regenerate the manifest JSON deterministically")
    refresh_parser.add_argument("--path", type=Path, help="Optional output path")
    refresh_parser.set_defaults(func=_handle_manifest_refresh)

    verify_parser = manifest_sub.add_parser("verify", help="Validate the manifest digests and structure")
    verify_parser.add_argument("--path", type=Path, help="Optional manifest path")
    verify_parser.set_defaults(func=_handle_manifest_verify)

    amplify_parser = subparsers.add_parser("amplify", help="Inspect amplification metrics")
    amplify_sub = amplify_parser.add_subparsers(dest="amplify_command", required=True)

    amplify_now = amplify_sub.add_parser("now", help="Show the latest amplification snapshot")
    amplify_now.set_defaults(func=_handle_amplify_now)

    amplify_log = amplify_sub.add_parser("log", help="Render the recent amplification log")
    amplify_log.add_argument("--limit", type=int, default=10, help="Number of cycles to include")
    amplify_log.set_defaults(func=_handle_amplify_log)

    amplify_gate = amplify_sub.add_parser("gate", help="Validate amplification gate against threshold")
    amplify_gate.add_argument("--min", dest="minimum", type=float, required=True, help="Minimum acceptable amplify index")
    amplify_gate.set_defaults(func=_handle_amplify_gate)

    forecast_parser = subparsers.add_parser("forecast", help="Forecast amplification index trends")
    forecast_parser.add_argument("--cycles", type=int, default=12, help="Number of historical cycles to analyse")
    forecast_parser.add_argument("--plot", action="store_true", help="Render an ASCII sparkline for the projection")
    forecast_parser.set_defaults(func=_handle_forecast)

    args = parser.parse_args(list(argv) if argv is not None else None)
    func = getattr(args, "func", None)
    if func is None:  # pragma: no cover - argparse should enforce
        parser.print_help()
        return 1
    return func(args)


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
