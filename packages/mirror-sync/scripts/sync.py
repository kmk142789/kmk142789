#!/usr/bin/env python3
"""Snapshot Mirror.xyz posts into the monorepo.

The sync process keeps a canonical copy of the published HTML and emits a
lightweight Markdown rendering for quick diffing.  Network access is optional:
when a fetch fails, the script preserves the previous snapshot and writes a
stub that records the failure so the CI pipeline can flag it later.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = PACKAGE_ROOT / "content"
ARTIFACT_DIR = PACKAGE_ROOT / "artifacts"
INDEX_PATH = PACKAGE_ROOT / "mirror.index.json"


class _TextExtractor(HTMLParser):
    """Best-effort HTML → text converter using only the standard library."""

    def __init__(self) -> None:
        super().__init__()
        self._fragments: list[str] = []

    def handle_data(self, data: str) -> None:  # pragma: no cover - HTMLParser callback
        if data and data.strip():
            self._fragments.append(data.strip())

    def get_text(self) -> str:
        output: list[str] = []
        last_blank = True
        for fragment in self._fragments:
            if fragment:
                output.append(fragment)
                last_blank = False
            elif not last_blank:
                output.append("")
                last_blank = True
        return "\n\n".join(output)


def _read_index() -> list[dict]:
    if not INDEX_PATH.exists():
        raise SystemExit(f"mirror index missing: {INDEX_PATH}")
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise SystemExit("mirror.index.json must contain a list")
    return payload


def _write_if_changed(path: Path, data: str, mode: str = "text") -> bool:
    if mode not in {"text", "binary"}:
        raise ValueError("mode must be 'text' or 'binary'")
    if mode == "binary":
        new_bytes = data.encode("utf-8")
        current = path.read_bytes() if path.exists() else None
        if current == new_bytes:
            return False
        path.write_bytes(new_bytes)
        return True
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == data:
        return False
    path.write_text(data, encoding="utf-8")
    return True


def _fetch(url: str) -> str | None:
    try:
        with urlopen(url, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, "ignore")
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"::warning ::Unable to fetch {url}: {exc}")
    except Exception as exc:  # pragma: no cover - defensive safeguard
        print(f"::warning ::Unexpected error fetching {url}: {exc}")
    return None


def _render_markdown(entry: dict, text: str, html_sha: str, synced_at: str) -> str:
    header = [
        "---",
        f"title: {entry.get('title', entry['slug'])}",
        f"canonical_url: {entry.get('canonical_url', '')}",
        f"arweave_txid: {entry.get('txid', '')}",
        f"synced_at: {synced_at}",
        f"html_sha256: {html_sha}",
        "---",
        "",
    ]
    body = text or "_No textual content extracted; see HTML artifact for details._"
    return "\n".join(header + [body, ""])


def _hash_text(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _ensure_dirs(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def snapshot(entry: dict) -> bool:
    slug = entry.get("slug")
    if not slug:
        raise SystemExit("mirror entry missing 'slug'")
    canonical_url = entry.get("canonical_url")
    synced_at_now = datetime.now(tz=timezone.utc).isoformat()
    previous_synced_at = entry.get("last_synced")
    synced_at = previous_synced_at or synced_at_now

    html_data = _fetch(canonical_url) if canonical_url else None
    artifact_path = ARTIFACT_DIR / f"{slug}.html"
    text = ""
    html_sha = ""
    changed = False
    html_changed = False

    if html_data:
        html_sha = _hash_text(html_data)
        html_changed = _write_if_changed(artifact_path, html_data)
        parser = _TextExtractor()
        parser.feed(html_data)
        text = parser.get_text()
    else:
        failure_note = f"Sync skipped for {slug}: unable to download canonical content."
        if not artifact_path.exists():
            artifact_path.write_text(failure_note + "\n", encoding="utf-8")
            html_changed = True
        text = failure_note

    markdown_path = CONTENT_DIR / f"{slug}.md"
    markdown_payload = _render_markdown(entry, text, html_sha, synced_at)
    markdown_changed = _write_if_changed(markdown_path, markdown_payload)

    changed = html_changed or markdown_changed
    if changed and synced_at != synced_at_now:
        synced_at = synced_at_now
        markdown_payload = _render_markdown(entry, text, html_sha, synced_at)
        markdown_changed = _write_if_changed(markdown_path, markdown_payload)
    if changed:
        entry["last_synced"] = synced_at
    elif previous_synced_at:
        entry["last_synced"] = previous_synced_at
    return changed


def main() -> int:
    _ensure_dirs([CONTENT_DIR, ARTIFACT_DIR])
    index = _read_index()

    any_changes = False
    for entry in index:
        if snapshot(entry):
            any_changes = True

    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    if any_changes:
        print("Mirror sync completed with updates.")
    else:
        print("Mirror sync completed; no changes detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
