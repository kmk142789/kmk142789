"""Retention policy enforcement for dev artifacts."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "config" / "retention.json"


class RetentionPolicy:
    def __init__(self, name: str, paths: List[Path], retention_days: int, patterns: List[str]) -> None:
        self.name = name
        self.paths = paths
        self.retention_days = retention_days
        self.patterns = patterns or ["*"]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "RetentionPolicy":
        name = str(payload.get("name", "unnamed"))
        retention_days = int(payload.get("retention_days", 0))
        path_values = [Path(str(value)) for value in payload.get("paths", [])]
        pattern_values = [str(value) for value in payload.get("patterns", ["*"])]
        return cls(name, path_values, retention_days, pattern_values)


def load_policies(config_path: Path) -> List[RetentionPolicy]:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return [RetentionPolicy.from_dict(item) for item in data.get("policies", [])]


def enforce_policy(policy: RetentionPolicy, *, dry_run: bool) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=policy.retention_days)
    for relative in policy.paths:
        base = (REPO_ROOT / relative).resolve()
        if not base.exists():
            continue
        for pattern in policy.patterns:
            for candidate in base.rglob(pattern):
                if not candidate.is_file():
                    continue
                if candidate.name.startswith(".git"):
                    continue
                modified = datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc)
                if modified >= cutoff:
                    continue
                if dry_run:
                    print(f"[DRY-RUN] {policy.name}: would remove {candidate.relative_to(REPO_ROOT)}")
                else:
                    candidate.unlink(missing_ok=True)
                    print(f"Removed ({policy.name}): {candidate.relative_to(REPO_ROOT)}")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Purge files according to retention policies")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to retention config JSON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without deleting files",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    policies = load_policies(args.config)
    for policy in policies:
        enforce_policy(policy, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
