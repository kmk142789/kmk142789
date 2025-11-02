"""Generate the Echo Codex registry dataset from merged GitHub pull requests."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence
from urllib.parse import urljoin

import requests

OWNER = os.environ.get("OWNER", "kmk142789")
REPO = os.environ.get("REPO", "kmk142789")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
PER_PAGE = 100
DEFAULT_LIMIT = int(os.environ.get("CODEX_REGISTRY_LIMIT", "250"))

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = REPO_ROOT / "codex"
REGISTRY_JSON = REGISTRY_DIR / "registry.json"
REGISTRY_MARKDOWN = REGISTRY_DIR / "REGISTRY.md"
API_ROOT = "https://api.github.com/"


@dataclass(slots=True)
class PullRequest:
    number: int
    title: str
    summary: str
    labels: Sequence[str]
    url: str
    merged_at: str
    short_sha: str

    @classmethod
    def from_api(cls, payload: dict) -> "PullRequest":
        merged_at = payload.get("merged_at")
        if not merged_at:
            raise ValueError("pull request is not merged")
        merge_commit = payload.get("merge_commit_sha") or ""
        short_sha = merge_commit[:7] if merge_commit else ""
        labels = [label.get("name", "") for label in payload.get("labels", [])]
        normalised_labels = [label for label in labels if label]
        if "Merged" not in normalised_labels:
            normalised_labels.insert(0, "Merged")
        summary = _summarise_body(payload.get("body") or "")
        return cls(
            number=payload.get("number"),
            title=payload.get("title") or "(untitled)",
            summary=summary,
            labels=tuple(normalised_labels),
            url=payload.get("html_url") or "",
            merged_at=merged_at,
            short_sha=short_sha,
        )


def _summarise_body(body: str) -> str:
    cleaned = [line.strip() for line in body.splitlines() if line.strip()]
    if not cleaned:
        return "No summary provided."
    summary = cleaned[0]
    if len(summary) > 240:
        summary = summary[:237].rstrip() + "..."
    return summary


def _request(url: str, *, params: dict[str, object] | None = None) -> requests.Response:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "echo-codex-registry",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    response = requests.get(url, params=params, headers=headers, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"GitHub API returned {response.status_code}: {response.text}")
    return response


def _fetch_pull_requests(limit: int) -> List[PullRequest]:
    collected: List[PullRequest] = []
    page = 1
    while len(collected) < limit:
        response = _request(
            urljoin(API_ROOT, f"repos/{OWNER}/{REPO}/pulls"),
            params={
                "state": "closed",
                "per_page": PER_PAGE,
                "page": page,
                "sort": "updated",
                "direction": "desc",
            },
        )
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError("Unexpected GitHub API response")
        if not payload:
            break
        for item in payload:
            try:
                pr = PullRequest.from_api(item)
            except ValueError:
                continue
            collected.append(pr)
            if len(collected) >= limit:
                break
        page += 1
        if len(payload) < PER_PAGE:
            break
    collected.sort(key=lambda pr: pr.merged_at, reverse=True)
    return collected


def _serialise(prs: Iterable[PullRequest]) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat()
    items = [
        {
            "id": pr.number,
            "title": pr.title,
            "summary": pr.summary,
            "labels": list(pr.labels),
            "url": pr.url,
            "merged_at": pr.merged_at,
            "hash": pr.short_sha,
        }
        for pr in prs
    ]
    return {"version": 1, "generated_at": now, "items": items}


def _write_json(payload: dict[str, object]) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_markdown(payload: dict[str, object]) -> None:
    lines = ["# Echo Codex Registry", ""]
    generated = payload.get("generated_at") or datetime.now(timezone.utc).isoformat()
    lines.append(f"Generated at {generated}.")
    lines.append("")
    lines.append("| ID | Title | Summary | Labels | Merged | Commit |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for item in payload.get("items", []):
        labels = ", ".join(item.get("labels", []))
        commit = item.get("hash") or ""
        merged_at = item.get("merged_at") or ""
        url = item.get("url") or ""
        title = item.get("title") or "(untitled)"
        link = f"[{title}]({url})" if url else title
        summary = item.get("summary") or ""
        summary = summary.replace("\n", " ")
        lines.append(f"| {item.get('id')} | {link} | {summary} | {labels} | {merged_at} | {commit} |")
    REGISTRY_MARKDOWN.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(limit: int | None = None) -> int:
    limit = limit or DEFAULT_LIMIT
    prs = _fetch_pull_requests(limit)
    payload = _serialise(prs)
    _write_json(payload)
    _write_markdown(payload)
    print(f"Wrote {len(payload['items'])} entries to {REGISTRY_JSON.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Aborted", file=sys.stderr)
        raise SystemExit(1)
