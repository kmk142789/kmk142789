"""Scan the repository for TODOs and update the roadmap."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from memory import PersistentMemoryStore

BASE_DIR = Path(__file__).parent
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "out"}
EXCLUDE_PREFIXES = (Path("viewer/constellation_app/build"),)
SCAN_EXTENSIONS = {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".js", ".ts", ".cpp", ".hpp", ".c", ".h"}
PATTERN = re.compile(r"\b(TODO|FIXME|STUB|NotImplementedError)\b", re.IGNORECASE)
ROADMAP_PATH = BASE_DIR / "ROADMAP.md"


@dataclass
class Finding:
    path: Path
    line_number: int
    content: str

    def to_markdown(self) -> str:
        rel = self.path.relative_to(BASE_DIR)
        snippet = self.content.strip()
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        return f"- [ ] `{rel}:{self.line_number}` — {snippet}"


def iter_files(base: Path) -> Iterable[Path]:
    for path in base.rglob("*"):
        if path.is_dir():
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            rel_dir = path.relative_to(base)
            if any(rel_dir.parts[:len(prefix.parts)] == prefix.parts for prefix in EXCLUDE_PREFIXES):
                continue
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        rel_path = path.relative_to(base)
        if any(rel_path.parts[:len(prefix.parts)] == prefix.parts for prefix in EXCLUDE_PREFIXES):
            continue
        if path.suffix and path.suffix not in SCAN_EXTENSIONS:
            continue
        yield path


def scan_repo(base: Path) -> List[Finding]:
    findings: List[Finding] = []
    for file in iter_files(base):
        try:
            text = file.read_text(errors="ignore")
        except OSError:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            if PATTERN.search(line):
                findings.append(Finding(path=file, line_number=idx, content=line))
    return findings


def update_roadmap(findings: List[Finding]) -> None:
    ROADMAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not ROADMAP_PATH.exists():
        ROADMAP_PATH.write_text(
            "# Echo Evolution Roadmap\n\n"
            "This roadmap is updated by `next_level.py` to capture newly discovered build\n"
            "steps based on TODO, FIXME, and stub annotations within the repository.\n\n"
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"## Scan {timestamp}",
        "",
        f"Findings: {len(findings)}",
        "",
    ]
    if findings:
        for finding in findings:
            lines.append(finding.to_markdown())
    else:
        lines.append("- [x] Repository clear — no TODO/FIXME/STUB markers detected")
    lines.append("")

    with ROADMAP_PATH.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate roadmap updates from TODO markers")
    parser.parse_args()

    store = PersistentMemoryStore.load_default()
    with store.context("next_level.scan", {"base": str(BASE_DIR)}) as session:
        findings = scan_repo(BASE_DIR)
        session.log_command("scan_repo", {"findings": len(findings)})
        update_roadmap(findings)
        session.log_validation(
            "roadmap_update",
            True,
            {"entries": len(findings), "roadmap": str(ROADMAP_PATH)},
        )
        session.log_dataset(
            "roadmap", fingerprint=_fingerprint_path(ROADMAP_PATH), source=str(ROADMAP_PATH), size=ROADMAP_PATH.stat().st_size
        )
        session.set_summary({"roadmap_entries": len(findings)})
    return 0


def _fingerprint_path(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
