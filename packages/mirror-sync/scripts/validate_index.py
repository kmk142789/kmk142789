#!/usr/bin/env python3
"""Validate mirror.index.json without mutating repository state."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = PACKAGE_ROOT / "mirror.index.json"
CONTENT_DIR = PACKAGE_ROOT / "content"
ARTIFACT_DIR = PACKAGE_ROOT / "artifacts"

REQUIRED_FIELDS = {"slug", "title", "canonical_url", "txid", "last_synced"}


def main() -> int:
    if not INDEX_PATH.exists():
        print(f"::error ::Missing {INDEX_PATH}")
        return 1

    try:
        payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"::error ::mirror.index.json is not valid JSON: {exc}")
        return 1

    if not isinstance(payload, list):
        print("::error ::mirror.index.json must contain a list")
        return 1

    status = 0
    seen_slugs: set[str] = set()
    for entry in payload:
        if not isinstance(entry, dict):
            print("::error ::Each mirror entry must be an object")
            status = 1
            continue
        missing = REQUIRED_FIELDS - entry.keys()
        if missing:
            print(f"::error ::Entry missing required fields: {sorted(missing)}")
            status = 1
        slug = entry.get("slug")
        if not slug:
            print("::error ::Entry missing slug")
            status = 1
            continue
        if slug in seen_slugs:
            print(f"::error ::Duplicate slug detected: {slug}")
            status = 1
        seen_slugs.add(slug)
        content_path = CONTENT_DIR / f"{slug}.md"
        artifact_path = ARTIFACT_DIR / f"{slug}.html"
        if not content_path.exists():
            print(f"::error ::Missing Markdown snapshot for {slug}")
            status = 1
        if not artifact_path.exists():
            print(f"::warning ::Missing HTML artifact for {slug}")
    if status == 0:
        print("Mirror index validation complete.")
    return status


if __name__ == "__main__":
    sys.exit(main())
