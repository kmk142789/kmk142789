#!/usr/bin/env python3
"""Generate release notes grouped by track labels and milestones."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Dict, List

import requests

REPO = os.environ.get("GITHUB_REPOSITORY")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

TRACKS = [
    "track:glyph-cloud",
    "track:continuum",
    "track:memory-store",
    "track:federated-pulse",
    "track:opencode",
    "track:wallets",
]


def gh(path: str, params: Dict[str, object] | None = None) -> List[dict]:
    url = f"https://api.github.com/{path}"
    headers = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    response = requests.get(url, headers=headers, params=params or {})
    response.raise_for_status()
    return response.json()


def main(tag: str) -> None:
    if not REPO:
        sys.exit("Set GITHUB_REPOSITORY")

    tags = gh(f"repos/{REPO}/tags")
    tag_names = [t["name"] for t in tags]
    if tag not in tag_names:
        print(
            f"Note: tag {tag} not found in remote list; proceeding with merged PRs in last 30 days.",
            file=sys.stderr,
        )

    prs = gh(f"repos/{REPO}/pulls", {"state": "closed", "per_page": 100})
    merged = [p for p in prs if p.get("merged_at")]

    groups: Dict[str, List[dict]] = {track: [] for track in TRACKS}
    groups.setdefault("other", [])

    for pr in merged:
        labels = [label["name"] for label in pr.get("labels", [])]
        for track in TRACKS:
            if track in labels:
                groups[track].append(pr)
                break
        else:
            groups["other"].append(pr)

    print(f"# Release Notes — {tag}")
    print(f"_Generated: {datetime.utcnow().isoformat()}Z_")

    for track in TRACKS + ["other"]:
        entries = groups.get(track) or []
        if not entries:
            continue
        print(f"\n## {track}")
        for pr in entries:
            print(f"- {pr['title']} (#{pr['number']}) — @{pr['user']['login']}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: release_notes.py vX.Y.Z")
    main(sys.argv[1])
