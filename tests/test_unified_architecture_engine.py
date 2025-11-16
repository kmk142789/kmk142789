from pathlib import Path
import importlib.util
import sys


def _load_engine_class():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "packages/core/src/echo/unified_architecture_engine.py"
    spec = importlib.util.spec_from_file_location(
        "echo.unified_architecture_engine", module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # ensure relative imports resolve
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.UnifiedArchitectureEngine


UnifiedArchitectureEngine = _load_engine_class()


def _write_module(path: Path, name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# test module\n", encoding="utf-8")


def test_blueprint_groups_modules(tmp_path):
    module_root = tmp_path / "echo"
    _write_module(module_root / "continuum_bridge.py", "continuum_bridge")
    _write_module(module_root / "pulse/pulse_engine.py", "pulse_engine")
    _write_module(module_root / "creative/story_orchestrator.py", "story_orchestrator")

    engine = UnifiedArchitectureEngine(module_root=module_root)
    blueprint = engine.build_blueprint()

    assert blueprint["total_modules"] == 3
    assert "continuum" in blueprint["category_summary"]
    assert "pulse" in blueprint["category_summary"]
    assert "creative" in blueprint["category_summary"]

    keystone_paths = {entry["relative_path"] for entry in blueprint["keystones"]}
    assert "pulse/pulse_engine.py" in keystone_paths

    markdown = engine.to_markdown(blueprint)
    assert "Unified Architecture" in markdown
