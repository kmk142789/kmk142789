"""Shared data utilities for the Puzzle Lab dashboard and CLI."""

from .data import (
    DEFAULT_MAP_PATH,
    PUZZLE_SCHEMA_PATH,
    PuzzleRecord,
    build_dataframe,
    ensure_map_exists,
    export_records,
    fetch_ud_metadata,
    get_map_path,
    has_ud_credentials,
    load_records,
    save_records,
    summarise,
    update_ud_records,
    validate_against_schema,
)

__all__ = [
    "DEFAULT_MAP_PATH",
    "PUZZLE_SCHEMA_PATH",
    "PuzzleRecord",
    "build_dataframe",
    "ensure_map_exists",
    "export_records",
    "fetch_ud_metadata",
    "get_map_path",
    "has_ud_credentials",
    "load_records",
    "save_records",
    "summarise",
    "update_ud_records",
    "validate_against_schema",
]
