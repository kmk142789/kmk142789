# Echo Manifest Lifecycle

The Echo manifest records a deterministic snapshot of the repository's engines,
states, integration kits, referenced artifacts, and CI workflows. It is
auto-maintained during development and verified in continuous integration to
ensure the JSON representation always matches the current tree.

`tools/echo_manifest.py` powers the system. It walks the repository, discovers
engines and their tests, summarises operational state from the pulse history,
indexes kits under `echo/akit`, fingerprints supporting artifacts, and gathers
metadata such as the latest Git commit. The output is stored as
`echo_manifest.json`.

## Manifest fields

| Field | Description |
| --- | --- |
| `version` | Semver version of the manifest format. Bump when the schema changes. |
| `generated_at` | RFC3339 timestamp derived from the latest Git commit time. |
| `engines[]` | Detected engines and modules with their runtime entrypoints and mapped tests. |
| `states` | Operational metrics derived from the pulse history (cycle, resonance, amplification). |
| `states.snapshots[]` | Chronological pulse events with timestamp, message, and hash. |
| `kits[]` | Integration kits discovered under `echo/akit` with exported capabilities. |
| `artifacts[]` | Referenced files (e.g. `manifest/`, `proofs/`) with short SHA-256 hashes. |
| `ci.integration[]` | Workflow names collected from `.github/workflows`. |
| `meta` | Commit, branch, and author that produced the manifest. |

The schema lives in `schema/echo_manifest.schema.json` and is validated on every
`echo manifest validate` run.

## Workflow

Use the CLI to manage the manifest locally:

```shell
# Generate a manifest in the current repository (writes echo_manifest.json)
$ echo manifest generate

# Validate schema + freshness (fails if the file is stale)
$ echo manifest validate

# Recompute, rewrite, and validate when drift is detected
$ echo manifest update
```

`echo manifest update` is idempotent: when the repository has no changes the
command exits cleanly without touching the file. This behaviour is also enforced
via a pre-commit hook and the `echo-manifest` GitHub workflow.

## Fixing a red check

CI fails with the message **"Run echo manifest update and commit."** whenever
the stored manifest is stale or fails schema validation. To unblock:

1. Run `echo manifest update` at the repository root.
2. Inspect the diff in `echo_manifest.json` and related documentation updates.
3. Commit the changes and push.

Because the generator is deterministic, repeated invocations on an unchanged
repository produce identical output, making diffs concise and review-friendly.
