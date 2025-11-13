from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo_module_registry import (
    ModuleRecord,
    ModuleRegistryError,
    RegistrySummary,
    list_modules,
    load_registry,
    register_module,
    store_registry,
    summarize_registry,
)


def read_registry(path: Path) -> list[dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_register_module_creates_registry(tmp_path: Path) -> None:
    registry_path = tmp_path / "modules.json"

    record = register_module(
        "quantum_governance_engine",
        "Implements probabilistic decision models for multi-agent consensus.",
        "governance",
        registry_path=registry_path,
    )

    assert record.name == "quantum_governance_engine"
    assert registry_path.exists()

    payload = read_registry(registry_path)
    assert len(payload) == 1
    stored = payload[0]
    assert stored["name"] == record.name
    assert stored["description"] == record.description
    assert stored["category"] == record.category
    assert stored["hash"] == record.hash


def test_register_module_overwrites_existing_entry(tmp_path: Path) -> None:
    registry_path = tmp_path / "modules.json"

    first = register_module(
        "quantum_governance_engine",
        "Initial description",
        "governance",
        registry_path=registry_path,
    )

    updated = register_module(
        "quantum_governance_engine",
        "Refined description",
        "governance",
        registry_path=registry_path,
    )

    assert updated.name == first.name
    assert updated.description == "Refined description"

    records = load_registry(registry_path)
    assert len(records) == 1
    assert records[0].description == "Refined description"


def test_load_registry_raises_on_corrupted_json(tmp_path: Path) -> None:
    registry_path = tmp_path / "modules.json"
    registry_path.write_text("{not:json}", encoding="utf-8")

    with pytest.raises(ModuleRegistryError):
        load_registry(registry_path)


def test_store_registry_uses_atomic_write(tmp_path: Path) -> None:
    registry_path = tmp_path / "modules.json"

    record = ModuleRecord.create(
        name="echo_test",
        description="A test module",
        category="testing",
    )

    store_registry([record], registry_path)
    assert load_registry(registry_path) == [record]


def test_list_modules_filters_and_sorts(tmp_path: Path) -> None:
    registry_path = tmp_path / "modules.json"

    register_module(
        "alpha", "desc", "governance", registry_path=registry_path
    )
    register_module(
        "beta", "desc", "observability", registry_path=registry_path
    )
    register_module(
        "gamma", "desc", "Governance", registry_path=registry_path
    )

    all_records = list_modules(registry_path=registry_path)
    assert [record.name for record in all_records] == ["alpha", "gamma", "beta"]

    filtered = list_modules(category="governance", registry_path=registry_path)
    assert [record.name for record in filtered] == ["alpha", "gamma"]


def test_summarize_registry_returns_expected_metrics() -> None:
    records = [
        ModuleRecord(
            name="alpha",
            description="desc",
            category="governance",
            timestamp="2023-01-01T00:00:00+00:00",
            hash="1",
        ),
        ModuleRecord(
            name="beta",
            description="desc",
            category="governance",
            timestamp="2023-02-01T00:00:00+00:00",
            hash="2",
        ),
        ModuleRecord(
            name="gamma",
            description="desc",
            category="observability",
            timestamp="2023-01-15T00:00:00+00:00",
            hash="3",
        ),
    ]

    summary = summarize_registry(records)

    assert isinstance(summary, RegistrySummary)
    assert summary.total_modules == 3
    assert summary.categories == {"governance": 2, "observability": 1}
    assert summary.last_updated == "2023-02-01T00:00:00+00:00"

    empty_summary = summarize_registry([])
    assert empty_summary.total_modules == 0
    assert empty_summary.categories == {}
    assert empty_summary.last_updated is None
