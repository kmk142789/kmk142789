# Pulse Narrator — Spec

- **Inputs**: Pulse snapshot stats, Continuum Index count, optional top prefixes and channels.
- **Outputs**: Markdown poem or log with timestamps and commit short-sha.
- **Determinism**: Controlled by `seed` (default derived from snapshot id).
- **Persistence**: `docs/narratives/<snap>_<hash>_<style>.md`.
- **Interfaces**:
  - CLI: `echo-cli pulse narrator --inputs snapshot.json --style poem --seed 88 --save`
  - API: `GET /pulse/narrator?style=poem&snapshot_id=...&index_count=...&save=true`
