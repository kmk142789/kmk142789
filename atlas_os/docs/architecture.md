# Atlas OS Architecture

Atlas OS is composed of six subsystems that can operate independently
or together as a modular distributed operating environment.  Each
module ships as a standalone package with dedicated unit tests and
integration points.

## Kernel

The kernel provides a cooperative event loop, a priority scheduler with
starvation protection, a message bus, and a resource manager that tracks
CPU and memory budgets on priority lanes.  Metrics are exported as JSON
for consumption by the CLI or dashboard.

## Storage

The storage subsystem offers a distributed virtual filesystem with
pluggable drivers.  The LocalFS driver writes to disk, MemoryFS stores
in RAM, and EncryptedFS uses AES-256-GCM to secure content.  Operations
are recorded in a transaction log with snapshot and integrity checking
utilities.

## Network

Networking is built on protobuf-defined RPC messages with Curve25519
key exchange for encryption.  Node discovery uses UDP multicast while
routing and heartbeat monitors maintain a resilient topology map.

## Runtime

The runtime contains a Wasm-inspired stack machine that enforces memory
and execution time limits.  A process isolator can run sandboxes in
separate OS processes for additional safety.

## CLI & UI

The CLI offers operational commands (`atlas status`, `atlas nodes`,
`atlas storage list`, and `atlas logs`).  The UI is a React + TypeScript
single-page dashboard that consumes metrics via WebSockets and renders a
node graph, metrics grid, and log stream.
