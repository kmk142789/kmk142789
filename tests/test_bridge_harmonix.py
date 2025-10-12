from __future__ import annotations

import json
from pathlib import Path

from cognitive_harmonics.harmonix_bridge import (
    BridgeConfig,
    BridgeEmitter,
    DistributedBridgeGraph,
    EchoBridgeHarmonix,
    PolicyProgram,
    SecureChannelSpec,
)
from echo import harmonix_connect


def _prepare_stream(tmp_path: Path, *, entries: int = 4) -> BridgeConfig:
    stream = tmp_path / "stream.jsonl"
    with stream.open("w", encoding="utf-8") as handle:
        for seq in range(1, entries + 1):
            handle.write(json.dumps({"seq": seq, "payload": seq}) + "\n")
    return BridgeConfig(
        stream_path=stream,
        anchor_dir=tmp_path / "anchors",
        state_path=tmp_path / "state.json",
        batch_size=entries,
    )


def test_bridge_harmonix_distributed_mesh(tmp_path: Path) -> None:
    config = _prepare_stream(tmp_path)
    emitter = BridgeEmitter(config)
    mesh = DistributedBridgeGraph(controller_id="ctrl")
    program = PolicyProgram.from_text("throughput_mbps>0->scale_out;connect bridge-0->edge-1")
    secure = SecureChannelSpec(protocol="tls")
    harmonix = EchoBridgeHarmonix(
        emitter=emitter,
        mesh_controller=mesh,
        policy=program,
        secure_channel=secure,
    )

    state, payload = harmonix.run_cycle()
    metadata = payload["metadata"]

    assert metadata["telemetry"]["throughput_mbps"] > 0
    assert metadata["policy"]["actions"], "policy actions should be emitted"
    assert metadata["mesh"]["nodes"], "mesh snapshot should include nodes"
    assert metadata["secure_channel"]["protocol"] == "tls"
    assert any(event.startswith("Telemetry synthesised") for event in state.events)

    nodes = metadata["mesh"]["nodes"]
    assert "bridge-0" in nodes
    assert any(key.startswith("edge-") for key in nodes), "scale out should add edge node"


def test_harmonix_sdk_connect_session(tmp_path: Path) -> None:
    config = _prepare_stream(tmp_path)
    session = harmonix_connect(
        "127.0.0.1:7500",
        "throughput_mbps>0->scale_out",
        config=config,
    )

    result = session.run_cycle()

    assert result["telemetry"]["throughput_mbps"] > 0
    assert result["mesh"]["nodes"]
    assert result["policy"]["actions"], "session should expose policy actions"

    snapshot = session.mesh_snapshot()
    assert snapshot["controller"]["links"], "controller should maintain adjacency"
