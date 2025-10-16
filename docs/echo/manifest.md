# Echo Manifest System

The Echo manifest captures a reproducible snapshot of key assets in the
repository.  It is generated automatically via the `echo manifest refresh`
command and stored as `echo_manifest.json` at the root of the project.

## Fields

Each manifest entry shares a common schema:

| Field | Description |
| --- | --- |
| `name` | Human readable identifier derived from the underlying asset. |
| `path` | Repository-relative file path to the source of the asset. |
| `category` | One of `engine`, `state`, `cli`, `dataset`, or `doc`. |
| `digest` | SHA-256 digest of the file contents. |
| `size` | File size in bytes. |
| `version` | Short identifier derived from the digest for quick comparison. |
| `last_modified` | ISO 8601 timestamp of the last commit touching the file (if available). |
| `owners` | Owners resolved from `.github/CODEOWNERS`. |
| `tags` | Normalised tags describing the asset (language, extension, grouping). |

## Commands

```shell
# Recompute the manifest and update echo_manifest.json
$ echo manifest refresh

# Display a tabular summary and the JSON payload
$ echo manifest show

# Validate file sizes and digests against the stored manifest
$ echo manifest verify
```

## Examples

Running `echo manifest show` prints category tables followed by the canonical
JSON manifest.  When used in CI, `echo manifest verify` appends its status to
the GitHub Actions job summary, providing quick visibility into drift.
