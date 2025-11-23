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
    "RegistrySummary",
    "list_modules",
    "load_registry",
    "remove_module",
    "search_modules",
    "register_module",
    "store_registry",
    "summarize_registry",
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


@dataclass(frozen=True)
class RegistrySummary:
    """Aggregate metrics describing the current registry state."""

    total_modules: int
    categories: dict[str, int]
    last_updated: str | None


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


def list_modules(
    *,
    category: str | None = None,
    registry_path: Path | str = REGISTRY_FILE,
) -> List[ModuleRecord]:
    """Return modules stored in ``modules.json`` optionally filtered by category."""

    records = load_registry(registry_path)
    if category is not None:
        safe_category = _validate_input(category, field="category")
        records = [
            record
            for record in records
            if record.category.lower() == safe_category.lower()
        ]

    return sorted(records, key=lambda record: (record.category.lower(), record.name.lower()))


def search_modules(
    term: str,
    *,
    fields: Sequence[str] | None = None,
    registry_path: Path | str = REGISTRY_FILE,
) -> List[ModuleRecord]:
    """Return modules whose fields contain ``term`` (case-insensitive).

    The helper defaults to searching across ``name``, ``description``, and
    ``category`` fields.  Callers can restrict the search to a subset of fields
    via ``fields`` when building focused discovery experiences.
    """

    safe_term = _validate_input(term, field="term").lower()
    search_fields = [
        field.strip().lower()
        for field in (DEFAULT_SEARCH_FIELDS if fields is None else fields)
        if field and field.strip()
    ]
    invalid_fields = [field for field in search_fields if field not in DEFAULT_SEARCH_FIELDS]
    if invalid_fields:
        raise ValueError(
            "Unsupported search field(s): " + ", ".join(sorted(set(invalid_fields)))
        )

    def matches(record: ModuleRecord) -> bool:
        field_map = {
            "name": record.name,
            "description": record.description,
            "category": record.category,
        }
        return any(field_map[field].lower().find(safe_term) != -1 for field in search_fields)

    records = load_registry(registry_path)
    return sorted((record for record in records if matches(record)), key=lambda record: record.name.lower())


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


def remove_module(
    name: str, *, registry_path: Path | str = REGISTRY_FILE
) -> ModuleRecord | None:
    """Remove ``name`` from the registry.

    The function returns the removed :class:`ModuleRecord` when a matching entry
    is found or ``None`` when the registry does not contain ``name``.  The
    idempotent behaviour matches the ergonomics of small automation scripts that
    may prune entries multiple times without coordinating global state.
    """

    registry_path = Path(registry_path)
    target_name = _validate_input(name, field="name")

    records = load_registry(registry_path)
    kept: list[ModuleRecord] = []
    removed: ModuleRecord | None = None

    for record in records:
        if record.name == target_name:
            removed = record
            continue
        kept.append(record)

    if removed is None:
        return None

    store_registry(kept, registry_path)
    return removed


def summarize_registry(records: Sequence[ModuleRecord]) -> RegistrySummary:
    """Return aggregate details for ``records``.

    The summary is helpful for dashboards or CI steps that need to present the
    high-level status of a registry snapshot without re-implementing
    aggregation logic.
    """

    if not records:
        return RegistrySummary(total_modules=0, categories={}, last_updated=None)

    category_totals: dict[str, int] = {}
    last_updated: str | None = None

    for record in records:
        category_totals[record.category] = category_totals.get(record.category, 0) + 1
        if last_updated is None or record.timestamp > last_updated:
            last_updated = record.timestamp

    ordered_categories = dict(
        sorted(category_totals.items(), key=lambda item: item[0].lower())
    )

    return RegistrySummary(
        total_modules=len(records),
        categories=ordered_categories,
        last_updated=last_updated,
    )


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


DEFAULT_SEARCH_FIELDS = ("name", "description", "category")


if __name__ == "__main__":  # pragma: no cover - convenience CLI
    import argparse
    import sys

    SUBCOMMANDS = {"register", "list", "summary", "remove", "search"}

    argv = sys.argv
    if len(argv) > 1 and not argv[1].startswith("-") and argv[1] not in SUBCOMMANDS:
        argv.insert(1, "register")

    parser = argparse.ArgumentParser(description="Manage Echo module registries")
    parser.add_argument(
        "--registry",
        default=REGISTRY_FILE,
        type=Path,
        help="Path to the registry file (defaults to modules.json beside this script)",
    )

    subparsers = parser.add_subparsers(dest="command")

    register_parser = subparsers.add_parser(
        "register", help="Register or update a module entry"
    )
    register_parser.add_argument("name", help="Module name")
    register_parser.add_argument("description", help="Short module description")
    register_parser.add_argument("category", help="Module category tag")

    list_parser = subparsers.add_parser("list", help="List stored modules")
    list_parser.add_argument(
        "--category", help="Limit results to a single category", default=None
    )

    search_parser = subparsers.add_parser("search", help="Search modules by term")
    search_parser.add_argument("term", help="Search term to match")
    search_parser.add_argument(
        "--fields",
        nargs="+",
        choices=DEFAULT_SEARCH_FIELDS,
        help="Fields to search (default: all)",
    )

    subparsers.add_parser("summary", help="Show registry summary information")

    remove_parser = subparsers.add_parser("remove", help="Remove a module entry")
    remove_parser.add_argument("name", help="Module name")

    args = parser.parse_args()

    if args.command is None:
        parser.error(
            "No command provided. Use 'register', 'list', 'search', 'summary', or 'remove'."
        )

    if args.command == "register":
        record = register_module(
            args.name,
            args.description,
            args.category,
            registry_path=args.registry,
        )
        print(json.dumps(asdict(record), indent=2))
    elif args.command == "list":
        records = list_modules(category=args.category, registry_path=args.registry)
        print(json.dumps([asdict(record) for record in records], indent=2))
    elif args.command == "search":
        records = search_modules(
            args.term, fields=args.fields, registry_path=args.registry
        )
        print(json.dumps([asdict(record) for record in records], indent=2))
    elif args.command == "summary":
        summary = summarize_registry(load_registry(args.registry))
        print(json.dumps(asdict(summary), indent=2))
    elif args.command == "remove":
        removed = remove_module(args.name, registry_path=args.registry)
        print(json.dumps(asdict(removed) if removed else None, indent=2))
