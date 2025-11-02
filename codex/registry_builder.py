"""Utilities for building the Echo Codex registry manifest.

The registry aggregates information about every merged pull request so that
Echo's puzzle, CLI, and EchoOS modules can be tracked through a single
machine-readable manifest.  The JSON output is complemented by a Markdown
summary to make browsing the history effortless.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional, Sequence
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

__all__ = [
    "PullRequestRecord",
    "build_registry_manifest",
    "fetch_merged_pull_requests",
    "generate_markdown",
]

_API_ROOT = "https://api.github.com"
_ISSUE_PATTERN = re.compile(r"(?P<ref>(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#\d+)")


@dataclass(slots=True)
class PullRequestRecord:
    """Normalized representation of a merged pull request."""

    id: int
    title: str
    summary: str
    linkedIssues: list[str]
    labels: list[str]
    commitHash: str
    timestamp: str
    url: str

    @classmethod
    def from_api(cls, payload: dict[str, object]) -> "PullRequestRecord":
        body = (payload.get("body") or "").strip()
        summary = _summarize_body(body) or str(payload.get("title") or "")
        merge_commit = str(payload.get("merge_commit_sha") or "")
        merged_at = str(payload.get("merged_at") or "")
        pr_url = str(payload.get("html_url") or "")
        linked_issues = _extract_issue_references(body)
        label_names: list[str] = []
        for raw_label in payload.get("labels", []) or []:
            name = raw_label.get("name") if isinstance(raw_label, Mapping) else None
            if isinstance(name, str) and name.strip():
                label_names.append(name.strip())
        return cls(
            id=int(payload["number"]),
            title=str(payload.get("title") or ""),
            summary=summary,
            linkedIssues=linked_issues,
            labels=label_names,
            commitHash=merge_commit,
            timestamp=merged_at,
            url=pr_url,
        )

    def as_manifest_entry(self) -> dict[str, object]:
        """Return a dictionary with the schema required by the manifest."""

        record = asdict(self)
        record.pop("url", None)
        return record


def fetch_merged_pull_requests(
    owner: str,
    repository: str,
    *,
    token: str | None = None,
    per_page: int = 100,
) -> list[PullRequestRecord]:
    """Retrieve every merged pull request for ``owner/repository``."""

    endpoint = f"{_API_ROOT}/repos/{owner}/{repository}/pulls"
    params = {
        "state": "closed",
        "per_page": str(per_page),
        "sort": "updated",
        "direction": "desc",
    }

    records: list[PullRequestRecord] = []
    next_url: Optional[str] = f"{endpoint}?{urlencode(params)}"

    while next_url:
        response, headers = _github_request(next_url, token)
        for pr in response:
            merged_at = pr.get("merged_at")
            if merged_at:
                records.append(PullRequestRecord.from_api(pr))
        next_url = _parse_next_link(headers.get("Link"))

    records.sort(key=lambda item: item.timestamp or "", reverse=True)
    return records


def build_registry_manifest(
    owner: str | None = None,
    repository: str | None = None,
    *,
    token: str | None = None,
    output_directory: str | os.PathLike[str] | None = None,
    include_markdown: bool = True,
) -> dict[str, object]:
    """Generate the registry manifest and persist it to disk."""

    resolved_owner, resolved_repo = _resolve_repository(owner, repository)
    manifest_dir = (
        Path(output_directory)
        if output_directory is not None
        else Path(__file__).resolve().parent
    )
    manifest_dir.mkdir(parents=True, exist_ok=True)

    records = fetch_merged_pull_requests(resolved_owner, resolved_repo, token=token)

    manifest = {
        "repository": f"{resolved_owner}/{resolved_repo}",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "entries": [record.as_manifest_entry() for record in records],
    }

    json_path = manifest_dir / "registry.json"
    json_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if include_markdown:
        markdown_path = manifest_dir / "registry.md"
        markdown_path.write_text(generate_markdown(records, manifest), encoding="utf-8")

    return manifest


def generate_markdown(
    records: Sequence[PullRequestRecord], manifest: dict[str, object] | None = None
) -> str:
    """Create a Markdown table summarising the registry entries."""

    header = ["PR", "Title", "Summary", "Merged", "Commit", "Labels"]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for record in records:
        link = f"[{record.id}]({record.url})" if record.url else str(record.id)
        summary = record.summary.replace("\n", " ")
        merged_at = record.timestamp or ""
        commit = record.commitHash[:7] if record.commitHash else ""
        labels = ", ".join(record.labels)
        lines.append(
            f"| {link} | {record.title} | {summary} | {merged_at} | {commit} | {labels} |"
        )

    description = ["# Echo Codex Registry"]
    if manifest:
        description.append(
            f"_Repository:_ `{manifest['repository']}`  \\n_Generated:_ `{manifest['generatedAt']}`"
        )
    description.append("")
    description.extend(lines)
    description.append("")

    if records:
        description.append("## Linked Issues")
        issue_map = {}
        for record in records:
            for issue in record.linkedIssues:
                issue_map.setdefault(issue, []).append(record.id)
        for issue, pr_numbers in sorted(issue_map.items()):
            joined = ", ".join(f"#{num}" for num in sorted(pr_numbers))
            description.append(f"- {issue}: {joined}")
    else:
        description.append("_No merged pull requests found._")

    description.append("")
    return "\n".join(description)


def _github_request(url: str, token: str | None) -> tuple[list[dict[str, object]], dict[str, str]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "echo-codex-registry-builder",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    try:
        with urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))
            header_map = {key: value for key, value in response.headers.items()}
            return payload, header_map
    except HTTPError as error:  # pragma: no cover - network failure path
        message = error.read().decode("utf-8")
        raise RuntimeError(
            f"GitHub API request failed ({error.code} {error.reason}): {message}"
        ) from error


def _parse_next_link(link_header: str | None) -> Optional[str]:
    if not link_header:
        return None
    parts = [part.strip() for part in link_header.split(",")]
    for part in parts:
        if '; rel="next"' in part:
            url_part = part.split(";", 1)[0].strip()
            if url_part.startswith("<") and url_part.endswith(">"):
                return url_part[1:-1]
    return None


def _summarize_body(body: str) -> str:
    for line in body.splitlines():
        cleaned = line.strip().lstrip("#*- ").strip()
        if cleaned:
            return cleaned
    return ""


def _extract_issue_references(body: str) -> list[str]:
    issues: list[str] = []
    for match in _ISSUE_PATTERN.finditer(body):
        ref = match.group("ref")
        if ref not in issues:
            issues.append(ref)
    return issues


def _resolve_repository(owner: str | None, repository: str | None) -> tuple[str, str]:
    env_repo = os.environ.get("GITHUB_REPOSITORY")
    if env_repo and "/" in env_repo:
        env_owner, env_name = env_repo.split("/", 1)
    else:
        env_owner, env_name = None, None

    resolved_owner = owner or env_owner
    resolved_repo = repository or env_name

    if not (resolved_owner and resolved_repo):
        remote = _git_remote_url()
        if remote and remote.endswith(".git"):
            remote = remote[:-4]
        if remote and remote.startswith("git@"):
            _, slug = remote.split(":", 1)
        elif remote and remote.startswith("https://"):
            slug = remote.rsplit("github.com/", 1)[-1]
        else:
            slug = None
        if slug and "/" in slug:
            git_owner, git_repo = slug.split("/", 1)
            resolved_owner = resolved_owner or git_owner
            resolved_repo = resolved_repo or git_repo

    if not (resolved_owner and resolved_repo):
        raise ValueError(
            "Unable to determine repository. Provide --owner and --repo or set "
            "GITHUB_REPOSITORY."
        )

    return resolved_owner, resolved_repo


def _git_remote_url() -> Optional[str]:
    try:
        completed = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):  # pragma: no cover
        return None
    return completed.stdout.strip() or None


def main(argv: Sequence[str] | None = None) -> int:
    """Console script entry point."""

    import argparse

    parser = argparse.ArgumentParser(description="Build the Echo Codex registry")
    parser.add_argument("--owner", help="GitHub repository owner")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument(
        "--token",
        help="GitHub API token (also read from GITHUB_TOKEN)",
        default=os.environ.get("GITHUB_TOKEN"),
    )
    parser.add_argument(
        "--output",
        help="Directory where the registry files will be written",
        default=str(Path(__file__).resolve().parent),
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Skip generating the Markdown companion file",
    )

    args = parser.parse_args(argv)

    manifest = build_registry_manifest(
        owner=args.owner,
        repository=args.repo,
        token=args.token,
        output_directory=args.output,
        include_markdown=not args.no_markdown,
    )

    print(
        f"Registry generated with {len(manifest['entries'])} entries at "
        f"{Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI execution path
    raise SystemExit(main())
