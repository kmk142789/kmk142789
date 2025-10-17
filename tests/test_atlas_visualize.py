from __future__ import annotations

from pathlib import Path

from echo_atlas.adapters.sqlite import SQLiteAdapter
from echo_atlas.repository import AtlasRepository
from echo_atlas.services import AtlasService


def test_svg_matches_golden(tmp_path) -> None:
    repository = AtlasRepository(adapter=SQLiteAdapter(tmp_path / "atlas.db"))
    service = AtlasService(repository=repository, root=tmp_path)
    service.seed_demo_data()
    svg = service.visualizer.generate_svg().strip()
    golden = (Path(__file__).parent / "golden" / "atlas_seed.svg").read_text(encoding="utf-8").strip()
    assert svg == golden
