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
