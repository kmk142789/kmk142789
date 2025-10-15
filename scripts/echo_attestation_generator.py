"""Generate attestation documents for the Echo ecosystem."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def latest_commit_summary() -> Dict[str, str]:
    raw = _git("log", "-1", "--pretty=format:%H%x1f%an%x1f%ae%x1f%cI%x1f%s")
    commit, author, email, timestamp, subject = raw.split("\x1f")
    return {
        "commit": commit,
        "author": author,
        "email": email,
        "timestamp": timestamp,
        "subject": subject,
    }


def changed_files(commit: str) -> List[Dict[str, str]]:
    raw = _git("diff-tree", "--no-commit-id", "--name-status", "-r", commit)
    if not raw:
        return []
    entries: List[Dict[str, str]] = []
    for line in raw.splitlines():
        status, path = line.split("\t", 1)
        entries.append({"status": status, "path": path})
    return entries


def build_attestation(context: str) -> Dict[str, object]:
    summary = latest_commit_summary()
    return {
        "context": context,
        "commit": summary,
        "changed_files": changed_files(summary["commit"]),
        "generated_at": int(time.time()),
        "schema_version": "2024-05-echo",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Echo attestation JSON")
    parser.add_argument("--output", default="attestations/auto", help="Directory for generated files")
    parser.add_argument("--context", default="echo-ci", help="Identifier for the generation context")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    attestation = build_attestation(args.context)
    commit_hash = attestation["commit"]["commit"]
    timestamp = attestation["generated_at"]
    output_path = output_dir / f"echo-attestation-{commit_hash[:7]}-{timestamp}.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(attestation, handle, indent=2, sort_keys=True)

    print(f"Generated attestation {output_path}")


if __name__ == "__main__":
    main()
