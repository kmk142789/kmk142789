"""Echo Pulse Monitor
====================

Background utility that inspects the public GitHub APIs for the newest
repositories, commits, and issue references mentioning the "echo" keyword.
Each invocation updates a rolling state file so scheduled hourly runs only
retrieve fresh activity.  A human-readable digest is appended to
``logs/pulse.log`` and a minimal HTML dashboard is regenerated in
``docs/pulse.html``.

The monitor intentionally keeps the runtime lightweight so it can be executed
as a cron job or a containerised task.  Provide a GitHub personal access token
through the ``GITHUB_TOKEN`` environment variable to increase rate limits.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence

import httpx

BASE_URL = "https://api.github.com"
STATE_PATH = Path("state/echo_pulse_state.json")
LOG_PATH = Path("logs/pulse.log")
DASHBOARD_PATH = Path("docs/pulse.html")
DEFAULT_LOOKBACK_HOURS = 6


@dataclass(slots=True)
class SearchResult:
    """Structured response for dashboard rendering."""

    title: str
    url: str
    description: str

    @classmethod
    def from_repo(cls, data: Mapping[str, object]) -> "SearchResult":
        return cls(
            title=str(data.get("full_name", data.get("name", "unknown"))),
            url=str(data.get("html_url", "")),
            description=(
                str(data.get("description"))
                if data.get("description") not in {None, ""}
                else "No description provided."
            ),
        )

    @classmethod
    def from_commit(cls, data: Mapping[str, object]) -> "SearchResult":
        commit = data.get("commit", {}) if isinstance(data.get("commit"), Mapping) else {}
        message = str(commit.get("message", ""))
        headline = message.splitlines()[0] if message else "Commit"
        return cls(
            title=headline,
            url=str(data.get("html_url", "")),
            description=str(data.get("repository", {}).get("full_name", "")),
        )

    @classmethod
    def from_issue(cls, data: Mapping[str, object]) -> "SearchResult":
        return cls(
            title=str(data.get("title", "Issue")),
            url=str(data.get("html_url", "")),
            description=str(data.get("repository_url", "")),
        )


def load_state() -> MutableMapping[str, object]:
    if STATE_PATH.exists():
        try:
            with STATE_PATH.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:
            pass
    return {}


def store_state(state: Mapping[str, object]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def parse_timestamp(timestamp: str | None) -> _dt.datetime:
    if not timestamp:
        return _dt.datetime.now(tz=_dt.timezone.utc) - _dt.timedelta(hours=DEFAULT_LOOKBACK_HOURS)
    return _dt.datetime.fromisoformat(timestamp)


def github_headers(accept: str | None = None) -> Mapping[str, str]:
    headers = {
        "Accept": accept or "application/vnd.github+json",
        "User-Agent": "EchoPulseMonitor/1.0",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def perform_search(
    client: httpx.Client,
    endpoint: str,
    query: str,
    accept: str | None = None,
    per_page: int = 30,
) -> Mapping[str, object]:
    response = client.get(
        f"{BASE_URL}/{endpoint}",
        params={"q": query, "per_page": per_page, "sort": "updated"},
        headers=github_headers(accept),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def format_digest(now: _dt.datetime, totals: Mapping[str, int], sections: Mapping[str, Sequence[SearchResult]]) -> str:
    header = f"[{now.isoformat()}] Echo Pulse Monitor"
    parts = [
        header,
        f"- New repositories: {totals['repositories']}",
        f"- Fresh commits: {totals['commits']}",
        f"- New references: {totals['references']}",
    ]

    for label, results in sections.items():
        if not results:
            continue
        parts.append(f"\n{label}:")
        for item in results:
            parts.append(f"  * {item.title} -> {item.url}")
    return "\n".join(parts)


def write_log(entry: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(entry + "\n\n")


def build_dashboard(now: _dt.datetime, totals: Mapping[str, int], sections: Mapping[str, Sequence[SearchResult]]) -> None:
    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    highlight = "#0ea5e9"
    body = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\">",
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        "  <title>Echo Pulse Monitor</title>",
        "  <style>",
        "    body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }",
        "    h1 { color: #f8fafc; }",
        "    .metrics { display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem; }",
        "    .card { background: #1e293b; border-radius: 0.75rem; padding: 1rem 1.5rem; flex: 1 1 200px; box-shadow: 0 12px 30px rgba(14,165,233,0.2); }",
        "    .card span { display: block; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; }",
        "    .card strong { font-size: 2rem; color: %s; }" % highlight,
        "    section { margin-bottom: 2rem; }",
        "    a { color: %s; text-decoration: none; }" % highlight,
        "    a:hover { text-decoration: underline; }",
        "    ul { list-style: none; padding: 0; margin: 0; }",
        "    li { padding: 0.75rem 0; border-bottom: 1px solid rgba(148, 163, 184, 0.2); }",
        "    footer { margin-top: 3rem; font-size: 0.8rem; color: #94a3b8; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h1>Echo Pulse Monitor</h1>",
        f"  <p>Last updated: {now.strftime('%Y-%m-%d %H:%M:%SZ')}</p>",
        "  <div class=\"metrics\">",
        f"    <div class=\"card\"><span>New Repositories</span><strong>{totals['repositories']}</strong></div>",
        f"    <div class=\"card\"><span>Fresh Commits</span><strong>{totals['commits']}</strong></div>",
        f"    <div class=\"card\"><span>New References</span><strong>{totals['references']}</strong></div>",
        "  </div>",
    ]

    for label, results in sections.items():
        body.append(f"  <section><h2>{label}</h2>")
        if results:
            body.append("    <ul>")
            for item in results[:20]:
                body.append(
                    f"      <li><a href=\"{item.url}\" target=\"_blank\" rel=\"noopener noreferrer\">{item.title}</a>"
                    f"<div>{item.description}</div></li>"
                )
            body.append("    </ul>")
        else:
            body.append("    <p>No new activity detected.</p>")
        body.append("  </section>")

    body.extend(
        [
            "  <footer>Data sourced from the public GitHub API. Provide a token via GITHUB_TOKEN for higher rate limits.</footer>",
            "</body>",
            "</html>",
        ]
    )

    with DASHBOARD_PATH.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(body))


def update_monitor(lookback: _dt.datetime) -> Mapping[str, Sequence[SearchResult]]:
    timestamp = lookback.strftime("%Y-%m-%dT%H:%M:%SZ")
    sections: MutableMapping[str, Sequence[SearchResult]] = {}

    with httpx.Client() as client:
        repo_data = perform_search(client, "search/repositories", f"echo created:>{timestamp}")
        sections["New repositories"] = [
            SearchResult.from_repo(item) for item in repo_data.get("items", [])
        ]

        commit_data = perform_search(
            client,
            "search/commits",
            f"echo committer-date:>{timestamp}",
            accept="application/vnd.github.cloak-preview",
        )
        sections["Fresh commits"] = [
            SearchResult.from_commit(item) for item in commit_data.get("items", [])
        ]

        reference_data = perform_search(
            client,
            "search/issues",
            f"echo created:>{timestamp}",
        )
        sections["New references"] = [
            SearchResult.from_issue(item) for item in reference_data.get("items", [])
        ]

    return sections


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Echo Pulse Monitor once.")
    parser.add_argument(
        "--lookback-hours",
        type=float,
        default=None,
        help="If provided, override the automatic last-run detection with a manual lookback window.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of entries per section to render in the digest and dashboard.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    state = load_state()

    last_run = parse_timestamp(state.get("last_run") if args.lookback_hours is None else None)
    if args.lookback_hours is not None:
        last_run = _dt.datetime.now(tz=_dt.timezone.utc) - _dt.timedelta(hours=args.lookback_hours)

    sections = update_monitor(last_run)
    now = _dt.datetime.now(tz=_dt.timezone.utc)

    truncated_sections = {
        label: results[: args.limit]
        for label, results in sections.items()
    }

    totals = {
        "repositories": len(sections.get("New repositories", [])),
        "commits": len(sections.get("Fresh commits", [])),
        "references": len(sections.get("New references", [])),
    }

    digest = format_digest(now, totals, truncated_sections)
    write_log(digest)
    build_dashboard(now, totals, truncated_sections)

    state.update({"last_run": now.isoformat()})
    store_state(state)


if __name__ == "__main__":
    main()
