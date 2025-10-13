from __future__ import annotations

import json
import pytest

from echo.memory import JsonMemoryStore


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
