from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.echo_manifest import (
    build_states_section,
    discover_engines,
    discover_kits,
    generate_manifest_data,
)


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path
    (repo / "echo").mkdir()
    (repo / "modules").mkdir()
    (repo / "tests").mkdir()

    (repo / "echo" / "alpha_engine.py").write_text(
        "def cli():\n    return 'alpha'\n",
        encoding="utf-8",
    )
    (repo / "modules" / "kit" ).mkdir()
    (repo / "modules" / "kit" / "__init__.py").write_text(
        "__all__ = ['KitAPI']\n\nclass KitAPI:\n    ...\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_alpha_engine.py").write_text(
        "def test_alpha_engine():\n    assert True\n",
        encoding="utf-8",
    )
    return repo


def test_discover_engines(sample_repo: Path) -> None:
    engines = discover_engines(sample_repo)
    assert engines
    engine = engines[0]
    assert engine["name"] == "alpha_engine"
    assert engine["status"] == "tested"
    assert engine["entrypoints"] == ["cli"]


def test_discover_kits(sample_repo: Path) -> None:
    kits = discover_kits(sample_repo)
    assert kits == [
        {
            "name": "kit",
            "path": "modules/kit",
            "api": ["KitAPI"],
            "capabilities": ["KitAPI"],
        }
    ]


def test_manifest_generation_is_deterministic(sample_repo: Path) -> None:
    first = generate_manifest_data(sample_repo).payload
    second = generate_manifest_data(sample_repo, existing=first).payload
    assert first == second
    states = build_states_section(first["engines"])  # type: ignore[arg-type]
    assert states["cycle"] == len(first["engines"])  # type: ignore[index]
