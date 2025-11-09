from codex.advance_system_history import RecursiveForkTracker


def test_recursive_fork_tracker_records_and_snapshots(tmp_path, monkeypatch):
    history_path = tmp_path / "advance.jsonl"
    monkeypatch.setenv("ECHO_ADVANCE_HISTORY_PATH", str(history_path))
    tracker = RecursiveForkTracker(history_path)

    tracker.record_fork("fork-1", platform="echo-os", summary="Seeded" )
    record = tracker.fork_propose_upgrade("codex/add-ledger", "Integrate sovereign ledger")

    snapshot = tracker.snapshot()
    assert len(snapshot) == 2
    assert snapshot[-1]["fork_id"] == record.fork_id
    assert "hash" in snapshot[-1]["proposal"]
