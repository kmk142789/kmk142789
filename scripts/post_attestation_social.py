#!/usr/bin/env python3
"""Emit a social notification for the freshest attestation node."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def _load_latest(path: Path) -> dict | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    nodes = payload.get("nodes") or []
    if not nodes:
        return None
    def sort_key(entry: dict) -> tuple[int, str, int]:
        created = entry.get("created_at") or ""
        return (
            int(entry.get("cycle", 0)),
            created,
            int(entry.get("puzzle", 0)),
        )

    return max(nodes, key=sort_key)


def _format_status(entry: dict, *, base_url: str) -> str:
    puzzle = entry.get("puzzle")
    cycle = entry.get("cycle")
    address = entry.get("address")
    digest = (entry.get("metadata") or {}).get("hash_sha256")
    status = entry.get("status", "attested").title()
    commit = (entry.get("links") or {}).get("commit")
    history = (entry.get("links") or {}).get("history")
    line = f"Puzzle #{puzzle} cycle {cycle}: {status} @ {address} (hash {digest})"
    if commit:
        line += f" {base_url.rstrip('/')}/{commit.lstrip('./')}"
    elif history:
        line += f" {base_url.rstrip('/')}/{history.lstrip('./')}"
    return line[:500]


def _post_status(base_url: str, token: str, status: str) -> None:
    endpoint = base_url.rstrip("/") + "/api/v1/statuses"
    data = urllib.parse.urlencode({"status": status}).encode("utf-8")
    request = urllib.request.Request(endpoint, data=data)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    urllib.request.urlopen(request, timeout=15)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Post attestation status to social feed")
    parser.add_argument("--index", default="federated_attestation_index.json")
    parser.add_argument("--base-url", default="https://github.com/kmk142789/kmk142789")
    args = parser.parse_args(argv)

    index_path = Path(args.index)
    if not index_path.exists():
        print(f"No index found at {index_path}")
        return 0

    latest = _load_latest(index_path)
    if not latest:
        print("No attestation nodes to broadcast")
        return 0

    mastodon_token = os.getenv("MASTODON_ACCESS_TOKEN")
    mastodon_base = os.getenv("MASTODON_BASE_URL", "https://mastodon.social")

    status_text = _format_status(latest, base_url=args.base_url)
    print(f"Prepared status: {status_text}")

    if not mastodon_token:
        print("MASTODON_ACCESS_TOKEN not set; skipping network broadcast.")
        return 0

    try:
        _post_status(mastodon_base, mastodon_token, status_text)
        print("Broadcast dispatched to Mastodon")
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"Broadcast failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
