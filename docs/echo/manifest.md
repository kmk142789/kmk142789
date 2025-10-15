# Echo Manifest Lifecycle

The Echo manifest captures the repository's engine inventory, operational states, and CI wiring in a single deterministic JSON document. The generator (`tools/echo_manifest.py`) discovers engines, companion tests, kits, and workflows to keep the manifest aligned with the codebase.

## Fields

- **version** – semantic version of the manifest schema. Increment when the JSON layout changes.
- **generated_at** – UTC timestamp in RFC3339 format. The generator preserves the timestamp when nothing else changes so repeated updates are stable.
- **engines** – discovered Python entry points inside `echo/` and `modules/`. Each item records the file path, detected entrypoints, and the tests that cover it.
- **states** – aggregate metrics derived from the engines collection. `cycle` counts the engines, `resonance` counts entrypoints, `amplification` is the resonance-per-engine ratio, and `snapshots` summarise coverage health.
- **kits** – packages inside `modules/` along with their exported APIs (from `__all__`) and detected capabilities (public classes and functions).
- **artifacts** – important generated files tracked via a short SHA256 hash.
- **ci.integration** – the set of GitHub workflow definitions discovered under `.github/workflows/`.
- **meta** – commit metadata resolved with `git`. Falls back to `"unknown"` when Git data is unavailable.

## Workflow

1. Run `echo manifest update` whenever code changes affect engines, tests, or workflows.
2. Commit the updated `echo_manifest.json` alongside the related code changes.
3. Push your branch. CI will execute `echo manifest validate` and fail with `Run echo manifest update and commit.` if the manifest is stale.

## Fixing a Red Check

1. Pull the latest changes.
2. Execute `echo manifest update` from the repository root.
3. Review the diff to understand the discovered changes.
4. Commit the manifest update and push.

## Changelog Discipline

When the manifest schema evolves:

1. Bump `SCHEMA_VERSION` in `tools/echo_manifest.py`.
2. Update this document with the new field definitions.
3. Regenerate `echo_manifest.json`.
4. Note the schema update in your PR description.
