"""Auto-maintained manifest system for Echo artifacts."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Mapping, MutableSequence, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "echo_manifest.json"


EXCLUDED_DIRS = {
    ".git",
    ".github",
    "__pycache__",
    "node_modules",
    "out",
    ".mypy_cache",
    ".pytest_cache",
}


class ManifestError(RuntimeError):
    """Base error for manifest operations."""


class ManifestDriftError(ManifestError):
    """Raised when manifest verification detects drift."""

    def __init__(self, mismatches: Sequence[str]) -> None:
        self.mismatches = list(mismatches)
        message = "Manifest drift detected: " + "; ".join(self.mismatches)
        super().__init__(message)


@dataclass(frozen=True)
class ArtifactRecord:
    """Represents a single tracked artifact."""

    path: PurePosixPath
    category: str
    digest: str
    size: int
    last_modified: str
    version: str
    owners: Sequence[str]
    tags: Sequence[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path.as_posix(),
            "digest": {"sha256": self.digest},
            "size": self.size,
            "last_modified": self.last_modified,
            "version": self.version,
            "owners": list(self.owners),
            "tags": list(self.tags),
        }


def load_codeowners(root: Path) -> Sequence[tuple[str, Sequence[str]]]:
    """Parse the CODEOWNERS file under ``.github`` (if present)."""

    codeowners_path = root / ".github" / "CODEOWNERS"
    if not codeowners_path.exists():
        return []

    rules: MutableSequence[tuple[str, Sequence[str]]] = []
    for line in codeowners_path.read_text(encoding="utf8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        segments = stripped.split()
        if len(segments) < 2:
            continue
        pattern = segments[0]
        owners = segments[1:]
        rules.append((pattern, owners))
    return list(rules)


def _codeowners_for(path: PurePosixPath, rules: Sequence[tuple[str, Sequence[str]]]) -> List[str]:
    owners: List[str] = []
    path_str = path.as_posix()
    for pattern, rule_owners in rules:
        normalised = pattern.lstrip("/")
        if fnmatch.fnmatch(path_str, normalised):
            owners = list(rule_owners)
        elif pattern.startswith("/") and fnmatch.fnmatch(path_str, pattern[1:]):
            owners = list(rule_owners)
    return owners


def _classify(relative: PurePosixPath) -> Optional[str]:
    if not relative.parts:
        return None

    top = relative.parts[0]
    suffix = relative.suffix.lower()

    if top == "docs" and suffix == ".md":
        return "docs"

    if suffix == ".md" and top not in ("docs", "tests", "node_modules"):
        return "docs"

    if top == "echo" and suffix == ".py":
        return "engines"

    if suffix == ".py":
        if relative.name.startswith("echo_"):
            return "clis"
        if relative.name in {"echodex.py", "echoshell.py"}:
            return "clis"
        if top == "scripts":
            return "clis"

    if suffix in {".json", ".jsonl", ".yaml", ".yml"}:
        if relative.name in {"pulse.json", "pulse_history.json"}:
            return "states"
        if top in {"memory", "state", "attestation", "attestations", "genesis_ledger", "federated_pulse"}:
            return "states"
        if top == "docs" and len(relative.parts) > 1 and relative.parts[1] == "data":
            return "datasets"
        if top in {"manifest", "modules", "function_schemas", "proofs", "verifier", "datasets"}:
            return "datasets"

    if top == "docs" and suffix in {".json", ".csv"}:
        return "datasets"

    return None


def _calculate_digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 128), b""):
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def _git_version(root: Path, relative: PurePosixPath) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--pretty=format:%h", "--", relative.as_posix()],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return "unknown"
    value = completed.stdout.strip()
    return value or "unknown"


def _last_modified(path: Path) -> str:
    ts = path.stat().st_mtime
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.isoformat()


def _build_tags(relative: PurePosixPath, category: str) -> List[str]:
    tags = {f"category:{category}"}
    suffix = relative.suffix.lower()
    if suffix:
        tags.add(f"ext:{suffix[1:]}")
    else:
        tags.add("ext:none")

    if len(relative.parts) > 1:
        tags.add(f"top:{relative.parts[0]}")
    else:
        tags.add("top:root")

    if suffix == ".py":
        tags.add("lang:python")
    elif suffix == ".md":
        tags.add("format:markdown")
    elif suffix in {".json", ".jsonl"}:
        tags.add("format:json")
    elif suffix in {".yaml", ".yml"}:
        tags.add("format:yaml")
    elif suffix == ".csv":
        tags.add("format:csv")

    return sorted(tags)


def _iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name
            for name in dirnames
            if name not in EXCLUDED_DIRS and not name.startswith(".")
        ]
        for filename in filenames:
            yield Path(dirpath) / filename


def scan_artifacts(root: Path, *, rules: Optional[Sequence[tuple[str, Sequence[str]]]] = None) -> List[ArtifactRecord]:
    rules = list(rules or load_codeowners(root))
    records: List[ArtifactRecord] = []

    for file_path in _iter_files(root):
        if file_path.is_symlink():
            continue
        try:
            relative = file_path.relative_to(root)
        except ValueError:
            continue
        relative_posix = PurePosixPath(relative.as_posix())
        category = _classify(relative_posix)
        if not category:
            continue

        digest = _calculate_digest(file_path)
        size = file_path.stat().st_size
        modified = _last_modified(file_path)
        version = _git_version(root, relative_posix)
        owners = _codeowners_for(relative_posix, rules)
        tags = _build_tags(relative_posix, category)

        records.append(
            ArtifactRecord(
                path=relative_posix,
                category=category,
                digest=digest,
                size=size,
                last_modified=modified,
                version=version,
                owners=owners,
                tags=tags,
            )
        )

    records.sort(key=lambda record: (record.category, record.path.as_posix()))
    return records


def build_document(
    records: Sequence[ArtifactRecord],
    *,
    generated_at: Optional[str] = None,
) -> Dict[str, object]:
    categories: Dict[str, List[Dict[str, object]]] = {}
    for record in records:
        categories.setdefault(record.category, []).append(record.to_dict())

    for entries in categories.values():
        entries.sort(key=lambda entry: entry["path"])

    document: Dict[str, object] = {
        "schema_version": "1.0",
        "generated_at": generated_at or datetime.now(tz=timezone.utc).isoformat(),
        "artifact_total": len(records),
        "categories": dict(sorted(categories.items())),
    }
    return document


def write_manifest(
    document: Mapping[str, object],
    *,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> None:
    serialized = json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True)
    manifest_path.write_text(serialized + "\n", encoding="utf8")


def refresh_manifest(
    *,
    root: Path = REPO_ROOT,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    generated_at: Optional[str] = None,
) -> Dict[str, object]:
    records = scan_artifacts(root)
    document = build_document(records, generated_at=generated_at)
    write_manifest(document, manifest_path=manifest_path)
    return document


def load_manifest(manifest_path: Path = DEFAULT_MANIFEST_PATH) -> Dict[str, object]:
    if not manifest_path.exists():
        raise ManifestError(f"Manifest file not found: {manifest_path}")
    try:
        return json.loads(manifest_path.read_text(encoding="utf8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Unable to decode manifest: {exc}") from exc


def flatten_manifest(document: Mapping[str, object]) -> List[Dict[str, object]]:
    categories = document.get("categories", {})
    flattened: List[Dict[str, object]] = []
    if isinstance(categories, Mapping):
        for category, entries in sorted(categories.items()):
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, Mapping):
                    flattened.append({"category": category, **dict(entry)})
    return flattened


def verify_manifest(
    *,
    root: Path = REPO_ROOT,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    append_summary: bool = True,
) -> None:
    document = load_manifest(manifest_path)
    records = flatten_manifest(document)
    mismatches: List[str] = []

    for entry in records:
        path_value = entry.get("path")
        digest_info = entry.get("digest", {})
        expected_digest = None
        if isinstance(digest_info, Mapping):
            expected_digest = digest_info.get("sha256")
        if not isinstance(path_value, str) or not isinstance(expected_digest, str):
            mismatches.append("invalid entry metadata")
            continue
        file_path = root / Path(path_value)
        if not file_path.exists():
            mismatches.append(f"missing:{path_value}")
            continue
        actual_digest = _calculate_digest(file_path)
        if actual_digest != expected_digest:
            mismatches.append(f"digest:{path_value}")

    summary_line = (
        "✅ Manifest verification passed" if not mismatches else "❌ Manifest verification failed"
    )
    if append_summary:
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            try:
                with open(summary_path, "a", encoding="utf8") as handle:
                    handle.write(summary_line + "\n")
            except OSError:
                pass

    if mismatches:
        raise ManifestDriftError(mismatches)


def show_manifest(*, manifest_path: Path = DEFAULT_MANIFEST_PATH) -> str:
    document = load_manifest(manifest_path)
    records = flatten_manifest(document)
    if not records:
        return "No artifacts recorded.\n"

    headers = ("Category", "Path", "Size", "Owners", "Version")
    rows: List[tuple[str, str, str, str, str]] = []
    for entry in records:
        category = str(entry.get("category", ""))
        path = str(entry.get("path", ""))
        size_value = entry.get("size")
        size = f"{size_value}" if isinstance(size_value, int) else "?"
        owners_list = entry.get("owners", [])
        if isinstance(owners_list, list):
            owners = ", ".join(str(owner) for owner in owners_list)
        else:
            owners = ""
        version = str(entry.get("version", ""))
        rows.append((category, path, size, owners, version))

    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    lines = []
    header_line = " ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    lines.append(header_line)
    lines.append(" ".join("-" * width for width in widths))
    for row in rows:
        lines.append(" ".join(value.ljust(widths[idx]) for idx, value in enumerate(row)))

    lines.append("")
    lines.append(json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True))
    lines.append("")
    output = "\n".join(lines)
    return output


__all__ = [
    "ArtifactRecord",
    "ManifestDriftError",
    "ManifestError",
    "build_document",
    "flatten_manifest",
    "load_manifest",
    "refresh_manifest",
    "scan_artifacts",
    "show_manifest",
    "verify_manifest",
]

