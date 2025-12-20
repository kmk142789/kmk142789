# Federation Reference Instance

This reference instance anchors federation replication to the canonical Echo governance kernel.
It mirrors the governance kernel and interface maps from the repository root and supplies the
minimal directory layout required for safe replication without governance drift.

## Included

- `governance_kernel.json`
- `interface_map_strong.json`
- `interface_map_weak.json`
- `manifest/`
- `governance/`
- `contracts/`
- `logs/`

## Usage

1. Copy the entire `federation/reference-instance` folder to a new federation node.
2. Populate `manifest/`, `governance/`, and `contracts/` with validated payloads.
3. Run the readiness check from the repository root:

```bash
python tools/federation_readiness.py
```

Any drift in the kernel or interface maps will fail the check to prevent unsafe replication.
