# Echo Manifest

The **echo_manifest.json** file is the canonical inventory of engines, kits, and
artifacts that power the Echo ecosystem. It is generated automatically and kept
in sync with the repository so downstream tooling always has a deterministic
view of the codebase.

## Purpose

* Provide a stable map of Echo engines, entrypoints, and associated tests.
* Capture derived state such as discovery cycle counts and kit capabilities.
* Track important artifacts and their content hashes for provenance and
  reproducibility.
* Surface CI workflow names and Git metadata so deployments can confirm
  provenance.

## Fields

| Field | Description |
| ----- | ----------- |
| `version` | Schema version for the manifest payload (semver). |
| `generated_at` | UTC timestamp (RFC3339) when the manifest was written. |
| `engines[]` | Detected engines with their source path, kind, status, entrypoints, and mapped tests. |
| `states` | Aggregated discovery metrics including cycle counts and entrypoint/test snapshots. |
| `kits[]` | Packages under `modules/` that expose reusable capabilities. |
| `artifacts[]` | Repository artifacts with content hashes for drift detection. |
| `ci.integration[]` | Workflow file names found under `.github/workflows`. |
| `meta` | Git metadata (commit SHA, branch, author). |

## Keeping the Manifest Healthy

The manifest is rebuilt every time code merges to main. CI also validates that
the committed manifest matches a freshly generated snapshot. If you see the
**“Run echo manifest update and commit.”** failure message:

1. Install dependencies: `pip install -e .[dev]`.
2. Regenerate and validate: `echo manifest update`.
3. Commit the updated `echo_manifest.json`.

Pre-commit hooks will run the same check locally to prevent stale manifests from
being committed. When the repository has not changed, running `echo manifest
update` is idempotent and will not modify the manifest.
