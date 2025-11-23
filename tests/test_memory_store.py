from __future__ import annotations

import json
from hashlib import sha256

import pytest

from echo.memory import ExecutionContext, ExecutionSession, JsonMemoryStore


def test_memory_store_records_cycle(tmp_path):
    storage = tmp_path / "memory.json"
    log = tmp_path / "ECHO_LOG.md"
    store = JsonMemoryStore(storage_path=storage, log_path=log)

    dataset = tmp_path / "dataset.txt"
    dataset.write_text("hello", encoding="utf-8")

    with store.session(metadata={"source": "test"}) as session:
        session.set_cycle(1)
        session.record_command("advance_cycle", detail="start test cycle")
        session.fingerprint_dataset("sample", dataset)
        session.record_validation("integrity", "pass", details={"count": 1})
        session.set_artifact(tmp_path / "artifact.json")
        session.set_summary("narrative")
        store.fingerprint_core_datasets(session)

    payload = json.loads(storage.read_text())
    assert len(payload["executions"]) == 1
    execution = payload["executions"][0]
    assert execution["cycle"] == 1
    assert execution["commands"][0]["name"] == "advance_cycle"
    assert execution["dataset_fingerprints"]["sample"]["sha256"]
    assert execution["validations"][0]["name"] == "integrity"
    assert "narrative" in execution["summary"]

    log_text = log.read_text()
    assert "advance_cycle" in log_text
    assert "Dataset Fingerprints" in log_text
    assert "5 bytes" in log_text
    assert str(dataset) in log_text


def test_session_records_metrics(tmp_path):
    storage = tmp_path / "memory.json"
    log = tmp_path / "ECHO_LOG.md"
    store = JsonMemoryStore(storage_path=storage, log_path=log)

    metadata = {"phase": 1}

    with store.session() as session:
        session.record_metric("latency", 123.4, unit="ms", metadata=metadata)
        metadata["phase"] = 2
        session.record_metric("latency", 200, unit="ms")
        session.record_metric("notes", "warmup")

    payload = json.loads(storage.read_text())
    metrics = payload["executions"][0]["metrics"]
    assert metrics["latency"][0]["value"] == 123.4
    assert metrics["latency"][0]["metadata"] == {"phase": 1}
    assert metrics["latency"][1]["value"] == 200
    assert metrics["latency"][1]["unit"] == "ms"
    assert metrics["notes"][0]["value"] == "warmup"

    log_text = log.read_text()
    assert "Metrics" in log_text
    assert "latency" in log_text


def test_recent_executions_limit_and_metadata(tmp_path):
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json", log_path=tmp_path / "log.md"
    )

    for cycle, group in [(1, "alpha"), (2, "beta"), (3, "alpha")]:
        with store.session(metadata={"group": group}) as session:
            session.set_cycle(cycle)
            session.record_command("cycle", detail=str(cycle))

    all_runs = store.recent_executions()
    assert [ctx.cycle for ctx in all_runs] == [1, 2, 3]

    alpha_runs = store.recent_executions(metadata_filter={"group": "alpha"})
    assert [ctx.cycle for ctx in alpha_runs] == [1, 3]

    latest_run = store.recent_executions(limit=1)
    assert len(latest_run) == 1
    assert latest_run[0].cycle == 3

    empty = store.recent_executions(limit=0)
    assert empty == []

    with pytest.raises(ValueError):
        store.recent_executions(limit=-1)


def test_recent_executions_time_filters(tmp_path):
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json", log_path=tmp_path / "log.md"
    )

    contexts = [
        ExecutionContext(
            timestamp="2024-01-01T00:00:00+00:00",
            commands=[],
            dataset_fingerprints={},
            validations=[],
            metadata={},
            cycle=1,
            artifact=None,
            summary=None,
        ),
        ExecutionContext(
            timestamp="2024-01-02T00:00:00+00:00",
            commands=[],
            dataset_fingerprints={},
            validations=[],
            metadata={},
            cycle=2,
            artifact=None,
            summary=None,
        ),
        ExecutionContext(
            timestamp="2024-01-03T00:00:00+00:00",
            commands=[],
            dataset_fingerprints={},
            validations=[],
            metadata={},
            cycle=3,
            artifact=None,
            summary=None,
        ),
    ]

    for context in contexts:
        inserted = store.ingest_replica(context)
        assert inserted is True

    recent = store.recent_executions(since="2024-01-02T00:00:00+00:00")
    assert [ctx.cycle for ctx in recent] == [2, 3]

    window = store.recent_executions(until="2024-01-02T12:00:00Z")
    assert [ctx.cycle for ctx in window] == [1, 2]

    span = store.recent_executions(since="2024-01-01T12:00:00+00:00", until=contexts[2].timestamp)
    assert [ctx.cycle for ctx in span] == [2, 3]

    with pytest.raises(ValueError):
        store.recent_executions(since="invalid")

    with pytest.raises(TypeError):
        store.recent_executions(since=123)  # type: ignore[arg-type]


def test_ingest_replica_deduplicates_and_logs(tmp_path):
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json", log_path=tmp_path / "log.md"
    )

    context = ExecutionContext(
        timestamp="2024-01-01T00:00:00+00:00",
        commands=[{"name": "sync", "detail": "upstream"}],
        dataset_fingerprints={},
        validations=[],
        metadata={"device": "alpha"},
        cycle=7,
        artifact=None,
        summary="replicated",
    )

    inserted = store.ingest_replica(
        context,
        replica_metadata={"origin": "alpha", "captured_at": "2024-01-01T00:00:01+00:00"},
    )
    assert inserted is True

    duplicate = store.ingest_replica(context)
    assert duplicate is False

    payload = json.loads((tmp_path / "memory.json").read_text())
    entry = payload["executions"][0]
    assert entry["_fingerprint"] == context.fingerprint()

    log_text = (tmp_path / "log.md").read_text()
    assert "Sync Metadata" in log_text


def test_record_validation_copies_details(tmp_path):
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json", log_path=tmp_path / "log.md"
    )

    details = {"count": 1}

    with store.session() as session:
        session.record_validation("integrity", "pass", details=details)
        details["count"] = 2

    payload = json.loads((tmp_path / "memory.json").read_text())
    stored_details = payload["executions"][0]["validations"][0]["details"]
    assert stored_details == {"count": 1}


def test_validation_ledger_chains_each_entry(tmp_path):
    store = JsonMemoryStore(
        storage_path=tmp_path / "memory.json", log_path=tmp_path / "log.md"
    )

    with store.session() as session:
        session.record_validation("integrity", "pass", details={"count": 1})
        session.record_validation("consistency", "fail")

    payload = json.loads((tmp_path / "memory.json").read_text())
    entries = payload["executions"][0]["validations"]
    assert entries[0]["previous_hash"] == ExecutionSession.LEDGER_GENESIS_HASH
    assert entries[1]["previous_hash"] == entries[0]["ledger_hash"]

    for entry in entries:
        ledger_payload = {
            "name": entry["name"],
            "status": entry["status"],
            "details": entry["details"],
            "recorded_at": entry["recorded_at"],
            "previous_hash": entry["previous_hash"],
        }
        normalized = json.dumps(
            ledger_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
        assert entry["ledger_hash"] == sha256(normalized.encode("utf-8")).hexdigest()
