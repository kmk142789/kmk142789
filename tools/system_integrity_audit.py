"""System integrity audit utilities for Echo.

This module provides a command-line tool that computes cryptographic
fingerprints for key directories in the repository. The resulting manifest can
be saved for future comparison or compared to a previously saved manifest to
highlight changes. It is designed to help operators increase confidence in the
state of the repository and support autonomous integrity monitoring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping, MutableMapping, Set

DEFAULT_EXCLUDE_DIRS: Set[str] = {
    ".git",
    "node_modules",
    "out",
    "__pycache__",
}
DEFAULT_EXCLUDE_FILES: Set[str] = {"integrity_manifest.json"}


@dataclass(frozen=True)
class FileDigest:
    """A digest entry for a file on disk."""

    path: str
    sha256: str
    size: int

    def to_dict(self) -> Mapping[str, object]:
        return {"path": self.path, "sha256": self.sha256, "size": self.size}


def iter_files(root: Path, excludes: Set[str]) -> Iterable[Path]:
    """Yield files beneath ``root`` while honoring directory exclusions."""
    for path in root.rglob("*"):
        # Skip directories that should be excluded outright.
        if path.is_dir():
            if path.name in excludes:
                # ``rglob`` still explores directories even if we skip here, so
                # use ``continue`` and rely on the check before processing files.
                continue
            # Nothing to do for directories beyond making sure they are not
            # yielded.
            continue

        if path.name in DEFAULT_EXCLUDE_FILES:
            continue
        # Ensure the file resides in a directory that is not excluded.
        parents = {p.name for p in path.parents}
        if parents & excludes:
            continue
        if not path.is_file():
            continue
        yield path


def hash_file(path: Path) -> FileDigest:
    """Compute the SHA-256 digest and size of ``path``."""
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            if not chunk:
                break
            hasher.update(chunk)
            size += len(chunk)
    return FileDigest(path=str(path), sha256=hasher.hexdigest(), size=size)


def build_manifest(
    directories: Iterable[Path], excludes: Set[str]
) -> Dict[str, MutableMapping[str, object]]:
    """Build a manifest mapping relative paths to digest information."""
    manifest: Dict[str, MutableMapping[str, object]] = {}
    repo_root = Path.cwd()
    for directory in directories:
        abs_dir = (repo_root / directory).resolve()
        if not abs_dir.exists():
            continue
        for file_path in iter_files(abs_dir, excludes):
            digest = hash_file(file_path)
            relative = os.path.relpath(file_path, repo_root)
            manifest[relative] = dict(digest.to_dict())
    return manifest


def load_manifest(path: Path) -> Dict[str, Mapping[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, Mapping):
        raise ValueError("Manifest file is not a mapping")
    return {str(key): value for key, value in data.items()}


def compare_manifests(
    current: Mapping[str, Mapping[str, object]],
    baseline: Mapping[str, Mapping[str, object]],
) -> Dict[str, Set[str]]:
    """Return a summary of manifest differences."""
    current_keys = set(current)
    baseline_keys = set(baseline)
    added = current_keys - baseline_keys
    removed = baseline_keys - current_keys
    changed = {
        key
        for key in current_keys & baseline_keys
        if current[key]["sha256"] != baseline[key]["sha256"]
    }
    return {"added": added, "removed": removed, "changed": changed}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute file integrity digests for key Echo directories. "
            "Optionally compare the results to a saved manifest to detect "
            "unexpected changes."
        )
    )
    parser.add_argument(
        "directories",
        nargs="*",
        default=["code", "docs", "tools", "src"],
        help="Directories to audit (defaults to core Echo modules).",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Path to a previously saved manifest for comparison.",
    )
    parser.add_argument(
        "--save",
        type=Path,
        help="Save the computed manifest to the provided path.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional directory names to exclude from the audit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exclude_dirs = DEFAULT_EXCLUDE_DIRS | {Path(p).name for p in args.exclude}
    directories = [Path(d) for d in args.directories]
    manifest = build_manifest(directories, exclude_dirs)

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        with args.save.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
        print(f"Integrity manifest saved to {args.save}")

    if args.baseline:
        baseline = load_manifest(args.baseline)
        diff = compare_manifests(manifest, baseline)
        summary_parts = []
        status = 0
        for label in ("added", "removed", "changed"):
            items = sorted(diff[label])
            if items:
                summary_parts.append(f"{label}: {len(items)}")
                status = 1
        if summary_parts:
            print("Differences detected (" + ", ".join(summary_parts) + "):")
            for label in ("added", "removed", "changed"):
                items = sorted(diff[label])
                if items:
                    print(f"  {label}:")
                    for item in items:
                        print(f"    - {item}")
        else:
            print("No differences detected compared to baseline.")
        return status

    print(f"Audited {len(manifest)} files across {len(directories)} directories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
