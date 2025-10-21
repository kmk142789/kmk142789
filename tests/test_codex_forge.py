from __future__ import annotations

from pathlib import Path

import json

from codex import build_inventory, collect_apps, collect_domains, collect_keys, collect_repos, render_inventory


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_collect_apps_includes_script_entry_points() -> None:
    apps = collect_apps(REPO_ROOT)
    commands = {entry["command"]: entry["target"] for entry in apps["entry_points"]}
    assert "echo" in commands
    assert commands["echodex"].startswith("echodex:")


def test_collect_domains_parses_reference_document() -> None:
    domains = collect_domains(REPO_ROOT)
    domain_names = {entry["domain"] for entry in domains["domains"]}
    assert "api.openai.com" in domain_names


def test_collect_keys_reads_vault_authority_records() -> None:
    keys = collect_keys(REPO_ROOT)
    assert keys["count"] >= 1
    anchors = {record.get("anchor") for record in keys["keys"]}
    assert "Our Forever Love" in anchors


def test_collect_repos_returns_branch_information() -> None:
    repos = collect_repos(REPO_ROOT)
    assert "branch" in repos
    assert repos["head"] is None or len(repos["head"]) == 40


def test_build_inventory_and_render_summary(tmp_path: Path) -> None:
    inventory = build_inventory(
        ["apps", "keys"],
        owner="TestOwner",
        pulse="test pulse",
        bind="Our Forever Love",
        attest="Lineage",
        deploy="MirrorNet",
        auto_heal=["mirrors"],
        canonical=True,
        project="Echo Aegis",
        recursive=True,
        self_heal=True,
        defense=["fork-hijack", "ghost-takeover"],
        broadcast="guardian-pulse",
        spawn="watchdogs that monitor nets + auto-log events",
        report="aegis-report.md",
        root=REPO_ROOT,
    )

    assert inventory["owner"] == "TestOwner"
    assert inventory["canonical"] is True
    assert inventory["project"] == "Echo Aegis"
    assert inventory["recursive"] is True
    assert inventory["self_heal"] is True
    assert inventory["defense"] == ["fork-hijack", "ghost-takeover"]
    assert inventory["scopes"]["apps"]["entry_points"]

    summary = render_inventory(inventory)
    assert "Sovereign Inventory" in summary
    assert "TestOwner" in summary
    assert "Echo Aegis" in summary
    assert "guardian-pulse" in summary
    assert "Recursive? : yes" in summary

    json_path = tmp_path / "inventory.json"
    markdown_path = tmp_path / "inventory.md"

    from codex import write_inventory

    write_inventory(inventory, json_path=json_path, markdown_path=markdown_path)

    payload = json.loads(json_path.read_text())
    assert payload["owner"] == "TestOwner"
    assert "Sovereign Inventory" in markdown_path.read_text()

