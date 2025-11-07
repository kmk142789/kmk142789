"""Utilities for registering Echo modules in a local JSON manifest.

The historical implementation of this helper lived as a loose script that
performed unchecked reads and writes against ``modules.json``.  That approach
was fragile – the file handle remained open, corrupted JSON would crash the
process without a clear error, and partially written data could leave the
registry unusable.  The helpers below harden the workflow while keeping the
light‑weight ergonomics expected by small tooling scripts.

Key features
============
* **Safe I/O** – the registry is always written atomically using a temporary
  file and :func:`os.replace`, eliminating partially written files.
* **Input validation** – consumer code receives a :class:`ValueError` when
  required fields are missing instead of creating malformed entries.
* **Graceful recovery** – corrupted registries raise a dedicated
  :class:`ModuleRegistryError` with actionable context.

The module is intentionally dependency free so that it can be imported from the
existing scripts in ``tools/`` and ``packages/`` without requiring extra
installation steps.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Iterator, List, Sequence

__all__ = [
    "REGISTRY_FILE",
    "ModuleRecord",
    "ModuleRegistryError",
    "load_registry",
    "register_module",
    "store_registry",
]


REGISTRY_FILE = Path(__file__).with_name("modules.json")


class ModuleRegistryError(RuntimeError):
    """Raised when the registry on disk cannot be parsed."""


@dataclass(frozen=True)
class ModuleRecord:
    """In-memory representation of a single registry entry."""

    name: str
    description: str
    category: str
    timestamp: str
    hash: str

    @classmethod
    def create(cls, *, name: str, description: str, category: str) -> "ModuleRecord":
        """Return a record populated with derived metadata.

        The hash mirrors the behaviour of the original script to preserve
        compatibility for downstream tooling that may validate entries.
        """

        safe_name = _validate_input(name, field="name")
        safe_description = _validate_input(description, field="description")
        safe_category = _validate_input(category, field="category")

        timestamp = datetime.now(timezone.utc).isoformat()
        digest = hashlib.sha256(f"{safe_name}{safe_description}".encode("utf-8")).hexdigest()
        return cls(
            name=safe_name,
            description=safe_description,
            category=safe_category,
            timestamp=timestamp,
            hash=digest,
        )


def load_registry(path: Path | str = REGISTRY_FILE) -> List[ModuleRecord]:
    """Return all records stored in ``modules.json``.

    ``ModuleRegistryError`` is raised when the file exists but cannot be parsed
    as a list of registry entries.
    """

    registry_path = Path(path)
    if not registry_path.exists():
        return []

    try:
        with registry_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive branch
        raise ModuleRegistryError(
            f"Registry file '{registry_path}' is not valid JSON"
        ) from exc

    if not isinstance(payload, list):
        raise ModuleRegistryError(
            f"Registry file '{registry_path}' is expected to contain a JSON list"
        )

    records: List[ModuleRecord] = []
    for entry in payload:
        if not isinstance(entry, dict):
            raise ModuleRegistryError(
                f"Registry file '{registry_path}' contains a non-object entry"
            )

        try:
            record = ModuleRecord(
                name=_validate_input(entry["name"], field="name"),
                description=_validate_input(entry["description"], field="description"),
                category=_validate_input(entry["category"], field="category"),
                timestamp=_validate_input(entry["timestamp"], field="timestamp"),
                hash=_validate_input(entry["hash"], field="hash"),
            )
        except KeyError as exc:  # pragma: no cover - defensive branch
            missing = exc.args[0]
            raise ModuleRegistryError(
                f"Registry entry in '{registry_path}' is missing required key '{missing}'"
            ) from exc

        records.append(record)

    return records


def store_registry(records: Sequence[ModuleRecord], path: Path | str = REGISTRY_FILE) -> None:
    """Persist the provided records to disk using an atomic write."""

    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    payload: list[dict[str, str]] = [asdict(record) for record in records]

    with NamedTemporaryFile("w", delete=False, dir=str(registry_path.parent), encoding="utf-8") as tmp:
        json.dump(payload, tmp, indent=2)
        tmp_path = Path(tmp.name)

    tmp_path.replace(registry_path)


def register_module(
    name: str,
    description: str,
    category: str,
    *,
    registry_path: Path | str = REGISTRY_FILE,
) -> ModuleRecord:
    """Register a module and persist it to ``modules.json``.

    Existing modules with the same name are updated rather than duplicated so
    callers can safely re-run registration scripts.
    """

    registry_path = Path(registry_path)
    records = load_registry(registry_path)

    new_record = ModuleRecord.create(name=name, description=description, category=category)

    filtered = [record for record in records if record.name != new_record.name]
    filtered.append(new_record)
    filtered.sort(key=lambda record: record.name.lower())

    store_registry(filtered, registry_path)
    return new_record


def _validate_input(value: str, *, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Registry field '{field}' must be a string")

    stripped = value.strip()
    if not stripped:
        raise ValueError(f"Registry field '{field}' must not be empty")
    return stripped


def _iter_records(sequence: Iterable[ModuleRecord]) -> Iterator[ModuleRecord]:
    """Yield records from ``sequence``.  Exists for discoverability and testing."""

    yield from sequence


if __name__ == "__main__":  # pragma: no cover - convenience CLI
    import argparse

    parser = argparse.ArgumentParser(description="Register an Echo module")
    parser.add_argument("name", help="Module name")
    parser.add_argument("description", help="Short module description")
    parser.add_argument("category", help="Module category tag")
    parser.add_argument(
        "--registry",
        default=REGISTRY_FILE,
        type=Path,
        help="Path to the registry file (defaults to modules.json beside this script)",
    )

    args = parser.parse_args()
    record = register_module(
        args.name,
        args.description,
        args.category,
        registry_path=args.registry,
    )
    print(json.dumps(asdict(record), indent=2))
