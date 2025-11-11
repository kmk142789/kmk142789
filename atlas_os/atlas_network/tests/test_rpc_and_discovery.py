import json

from atlas_network import AtlasRPCClient, AtlasRPCServer, NodeDiscoveryService


def test_rpc_roundtrip():
    server = AtlasRPCServer()
    server.add_handler("echo", lambda payload: payload.upper())
    server.start()

    client = AtlasRPCClient("127.0.0.1", server.port, server.public_key)
    response = client.call("echo", b"atlas")
    server.stop()

    assert response.success
    assert response.payload == b"ATLAS"


def test_node_discovery_localhost():
    service_a = NodeDiscoveryService("node-a", "127.0.0.1", 5000, group="127.0.0.1", listen_port=50010)
    service_b = NodeDiscoveryService("node-b", "127.0.0.1", 5001, group="127.0.0.1", listen_port=50010)
    service_a.start()
    service_b.start()
    try:
        service_b.ingest_announcement(
            bytes(json.dumps({"node_id": "node-a", "host": "127.0.0.1", "port": 5000}), "utf-8")
        )
        service_a.ingest_announcement(
            bytes(json.dumps({"node_id": "node-b", "host": "127.0.0.1", "port": 5001}), "utf-8")
        )
        peers_a = list(service_a.peers())
        peers_b = list(service_b.peers())
        assert any(peer.node_id == "node-b" for peer in peers_a)
        assert any(peer.node_id == "node-a" for peer in peers_b)
    finally:
        service_a.stop()
        service_b.stop()
