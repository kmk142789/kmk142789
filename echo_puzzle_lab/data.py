"""Data access helpers shared between the Puzzle Lab CLI and dashboard."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd
from jsonschema import Draft7Validator
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP_PATH = REPO_ROOT / "echo_map.json"
PUZZLE_SCHEMA_PATH = REPO_ROOT / "schemas" / "echo_schema_v1.json"
CACHE_DIR = REPO_ROOT / ".cache" / "ud"
EXPORT_ROOT = REPO_ROOT / "exports"


class PkScript(BaseModel):
    """Representation of the locking script text and hex encodings."""

    asm: str = Field(description="Assembly form of the script")
    hex: str = Field(description="Hexadecimal encoding of the script")

    model_config = {"extra": "allow"}


class UDMetadata(BaseModel):
    """Metadata returned from Unstoppable Domains enrichment."""

    domains: list[str] = Field(default_factory=list)
    owner: str | None = None
    records: dict[str, str] = Field(default_factory=dict)
    status: str | None = None
    message: str | None = None

    model_config = {"extra": "allow"}

    @property
    def bound(self) -> bool:
        return bool(self.domains or self.owner)


class Lineage(BaseModel):
    """Source provenance for a puzzle entry."""

    source_files: list[str] = Field(default_factory=list)
    commit: str | None = None
    pr: str | None = None

    model_config = {"extra": "allow"}


class PuzzleRecord(BaseModel):
    """Validated representation of a puzzle entry from ``echo_map.json``."""

    puzzle: int
    address: str
    address_family: str
    hash160: str
    pkscript: PkScript
    ud: UDMetadata = Field(default_factory=UDMetadata)
    lineage: Lineage = Field(default_factory=Lineage)
    tested: bool = False
    updated_at: datetime

    model_config = {"extra": "allow"}

    @property
    def ud_domain_count(self) -> int:
        return len(self.ud.domains)

    @property
    def lineage_pr(self) -> str:
        return self.lineage.pr or "(untracked)"


def get_map_path() -> Path:
    """Return the effective path to ``echo_map.json`` (env overrides allowed)."""

    override = os.getenv("ECHO_MAP_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_MAP_PATH


def ensure_map_exists(force: bool = False) -> Path:
    """Ensure ``echo_map.json`` exists, optionally rebuilding it using orchestrator."""

    path = get_map_path()
    if path.exists() and not force:
        return path

    if path != DEFAULT_MAP_PATH:
        if force:
            raise RuntimeError(
                "Cannot refresh echo_map.json for a custom ECHO_MAP_PATH override."
            )
        raise FileNotFoundError(
            f"Puzzle map not found at {path}. Set ECHO_MAP_PATH or run refresh first."
        )

    from scripts.echo_orchestrator import orchestrate

    orchestrate()
    if not path.exists():
        raise RuntimeError("Failed to build echo_map.json using orchestrator")
    return path


def load_records(validate: bool = True) -> list[PuzzleRecord]:
    """Load puzzle entries from ``echo_map.json`` as validated models."""

    path = ensure_map_exists()
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError("echo_map.json should contain a list of entries")

    records: list[PuzzleRecord] = []
    for raw in data:
        if not validate:
            record = PuzzleRecord.model_construct(**raw)  # type: ignore[arg-type]
        else:
            record = PuzzleRecord.model_validate(raw)
        records.append(record)
    return records


def save_records(records: Sequence[PuzzleRecord], path: Path | None = None) -> None:
    """Persist the provided records back to ``echo_map.json`` preserving extras."""

    target = path or get_map_path()
    payload = [record.model_dump(mode="json", round_trip=True) for record in records]
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def validate_against_schema(records: Sequence[PuzzleRecord]) -> list[str]:
    """Validate entries against the JSON schema, returning human-readable errors."""

    with PUZZLE_SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)

    validator = Draft7Validator(schema)
    errors = []
    for record in records:
        for error in validator.iter_errors(record.model_dump(mode="json", round_trip=True)):
            errors.append(f"Puzzle {record.puzzle}: {error.message}")
    return errors


def _derive_address(record: PuzzleRecord) -> str | None:
    """Recompute the address from the stored pkScript to detect mismatches."""

    try:
        from scripts.echo_orchestrator import derive_address, parse_script
    except ImportError:  # pragma: no cover - defensive
        return None

    script = record.pkscript.asm
    try:
        script_type, derived_hash = parse_script(script)
    except ValueError:
        script_type = record.address_family.lower()
        derived_hash = record.hash160

    try:
        return derive_address(script_type, derived_hash)
    except ValueError:
        return None


def build_dataframe(records: Sequence[PuzzleRecord]) -> pd.DataFrame:
    """Transform the records into a :class:`~pandas.DataFrame` with helper columns."""

    rows: list[dict[str, object]] = []
    for record in records:
        derived_address = _derive_address(record)
        mismatch = bool(derived_address and derived_address != record.address)
        rows.append(
            {
                "Puzzle": record.puzzle,
                "Address": record.address,
                "Family": record.address_family,
                "Hash160": record.hash160,
                "Hash160_8": record.hash160[:8],
                "Updated": record.updated_at,
                "UD_Domains": record.ud.domains,
                "UD_Count": record.ud_domain_count,
                "UD_Bound": record.ud.bound,
                "Lineage_PR": record.lineage_pr,
                "Lineage_Source": record.lineage.source_files,
                "Tested": record.tested,
                "Mismatch": mismatch,
                "Derived": derived_address,
            }
        )

    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["Updated"] = pd.to_datetime(frame["Updated"], utc=True, errors="coerce")
    return frame


def summarise(records: Sequence[PuzzleRecord]) -> dict[str, object]:
    """Produce quick metrics for CLI/statistics reporting."""

    df = build_dataframe(records)
    if df.empty:
        return {
            "total_puzzles": 0,
            "families": {},
            "ud_bound": {"bound": 0, "unbound": 0},
            "mismatches": 0,
        }

    fam_counts = Counter(df["Family"]).most_common()
    bound = int(df["UD_Bound"].sum())
    total = int(len(df))
    return {
        "total_puzzles": total,
        "families": dict(fam_counts),
        "ud_bound": {"bound": bound, "unbound": total - bound},
        "mismatches": int(df["Mismatch"].sum()),
    }


def export_records(records: Sequence[PuzzleRecord], destination: Path) -> Path:
    """Export the provided records to ``destination`` in JSON Lines format."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for record in records:
            json.dump(record.model_dump(mode="json", round_trip=True), handle)
            handle.write("\n")
    return destination


def has_ud_credentials() -> bool:
    """Return ``True`` when UD credentials are present in the environment."""

    return bool(
        os.getenv("UD_API_KEY")
        or os.getenv("UD_JWT")
        or os.getenv("UNSTOPPABLE_API_KEY")
    )


def _ud_cache_path(address: str) -> Path:
    safe = address.replace(":", "_")
    return CACHE_DIR / f"{safe}.json"


def fetch_ud_metadata(addresses: Iterable[str], refresh: bool = False) -> dict[str, UDMetadata]:
    """Fetch UD metadata for the provided addresses with basic caching."""

    if not has_ud_credentials():
        return {}

    from scripts.echo_orchestrator import resolve_domains

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    api_key = (
        os.getenv("UD_API_KEY")
        or os.getenv("UD_JWT")
        or os.getenv("UNSTOPPABLE_API_KEY")
    )

    results: dict[str, UDMetadata] = {}
    for address in addresses:
        cache_path = _ud_cache_path(address)
        if cache_path.exists() and not refresh:
            with cache_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            results[address] = UDMetadata.model_validate(payload)
            continue

        resolution = resolve_domains(address, api_key)
        metadata = UDMetadata(
            domains=resolution.resolved_domains,
            owner=resolution.resolved_domain,
            records=resolution.multi_chain,
            status=resolution.status,
            message=resolution.message,
        )
        with cache_path.open("w", encoding="utf-8") as handle:
            json.dump(metadata.model_dump(mode="json", round_trip=True), handle)
        results[address] = metadata
    return results


def update_ud_records(
    records: Sequence[PuzzleRecord], metadata: dict[str, UDMetadata]
) -> list[PuzzleRecord]:
    """Return a new list of records with UD information patched in."""

    updated: list[PuzzleRecord] = []
    now = datetime.now(tz=timezone.utc)
    for record in records:
        meta = metadata.get(record.address)
        if not meta:
            updated.append(record)
            continue

        data = record.model_dump(mode="json", round_trip=True)
        data["ud"] = {
            **data.get("ud", {}),
            "domains": meta.domains,
            "owner": meta.owner,
            "records": meta.records,
            "status": meta.status,
            **({"message": meta.message} if meta.message else {}),
        }
        data["updated_at"] = now.isoformat()
        updated.append(PuzzleRecord.model_validate(data))
    return updated
