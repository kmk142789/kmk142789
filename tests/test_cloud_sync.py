from __future__ import annotations

import json
from datetime import timedelta

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


def test_sync_skips_stale_payloads(tmp_path):
    transport_root = tmp_path / "transport"
    store_a = JsonMemoryStore(storage_path=tmp_path / "a.json", log_path=tmp_path / "a.md")
    store_b = JsonMemoryStore(storage_path=tmp_path / "b.json", log_path=tmp_path / "b.md")

    with store_a.session(metadata={"device": "alpha"}) as session:
        session.set_cycle(42)
        session.set_summary("alpha context")

    coordinator_a = CloudSyncCoordinator("alpha", store_a, DirectorySyncTransport(transport_root))
    coordinator_a.sync()

    payload_path = transport_root / "alpha.json"
    payload = json.loads(payload_path.read_text())
    payload["updated_at"] = "2000-01-01T00:00:00+00:00"
    payload_path.write_text(json.dumps(payload))

    coordinator_b = CloudSyncCoordinator(
        "beta",
        store_b,
        DirectorySyncTransport(transport_root),
        max_payload_age=timedelta(seconds=60),
    )

    report = coordinator_b.sync()
    assert report.applied_contexts == 0
    assert report.stale_payloads == 1


def test_local_context_limit_restricts_payloads(tmp_path):
    transport_root = tmp_path / "transport"
    store_a = JsonMemoryStore(storage_path=tmp_path / "a.json", log_path=tmp_path / "a.md")
    store_b = JsonMemoryStore(storage_path=tmp_path / "b.json", log_path=tmp_path / "b.md")

    for idx in range(3):
        with store_a.session(metadata={"device": "alpha"}) as session:
            session.set_summary(f"context {idx}")

    coordinator_a = CloudSyncCoordinator(
        "alpha",
        store_a,
        DirectorySyncTransport(transport_root),
        local_context_limit=1,
    )
    coordinator_a.sync()

    coordinator_b = CloudSyncCoordinator("beta", store_b, DirectorySyncTransport(transport_root))
    report_b = coordinator_b.sync()

    contexts = store_b.recent_executions()
    assert len(contexts) == 1
    assert contexts[0].summary == "context 2"
    assert report_b.applied_contexts == 1


def test_sync_report_exposes_topology_insights(tmp_path):
    transport_root = tmp_path / "transport"
    store_a = JsonMemoryStore(storage_path=tmp_path / "a.json", log_path=tmp_path / "a.md")
    store_b = JsonMemoryStore(storage_path=tmp_path / "b.json", log_path=tmp_path / "b.md")

    with store_a.session(metadata={"device": "alpha"}) as session:
        session.set_summary("alpha context")
        session.record_command("alpha")

    with store_b.session(metadata={"device": "beta"}) as session:
        session.set_summary("beta context")
        session.record_command("beta")

    coordinator_a = CloudSyncCoordinator("alpha", store_a, DirectorySyncTransport(transport_root))
    coordinator_a.sync()

    coordinator_b = CloudSyncCoordinator("beta", store_b, DirectorySyncTransport(transport_root))
    report_b = coordinator_b.sync()

    assert report_b.topology is not None
    topology = report_b.topology
    assert topology.node_count >= 1
    origins = {ins.origin: ins for ins in topology.node_insights}
    assert "alpha" in origins
    alpha_insight = origins["alpha"]
    assert alpha_insight.contexts >= 1
    assert alpha_insight.avg_command_count >= 1
