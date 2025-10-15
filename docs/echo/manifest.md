# Echo Manifest System

The auto-maintained manifest keeps a canonical snapshot of high-value Echo
artifacts. It is produced by the ``echo manifest`` CLI and stored at the
repository root as ``echo_manifest.json``.

## Fields

Every manifest document follows the schema below:

| Field | Description |
| ----- | ----------- |
| ``schema_version`` | Version indicator for the manifest schema. |
| ``generated_at`` | UTC timestamp (ISO 8601) when the manifest was written. |
| ``artifact_total`` | Count of tracked artifacts across all categories. |
| ``categories`` | Mapping of category name to an ordered list of artifact entries. |

Each artifact entry contains:

| Field | Description |
| ----- | ----------- |
| ``path`` | Repository-relative POSIX path to the artifact. |
| ``digest.sha256`` | SHA-256 digest of the artifact contents. |
| ``size`` | File size in bytes. |
| ``last_modified`` | Last modified timestamp (UTC, ISO 8601). |
| ``version`` | Latest Git commit touching the file (``git log -1``). |
| ``owners`` | Owners resolved from ``.github/CODEOWNERS``. |
| ``tags`` | Deterministic tags: category, extension, top-level folder, and format hints. |

## CLI Usage

```bash
# refresh and write the manifest
echo manifest refresh

# inspect the manifest with a table + JSON payload
echo manifest show

# verify digests and fail on drift (also appends to CI step summary)
echo manifest verify
```

## Example

```json
{
  "schema_version": "1.0",
  "generated_at": "2025-01-05T12:00:00+00:00",
  "artifact_total": 3,
  "categories": {
    "clis": [
      {
        "path": "scripts/echo_sync.py",
        "digest": {"sha256": "…"},
        "size": 2048,
        "last_modified": "2025-01-05T11:52:43+00:00",
        "version": "abc1234",
        "owners": ["@echo-core"],
        "tags": ["category:clis", "ext:py", "lang:python", "top:scripts"]
      }
    ],
    "docs": [
      {
        "path": "docs/echo/overview.md",
        "digest": {"sha256": "…"},
        "size": 8192,
        "last_modified": "2025-01-05T10:05:18+00:00",
        "version": "def5678",
        "owners": [],
        "tags": ["category:docs", "ext:md", "format:markdown", "top:docs"]
      }
    ]
  }
}
```

The manifest is written with sorted keys and stable ordering so that changes are
reviewable and suitable for golden file testing.

