from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.echo_constellation.scan import build_graph


def init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "echo@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Echo Tester"], cwd=root, check=True)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_collects_commits_prs_and_next_step(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    init_repo(repo_root)

    write_file(repo_root / "README.md", "# Echo Overview\n\nDetails about the Echo project.\n")
    write_file(repo_root / "echo_alpha" / "agent.py", """\n__all__ = ['ignite']\n\n
def ignite():\n    return 'spark'\n""")

    subprocess.run(["git", "add", "README.md", "echo_alpha/agent.py"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "chore: bootstrap repo"], cwd=repo_root, check=True)

    write_file(repo_root / "docs" / "guide.md", "## Echo Protocol\nMore words.\n")
    write_file(repo_root / "echo_alpha" / "agent.py", """\n__all__ = ['ignite']\n\n
def ignite():\n    return 'spark v2'\n""")
    subprocess.run(["git", "add", "docs/guide.md", "echo_alpha/agent.py"], cwd=repo_root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: improve ignition (#12)"],
        cwd=repo_root,
        check=True,
    )

    graph = build_graph([repo_root])

    node_ids = {node["id"] for node in graph["nodes"]}
    edge_pairs = {(edge["source"], edge["target"]) for edge in graph["edges"]}

    assert any(node.startswith("repo:") for node in node_ids)
    assert any(node.startswith("commit:") for node in node_ids)
    assert "pr:#12" in node_ids
    assert any(node.startswith("mod:echo_alpha") for node in node_ids)
    assert any(node.startswith("artifact:docs/guide.md") for node in node_ids)
    assert any(edge[0].startswith("commit:") and edge[1].startswith("artifact:") for edge in edge_pairs)
    assert isinstance(graph["meta"]["next_step"], str)
    assert graph["meta"]["next_step"].startswith("Next step:")

    data = json.loads(json.dumps(graph))
    assert data["meta"]["generated_at"]
