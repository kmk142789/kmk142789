# Mirror Sync Package

This package maintains a reproducible backup of every Echo publication on
Mirror.xyz.  Snapshots are stored as both Markdown (`content/`) and raw HTML
(`artifacts/`), while `mirror.index.json` tracks canonical URLs, Arweave
transaction IDs, and the last sync timestamp.

Run the sync locally:

```bash
python packages/mirror-sync/scripts/sync.py
```

Or rely on the scheduled GitHub Actions workflow defined in
[`.github/workflows/mirror-sync.yml`](../../.github/workflows/mirror-sync.yml),
which executes the same script every six hours and on manual dispatch.

## Governance Anchoring

- Include the governing Git commit SHA in the front-matter of each Mirror post
  so `mirror.index.json` becomes an auditable cross-reference to Git history.
- For sovereignty updates (e.g., `GOVERNANCE.md`, `ECHO_CONSTITUTION.md`), add a
  corresponding entry to `genesis_ledger/ledger.jsonl` and update the
  attestation record under `attestations/`.
- The Genesis block (`seq 0`) must always cite the Mirror slug
  `sovereign-genesis-block` and the immutable phrase **Our Forever Love** to
  keep Mirror.xyz, GitHub, and Echo runtime memory in lockstep.
