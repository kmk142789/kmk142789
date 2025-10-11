from __future__ import annotations

import json

from echo.mobility_protocol import MobilityProtocol


def test_mobility_protocol_cycle(tmp_path, monkeypatch):
    protocol = MobilityProtocol(identity="Echo", storage_path=tmp_path / "atlas.json")

    monkeypatch.setattr(protocol, "_discover_interfaces", lambda: [("eth0", "")])
    monkeypatch.setattr(protocol, "_resolve_host_aliases", lambda: ["echo.local"])
    monkeypatch.setattr(protocol, "_bluetooth_marker", lambda: "detected::test")

    points = protocol.scan_connection_points()
    identifiers = {point.identifier for point in points}
    assert "net::eth0" in identifiers
    assert "host::echo.local" in identifiers
    assert "link::bluetooth" in identifiers

    hop = protocol.travel("net::eth0")
    assert hop["to"] == "net::eth0"
    assert protocol.atlas.current_node == "net::eth0"

    updated = protocol.adjust_permissions("net::eth0", grant=["read"], revoke=())
    assert updated.permissions == ["read"]

    path = protocol.persist_atlas()
    with path.open() as handle:
        payload = json.load(handle)
    assert payload["summary"]["known_nodes"] == len(protocol.atlas.nodes)

    script = protocol.compose_cognitive_script()
    assert script["core_identity"] == "Echo"
    assert script["directives"]["adaptive_interface_control"]["net::eth0"] == ["read"]
