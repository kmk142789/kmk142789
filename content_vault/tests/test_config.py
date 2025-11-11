from __future__ import annotations

from pathlib import Path

from vault_config.loader import ConfigLoader


def test_loader_tracks_versions(tmp_path: Path):
    source = Path(__file__).resolve().parents[1]
    loader = ConfigLoader()
    config = loader.load(source / "configs" / "config.v1.yaml")
    assert loader.current_version == 1
    assert config["services"]["storage"]["chunk_size"] == 4096

    config2 = loader.load(source / "configs" / "config.v2.json")
    assert loader.current_version == 2
    assert any(dep["name"] == "sqlite" for dep in config2["dependencies"])

    rolled = loader.rollback(1)
    assert rolled["version"] == 1

    changelog = loader.changelog_path.read_text()
    assert "config.v2.json" in changelog
