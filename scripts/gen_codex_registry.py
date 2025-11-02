#!/usr/bin/env python3
"""Generate the Echo Codex registry feed in JSON and Markdown formats."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from codex.registry_builder import PullRequestRecord, fetch_merged_pull_requests

REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_DIR = REPO_ROOT / "codex"
JSON_PATH = CODEX_DIR / "registry.json"
MARKDOWN_PATH = CODEX_DIR / "REGISTRY.md"


def _env(name: str, *, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"environment variable {name} is required")
    return value


def _normalise_labels(labels: Sequence[str]) -> list[str]:
    unique: dict[str, None] = {}
    for label in labels:
        cleaned = label.strip()
        if cleaned:
            unique[cleaned] = None
    if "Merged" not in unique:
        unique["Merged"] = None
    return list(unique.keys())


def _render_markdown(items: Sequence[dict[str, object]], generated_at: str, repository: str) -> str:
    header = [
        "# Echo Codex Registry",
        "",
        f"_Repository:_ `{repository}`  \n_Generated:_ `{generated_at}`",
        "",
        "| PR | Title | Summary | Labels | Merged | Commit |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    body: list[str] = []
    for item in items:
        labels = ", ".join(item.get("labels", []))
        merged_at = item.get("merged_at", "")
        commit = item.get("hash", "")
        body.append(
            "| "
            f"[{item['id']}]({item['url']})"
            " | "
            f"{item['title']}"
            " | "
            f"{str(item.get('summary', '')).replace('\n', ' ')}"
            " | "
            f"{labels}"
            " | "
            f"{merged_at}"
            " | "
            f"{commit}"
            " |"
        )

    if not body:
        body.append("| – | – | No merged pull requests found. | – | – | – |")

    timeline: list[str] = ["", "## Timeline"]
    for item in items:
        merged_at = item.get("merged_at") or ""
        timeline.append(
            f"- **{merged_at}** – [{item['title']}]({item['url']}) `{item['hash']}` ({', '.join(item.get('labels', []))})"
        )

    return "\n".join(header + body + timeline) + "\n"


def _build_items(records: Iterable[PullRequestRecord]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for record in records:
        item = {
            "id": record.id,
            "title": record.title,
            "summary": record.summary,
            "labels": _normalise_labels(record.labels),
            "url": record.url,
            "merged_at": record.timestamp,
            "hash": (record.commitHash or "")[:7],
        }
        items.append(item)
    return items


def main() -> None:
    owner = _env("OWNER")
    repo = _env("REPO")
    token = os.getenv("GITHUB_TOKEN")

    CODEX_DIR.mkdir(parents=True, exist_ok=True)

    records = fetch_merged_pull_requests(owner, repo, token=token)
    generated_at = datetime.now(timezone.utc).isoformat()
    items = _build_items(records)

    json_payload = {
        "version": 1,
        "repository": f"{owner}/{repo}",
        "generated_at": generated_at,
        "items": items,
        # Legacy keys for compatibility with existing tools until they migrate.
        "generatedAt": generated_at,
        "entries": [record.as_manifest_entry() for record in records],
    }

    JSON_PATH.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    MARKDOWN_PATH.write_text(
        _render_markdown(items, generated_at, json_payload["repository"]),
        encoding="utf-8",
    )

    print(f"Generated {len(items)} codex entries at {generated_at}")


if __name__ == "__main__":
    main()
