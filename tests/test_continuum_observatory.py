from collections import OrderedDict
from pathlib import Path

from echo.continuum_observatory import (
    ContinuumObservatory,
    ContinuumSnapshot,
    LaneStats,
    build_default_lane_map,
    _render_heatmap,
    _render_lane_table,
)


def test_observatory_groups_files_into_lanes(tmp_path):
    repo = tmp_path
    exec_dir = repo / "packages" / "core"
    exec_dir.mkdir(parents=True)
    docs_dir = repo / "docs"
    docs_dir.mkdir()

    code_path = exec_dir / "module.py"
    code_path.write_text("print('hi')  # TODO refine\n", encoding="utf-8")

    doc_path = docs_dir / "guide.md"
    doc_path.write_text("Guidance text\nFIXME add diagrams\n", encoding="utf-8")

    # Ignored directories should not be counted
    ignored_dir = repo / ".git"
    ignored_dir.mkdir()
    (ignored_dir / "config").write_text("ignored", encoding="utf-8")

    observatory = ContinuumObservatory(root=repo)
    snapshot = observatory.scan()

    exec_stats = snapshot.lanes["execution_stack"]
    assert exec_stats.file_count == 1
    assert exec_stats.code_count == 1

    policy_stats = snapshot.lanes["governance_policy"]
    assert policy_stats.doc_count == 1

    todos = observatory.scan_todos(limit=5)
    assert len(todos) >= 2
    keywords = {match.keyword for match in todos}
    assert {"TODO", "FIXME"}.issubset(keywords)


def test_scan_todos_respects_word_boundaries(tmp_path):
    doc = tmp_path / "README.md"
    doc.write_text(
        "| `ECHO_BRIDGE_MASTODON_INSTANCE` | _unset_ | description |\n" "<!-- TODO add docs -->\n",
        encoding="utf-8",
    )

    observatory = ContinuumObservatory(root=tmp_path)
    matches = observatory.scan_todos(limit=5)

    assert len(matches) == 1
    assert matches[0].keyword == "TODO"
    assert "MASTODON" not in matches[0].line.upper()
    assert "add docs" in matches[0].line


def test_scan_todos_supports_custom_keywords(tmp_path):
    doc = tmp_path / "notes.txt"
    doc.write_text("NOTE: future work\n", encoding="utf-8")

    observatory = ContinuumObservatory(root=tmp_path)
    matches = observatory.scan_todos(limit=5, keywords=("NOTE",))

    assert len(matches) == 1
    assert matches[0].keyword == "NOTE"
    assert "future work" in matches[0].line


def test_scan_todos_orders_results_by_path_and_line(tmp_path):
    for name in ["b_dir", "a_dir"]:
        folder = tmp_path / name
        folder.mkdir()
        (folder / "task.txt").write_text("TODO first\nTODO second\n", encoding="utf-8")

    observatory = ContinuumObservatory(root=tmp_path)
    matches = observatory.scan_todos(limit=3)

    rel_paths = [match.path.relative_to(tmp_path).as_posix() for match in matches]
    assert rel_paths[0].startswith("a_dir")
    assert rel_paths[1].startswith("a_dir")
    assert rel_paths[2].startswith("b_dir")


def test_default_lane_map_isolated_copy():
    first = build_default_lane_map()
    first["execution_stack"] = ("custom",)
    second = build_default_lane_map()
    assert second["execution_stack"] != ("custom",)


def test_lane_and_heatmap_limits_truncate_output():
    lanes = OrderedDict(
        (
            (
                "alpha",
                LaneStats(
                    lane="alpha",
                    directories=("a",),
                    file_count=30,
                    total_bytes=10,
                    doc_count=5,
                    code_count=25,
                    newest_mtime=0.0,
                ),
            ),
            (
                "beta",
                LaneStats(
                    lane="beta",
                    directories=("b",),
                    file_count=20,
                    total_bytes=5,
                    doc_count=4,
                    code_count=16,
                    newest_mtime=0.0,
                ),
            ),
            (
                "gamma",
                LaneStats(
                    lane="gamma",
                    directories=("c",),
                    file_count=10,
                    total_bytes=2,
                    doc_count=3,
                    code_count=7,
                    newest_mtime=0.0,
                ),
            ),
        )
    )
    snapshot = ContinuumSnapshot(
        root=Path("/tmp/repo"),
        total_files=60,
        total_bytes=17,
        latest_mtime=0.0,
        lanes=lanes,
        misc=LaneStats(lane="misc", directories=("<unmapped>",)),
    )

    table = _render_lane_table(snapshot, sort_field="files", descending=True, limit=2)
    assert "alpha" in table and "beta" in table
    assert "gamma" not in table
    assert "showing top 2 lanes" in table

    heatmap = _render_heatmap(snapshot, sort_field="files", descending=True, limit=1)
    assert "alpha" in heatmap
    assert "beta" not in heatmap
    assert "showing top 1 lanes" in heatmap
