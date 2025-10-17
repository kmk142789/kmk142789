from __future__ import annotations

from echo_atlas.cli import main as atlas_main

from .atlas_utils import write_sample_files


def test_cli_sync_generates_assets(tmp_path) -> None:
    write_sample_files(tmp_path)
    exit_code = atlas_main(["--root", str(tmp_path), "atlas", "sync"])
    assert exit_code == 0

    report = tmp_path / "docs" / "ATLAS_REPORT.md"
    svg = tmp_path / "artifacts" / "atlas_graph.svg"
    assert report.exists()
    assert svg.exists()


def test_cli_show_outputs_summary(tmp_path, capsys) -> None:
    write_sample_files(tmp_path)
    atlas_main(["--root", str(tmp_path), "atlas", "sync"])
    exit_code = atlas_main(["--root", str(tmp_path), "atlas", "show", "--who", "Echo Maintainers"])
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "Echo Maintainers" in captured
