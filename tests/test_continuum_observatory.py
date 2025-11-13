from echo.continuum_observatory import (
    ContinuumObservatory,
    build_default_lane_map,
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


def test_default_lane_map_isolated_copy():
    first = build_default_lane_map()
    first["execution_stack"] = ("custom",)
    second = build_default_lane_map()
    assert second["execution_stack"] != ("custom",)
