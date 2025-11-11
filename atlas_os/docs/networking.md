# Networking

Atlas Network exposes a protobuf RPC service secured with Curve25519
key agreement and ChaCha20-Poly1305 encryption.  Clients connect to
servers by exchanging ephemeral public keys, then encrypt RPCRequest and
RPCResponse messages defined in `atlas_network/proto/atlas.proto`.

Node discovery relies on UDP multicast announcements.  Each node runs a
`NodeDiscoveryService` that broadcasts its node identifier and listens
for peer packets.  Discovered nodes are registered in the `RoutingTable`
which prioritizes routes by recency and static priority weights.

Heartbeat monitoring emits protobuf-encoded heartbeats at fixed
intervals.  The `HeartbeatMonitor` detects failures by tracking the most
recent timestamp per node and invoking callbacks if a peer exceeds the
configured timeout.
