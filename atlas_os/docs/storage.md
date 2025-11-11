# Storage Subsystem

The distributed virtual filesystem (VFS) coordinates multiple storage
nodes, each powered by a driver implementing the `FileDriver` protocol.

## Drivers

- `LocalFileDriver` writes data to the local disk under a configured
  root directory.
- `MemoryFileDriver` stores file contents in-memory for ultra-fast
  ephemeral storage.
- `EncryptedFileDriver` wraps another driver and applies AES-256-GCM
  authenticated encryption to all reads/writes.

## Transaction Logging

Every filesystem operation appends a structured entry to the
`TransactionLog`.  Logs can be tailed or replayed to reconstruct the
state of a cluster.

## Snapshots

`SnapshotManager` captures point-in-time snapshots by reading every file
in the namespace and storing the data in-memory.  Snapshots can be used
for rollbacks in test environments or quick disaster recovery drills.

## Integrity Checking

`IntegrityChecker` computes SHA-256 digests for selected paths and can
verify that no data corruption has occurred.  Manifest exports can be
persisted to disk or forwarded to monitoring systems.
