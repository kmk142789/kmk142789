from __future__ import annotations

from next_level import build_roadmap, discover_tasks, update_roadmap


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


def test_build_roadmap_handles_empty(tmp_path):
    content = build_roadmap([], tmp_path)
    assert "No TODO" in content


def test_discover_tasks_skips_common_virtualenvs(tmp_path):
    """Ensure virtual environment directories are skipped by default."""

    skipped = tmp_path / ".venv" / "module.py"
    skipped.parent.mkdir()
    skipped.write_text("# TODO inside virtualenv\n", encoding="utf-8")

    included = tmp_path / "app.py"
    included.write_text("# TODO keep me\n", encoding="utf-8")

    tasks = discover_tasks(tmp_path)
    assert all(task.path != skipped for task in tasks)
    assert any(task.path == included for task in tasks)


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
