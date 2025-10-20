from __future__ import annotations

from echo.memory import JsonMemoryStore
from echo.sync import CloudSyncCoordinator, DirectorySyncTransport


def test_directory_transport_replication(tmp_path):
    transport_root = tmp_path / "transport"
    store_a = JsonMemoryStore(
        storage_path=tmp_path / "a.json", log_path=tmp_path / "a.md"
    )
    store_b = JsonMemoryStore(
        storage_path=tmp_path / "b.json", log_path=tmp_path / "b.md"
    )

    with store_a.session(metadata={"device": "alpha"}) as session:
        session.set_cycle(1)
        session.set_summary("alpha context")

    coordinator_a = CloudSyncCoordinator(
        "alpha",
        store_a,
        DirectorySyncTransport(transport_root),
    )
    report_a = coordinator_a.sync()
    assert report_a.known_contexts == 1

    coordinator_b = CloudSyncCoordinator(
        "beta",
        store_b,
        DirectorySyncTransport(transport_root),
    )
    report_b = coordinator_b.sync()
    assert report_b.applied_contexts == 1

    contexts = store_b.recent_executions()
    assert len(contexts) == 1
    assert contexts[0].summary == "alpha context"

    log_text = (tmp_path / "b.md").read_text()
    assert "Sync Metadata" in log_text

    # A second sync should be idempotent
    follow_up = coordinator_b.sync()
    assert follow_up.applied_contexts == 0
