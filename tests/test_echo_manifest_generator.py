"""Tests for the Echo manifest generator."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from tools.echo_manifest import EchoManifestGenerator


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_engine_discovery_and_ordering(tmp_path: Path) -> None:
    _write(
        tmp_path / "echo" / "alpha_engine.py",
        """def main_alpha():\n    return 'alpha'\n\n\ndef cli_alpha():\n    return 'alpha-cli'\n""",
    )
    _write(tmp_path / "echo" / "beta" / "__init__.py", """def main():\n    return 'beta'\n""")
    _write(tmp_path / "echo" / "gamma" / "main.py", """def main():\n    return 'gamma'\n""")

    _write(tmp_path / "modules" / "toolkit" / "__init__.py", """VALUE = 1\n""")
    _write(tmp_path / "modules" / "toolkit" / "core.py", """def cli_tool():\n    return 'tool'\n""")

    _write(tmp_path / "tests" / "test_alpha_flow.py", """def test_alpha():\n    assert True\n""")
    _write(tmp_path / "tests" / "test_gamma.py", """def test_gamma():\n    assert True\n""")

    artifact_path = tmp_path / "manifest" / "sample.json"
    _write(artifact_path, json.dumps({"value": 1}))

    generator = EchoManifestGenerator(tmp_path)
    manifest = generator.build(generated_at="2024-01-01T00:00:00Z")

    engine_paths = [engine["path"] for engine in manifest["engines"]]
    assert engine_paths == sorted(engine_paths)

    alpha_engine = next(engine for engine in manifest["engines"] if engine["name"] == "alpha")
    assert alpha_engine["entrypoints"] == ["cli_alpha", "main_alpha"]
    assert alpha_engine["tests"] == ["tests/test_alpha_flow.py"]

    states = manifest["states"]
    assert states["cycle"] == len(manifest["engines"])
    assert states["resonance"] == sum(len(engine["tests"]) for engine in manifest["engines"])

    kits = manifest["kits"]
    assert kits
    toolkit = next(kit for kit in kits if kit["name"] == "toolkit")
    assert toolkit["capabilities"] == ["core"]

    artifacts = manifest["artifacts"]
    digest = sha256(artifact_path.read_bytes()).hexdigest()[:12]
    assert any(item["content_hash"] == digest for item in artifacts)


def test_empty_repository(tmp_path: Path) -> None:
    generator = EchoManifestGenerator(tmp_path)
    manifest = generator.build(generated_at="2024-01-01T00:00:00Z")

    assert manifest["engines"] == []
    assert manifest["kits"] == []
    assert manifest["artifacts"] == []
    assert manifest["states"] == {
        "cycle": 0,
        "resonance": 0,
        "amplification": 0,
        "snapshots": [],
    }


def test_meta_changes_refresh_timestamp(tmp_path: Path) -> None:
    generator = EchoManifestGenerator(tmp_path)
    manifest = generator.build(generated_at="2024-01-01T00:00:00Z")

    repeat = generator.build(previous=manifest)
    assert repeat["generated_at"] == "2024-01-01T00:00:00Z"

    generator._meta = lambda: {  # type: ignore[attr-defined]
        "commit_sha": "deadbeef",
        "branch": "main",
        "author": "tester",
    }
    refreshed = generator.build(previous=manifest)

    assert refreshed["meta"]["commit_sha"] == "deadbeef"
    assert refreshed["generated_at"] != manifest["generated_at"]
