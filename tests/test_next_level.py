from __future__ import annotations

import json
from pathlib import Path

import sys

from next_level import (
    Task,
    build_roadmap,
    build_summary_payload,
    DEFAULT_HOTSPOT_LIMIT,
    discover_tasks,
    update_roadmap,
    main,
)


def test_discover_tasks_and_update_roadmap(tmp_path):
    source = tmp_path / "module.py"
    source.write_text("""\n# TODO improve the signal\nvalue = 42\n# FIXME tighten the focus\n""", encoding="utf-8")

    tasks = discover_tasks(tmp_path)
    assert len(tasks) == 2
    assert tasks[0].tag == "TODO"

    roadmap = tmp_path / "ROADMAP.md"
    update_roadmap(tmp_path, roadmap)
    contents = roadmap.read_text()
    assert "TODO" in contents
    assert "FIXME" in contents


def test_discover_tasks_includes_hack(tmp_path):
    source = tmp_path / "module.py"
    source.write_text("""# HACK temporary bypass\nvalue = 42\n""", encoding="utf-8")

    tasks = discover_tasks(tmp_path)
    assert len(tasks) == 1
    assert tasks[0].tag == "HACK"
    assert tasks[0].text == "temporary bypass"


def test_build_roadmap_handles_empty(tmp_path):
    content = build_roadmap([], tmp_path)
    assert "No TODO" in content


def test_discover_tasks_skips_common_virtualenvs(tmp_path):
    """Ensure virtual environment directories are skipped by default."""

    skipped = tmp_path / ".venv" / "module.py"
    skipped.parent.mkdir()
    skipped.write_text("# TODO inside virtualenv\n", encoding="utf-8")

    direnv = tmp_path / ".direnv" / "module.py"
    direnv.parent.mkdir()
    direnv.write_text("# TODO inside direnv\n", encoding="utf-8")

    included = tmp_path / "app.py"
    included.write_text("# TODO keep me\n", encoding="utf-8")

    tasks = discover_tasks(tmp_path)
    assert all(task.path != skipped for task in tasks)
    assert all(task.path != direnv for task in tasks)
    assert any(task.path == included for task in tasks)


def test_update_roadmap_supports_stdout_json(tmp_path, capsys):
    source = tmp_path / "module.py"
    source.write_text("# TODO stream summary\n", encoding="utf-8")

    roadmap = tmp_path / "ROADMAP.md"
    update_roadmap(tmp_path, roadmap, json_output_path=Path("-"))

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["totals"]["overall"] == 1
    assert payload["tasks"][0]["path"].endswith("module.py")


def test_build_summary_payload_includes_per_file(tmp_path):
    first = tmp_path / "first.py"
    second = tmp_path / "nested" / "second.py"
    second.parent.mkdir()

    first.write_text("# TODO alpha\n# TODO beta\n", encoding="utf-8")
    second.write_text("# FIXME gamma\n", encoding="utf-8")

    tasks = discover_tasks(tmp_path)
    payload = build_summary_payload(tasks, tmp_path)

    assert payload["totals"]["per_file"] == {
        "first.py": 2,
        "nested/second.py": 1,
    }


def test_discover_tasks_in_block_comments(tmp_path):
    source = tmp_path / "engine.c"
    source.write_text(
        """/*\n * TODO reconnect the lattice\n * FIXME restore resonance\n */\n""",
        encoding="utf-8",
    )

    tasks = discover_tasks(tmp_path)
    assert {task.tag for task in tasks} == {"TODO", "FIXME"}
    assert {task.text for task in tasks} == {
        "reconnect the lattice",
        "restore resonance",
    }
    assert {task.line for task in tasks} == {2, 3}


def test_discover_tasks_in_html_comments(tmp_path):
    source = tmp_path / "index.html"
    source.write_text(
        """<div>\n    <!-- TODO align portal -->\n    <span>Echo</span>\n</div>\n""",
        encoding="utf-8",
    )

    tasks = discover_tasks(tmp_path)
    assert len(tasks) == 1
    assert tasks[0].tag == "TODO"
    assert tasks[0].text == "align portal"
    assert tasks[0].line == 2


def test_discover_tasks_in_docstrings(tmp_path):
    source = tmp_path / "module.py"
    source.write_text(
        """def calibrate():\n    \"\"\"\n    TODO harmonize resonance\n    \"\"\"\n    pass\n""",
        encoding="utf-8",
    )

    tasks = discover_tasks(tmp_path)
    assert len(tasks) == 1
    assert tasks[0].tag == "TODO"
    assert tasks[0].text == "harmonize resonance"
    assert tasks[0].line == 3


def test_discover_tasks_in_sql_line_comments(tmp_path):
    source = tmp_path / "schema.sql"
    source.write_text(
        """SELECT 1; -- TODO annotate query
UPDATE core SET active = 1 -- FIXME tighten constraint
""",
        encoding="utf-8",
    )

    tasks = discover_tasks(tmp_path)
    assert len(tasks) == 2
    assert {task.tag for task in tasks} == {"TODO", "FIXME"}
    assert any(task.text == "annotate query" and task.line == 1 for task in tasks)
    assert any(task.text == "tighten constraint" and task.line == 2 for task in tasks)


def test_discover_tasks_respects_max_file_size(tmp_path):
    large = tmp_path / "large.py"
    large_payload = "# TODO expansive refactor\n" + ("x" * 2048)
    large.write_text(large_payload, encoding="utf-8")

    included = tmp_path / "included.py"
    included.write_text("# TODO keep me\n", encoding="utf-8")

    small_limit = len(large_payload) - 1
    tasks = discover_tasks(tmp_path, max_file_size=small_limit)
    assert all(task.path != large for task in tasks)
    assert any(task.path == included for task in tasks)

    generous_limit = len(large_payload) + 10
    tasks_with_large = discover_tasks(tmp_path, max_file_size=generous_limit)
    assert any(task.path == large for task in tasks_with_large)
    assert any(task.path == included for task in tasks_with_large)


def test_discover_tasks_supports_nested_skip_paths(tmp_path):
    nested_dir = tmp_path / "src" / "module" / "depth"
    nested_dir.mkdir(parents=True)
    skipped = nested_dir / "skipped.py"
    skipped.write_text("# TODO hidden\n", encoding="utf-8")

    included = tmp_path / "src" / "other.py"
    included.write_text("# TODO keep\n", encoding="utf-8")

    tasks = discover_tasks(tmp_path, skip_dirs=["src/module"])
    assert all(task.path != skipped for task in tasks)
    assert any(task.path == included for task in tasks)


def test_discover_tasks_handles_platform_specific_paths(tmp_path):
    nested = tmp_path / "src" / "module" / "file.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("# TODO hidden\n", encoding="utf-8")

    keep = tmp_path / "src" / "module_two.py"
    keep.write_text("# TODO keep\n", encoding="utf-8")

    windows_style = "src\\module"
    tasks = discover_tasks(tmp_path, skip_dirs=[windows_style])
    assert all(task.path != nested for task in tasks)
    assert any(task.path == keep for task in tasks)


def test_discover_tasks_accepts_absolute_skip_paths(tmp_path):
    nested = tmp_path / "src" / "module" / "file.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("# TODO hidden\n", encoding="utf-8")

    keep = tmp_path / "src" / "keep.py"
    keep.write_text("# TODO keep\n", encoding="utf-8")

    tasks = discover_tasks(tmp_path, skip_dirs=[str(nested.parent)])
    assert all(task.path != nested for task in tasks)
    assert any(task.path == keep for task in tasks)


def test_discover_tasks_filters_extensions(tmp_path):
    py_task = tmp_path / "module.py"
    py_task.write_text("# TODO keep python\n", encoding="utf-8")

    txt_task = tmp_path / "notes.txt"
    txt_task.write_text("# TODO keep text\n", encoding="utf-8")

    only_py = discover_tasks(tmp_path, allowed_extensions=[".py"])
    assert {task.path for task in only_py} == {py_task}

    only_txt = discover_tasks(tmp_path, allowed_extensions=["TXT"])
    assert {task.path for task in only_txt} == {txt_task}


def test_discover_tasks_respects_ignore_patterns(tmp_path):
    ignored_dir = tmp_path / "build" / "generated" / "module.py"
    ignored_dir.parent.mkdir(parents=True)
    ignored_dir.write_text("# TODO hidden\n", encoding="utf-8")

    ignored_file = tmp_path / "module.generated.py"
    ignored_file.write_text("# TODO skip file\n", encoding="utf-8")

    included = tmp_path / "src" / "core.py"
    included.parent.mkdir()
    included.write_text("# TODO keep me\n", encoding="utf-8")

    tasks = discover_tasks(
        tmp_path,
        ignore_patterns=["build/**", "*.generated.py"],
    )

    assert all(task.path != ignored_dir for task in tasks)
    assert all(task.path != ignored_file for task in tasks)
    assert any(task.path == included for task in tasks)


def test_build_summary_payload_respects_hotspot_limit(tmp_path):
    files = []
    for idx in range(3):
        candidate = tmp_path / f"module_{idx}.py"
        candidate.write_text("# placeholder\n", encoding="utf-8")
        files.append(candidate)

    tasks = []
    for file_index, file_path in enumerate(files):
        for offset in range(file_index + 1):
            tasks.append(
                Task(
                    path=file_path,
                    line=offset + 1,
                    tag="TODO",
                    text=f"task {file_index}-{offset}",
                )
            )

    payload = build_summary_payload(tasks, tmp_path, hotspot_limit=2)
    assert len(payload["hotspots"]) == 2
    assert payload["hotspots"][0] == {"path": "module_2.py", "count": 3}
    assert payload["hotspots"][1] == {"path": "module_1.py", "count": 2}


def test_discover_tasks_requires_word_boundaries(tmp_path):
    """Ensure substrings like ``methodology`` do not register as TODOs."""

    sample = tmp_path / "notes.txt"
    sample.write_text(
        "# methodology and prefixfixmer should not trigger\n",
        encoding="utf-8",
    )

    assert discover_tasks(tmp_path) == []


def test_discover_tasks_trims_comment_text(tmp_path):
    doc = tmp_path / "doc.py"
    doc.write_text(
        '"""\nTODO calibrate signal\nadditional detail\n"""\n',
        encoding="utf-8",
    )

    inline = tmp_path / "inline.c"
    inline.write_text("/* TODO align portal */\n", encoding="utf-8")

    tasks = discover_tasks(tmp_path)
    texts = {task.text for task in tasks}

    assert texts == {"calibrate signal", "align portal"}


def test_build_summary_payload_includes_counts_and_paths(tmp_path):
    doc = tmp_path / "module.py"
    doc.write_text("# TODO keep\n# FIXME adjust\n", encoding="utf-8")

    tasks = discover_tasks(tmp_path)
    payload = build_summary_payload(tasks, tmp_path)

    assert payload["totals"]["overall"] == 2
    assert payload["totals"]["per_tag"] == {"FIXME": 1, "TODO": 1}
    assert payload["tasks"][0]["path"] == "module.py"
    assert payload["totals"]["per_extension"] == {".py": 2}


def test_build_summary_payload_tracks_missing_extensions(tmp_path):
    script = tmp_path / "script"
    script.write_text("# TODO add suffix\n", encoding="utf-8")

    payload = build_summary_payload(discover_tasks(tmp_path), tmp_path)
    assert payload["totals"]["per_extension"] == {"<no extension>": 1}


def test_build_summary_payload_includes_ranked_hotspots(tmp_path):
    for idx in range(6):
        path = tmp_path / f"module_{idx}.py"
        contents = "\n".join("# TODO entry" for _ in range(idx + 1)) + "\n"
        path.write_text(contents, encoding="utf-8")

    payload = build_summary_payload(discover_tasks(tmp_path), tmp_path)
    hotspots = payload["hotspots"]
    assert len(hotspots) == DEFAULT_HOTSPOT_LIMIT
    assert hotspots[0] == {"path": "module_5.py", "count": 6}


def test_build_summary_includes_file_type_table(tmp_path):
    py_task = tmp_path / "module.py"
    py_task.write_text("# TODO python\n", encoding="utf-8")

    txt_task = tmp_path / "notes.txt"
    txt_task.write_text("# TODO docs\n", encoding="utf-8")

    no_ext = tmp_path / "README"
    no_ext.write_text("# TODO plain\n", encoding="utf-8")

    roadmap = build_roadmap(discover_tasks(tmp_path), tmp_path)
    assert "### File Types" in roadmap
    assert "| .py | 1 |" in roadmap
    assert "| .txt | 1 |" in roadmap
    assert "| <no extension> | 1 |" in roadmap


def test_build_roadmap_includes_hotspot_table(tmp_path):
    busy = tmp_path / "core.py"
    busy.write_text("# TODO alpha\n# FIXME beta\n", encoding="utf-8")

    quiet = tmp_path / "helper.py"
    quiet.write_text("# TODO gamma\n", encoding="utf-8")

    roadmap = build_roadmap(discover_tasks(tmp_path), tmp_path)
    assert "### Hotspots" in roadmap
    hotspots_section = roadmap.split("### Hotspots", 1)[1]
    assert "| core.py | 2 |" in hotspots_section
    assert "| helper.py | 1 |" in hotspots_section
    assert hotspots_section.index("| core.py | 2 |") < hotspots_section.index("| helper.py | 1 |")


def test_update_roadmap_writes_json_summary(tmp_path):
    doc = tmp_path / "module.py"
    doc.write_text("# TODO keep\n", encoding="utf-8")

    roadmap = tmp_path / "ROADMAP.md"
    json_path = tmp_path / "summary.json"
    update_roadmap(tmp_path, roadmap, json_output_path=json_path)

    payload = json.loads(json_path.read_text())
    assert payload["tasks"]
    assert payload["tasks"][0]["tag"] == "TODO"
    assert payload["tasks"][0]["path"] == "module.py"


def test_main_enforces_max_tasks(tmp_path, monkeypatch):
    source = tmp_path / "module.py"
    source.write_text("# TODO keep\n", encoding="utf-8")

    roadmap = tmp_path / "ROADMAP.md"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["next_level", "--roadmap", str(roadmap), "--max-tasks", "0"],
    )

    assert main() == 1
    assert roadmap.exists()


def test_main_allows_tasks_with_generous_limit(tmp_path, monkeypatch):
    source = tmp_path / "module.py"
    source.write_text("# TODO keep\n", encoding="utf-8")

    roadmap = tmp_path / "ROADMAP.md"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["next_level", "--roadmap", str(roadmap), "--max-tasks", "5"],
    )

    assert main() == 0
