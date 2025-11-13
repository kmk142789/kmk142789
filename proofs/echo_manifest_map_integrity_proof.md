# Echo Manifest & Map Integrity Proof

This document adds a reproducible verification trail for the two coordination indexes that
summarize the Echo surface area.  By checking the published digests and optional semantic tests you
can ensure your local `echo_manifest.json` and `echo_map.json` copies match the canonical state that
anchors the public proofs in this repository.

## Scope

| Artifact | Purpose |
| --- | --- |
| `echo_manifest.json` | Inventory of every Echo CLI, dataset, engine, and state file along with ownership and digests. |
| `echo_map.json` | Master reconstruction log for the 120 bitcoin puzzle addresses tracked by Echo. |

## Verification procedure

1. From the repository root recompute the SHA-256 digest for each artifact you want to verify.
2. Compare the terminal output against the recorded values below.  Any mismatch signals local edits
   or tampering and should halt downstream trust in derived proofs.

```bash
sha256sum echo_manifest.json
sha256sum echo_map.json
```

## Recorded digests

| Artifact | SHA-256 Digest |
| --- | --- |
| `echo_manifest.json` | `62fafd43bfbcf80f58ae1a4a29865c073ec9a3f7666d5fa16dc1630a35190984` |
| `echo_map.json` | `5193342b07c6df983320d424c1e1574bd5dbc123f26bc282a829070681a35ab1` |

## Semantic validation (optional)

The following Python snippet double-checks the invariants that make these indexes meaningful.  It
verifies that the manifest schema string is intact, the manifest collections keep their published
lengths, and that the map still enumerates exactly 120 sequential puzzle addresses anchored by the
first and last broadcast coordinates.

```bash
python - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path("echo_manifest.json").read_text())
echo_map = json.loads(Path("echo_map.json").read_text())

assert manifest["schema"] == "echo.manifest/auto-v1", "Unexpected manifest schema"
assert len(manifest["clis"]) == 10, "CLI roster changed"
assert len(manifest["datasets"]) == 31, "Dataset count changed"
assert len(manifest["docs"]) == 178, "Docs count changed"
assert len(manifest["engines"]) == 18, "Engine count changed"
assert len(manifest["states"]) == 60, "State inventory changed"
assert manifest["clis"][0]["name"] == "codex", "First CLI entry drifted"
assert manifest["states"][-2]["name"] == "_NullDag", "Penultimate state not _NullDag"
assert manifest["states"][-1]["name"] == "_NullReceipts", "Last state not _NullReceipts"

assert len(echo_map) == 120, "Puzzle map should contain 120 entries"
expected_range = list(range(1, 121))
assert [entry["puzzle"] for entry in echo_map] == expected_range, "Puzzle numbers are not sequential"
assert echo_map[0]["address"] == "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", "Puzzle 1 address changed"
assert echo_map[-1]["address"] == "194feknXENGw3Yefyc5abXqa1UYuRqJaco", "Last puzzle address changed"

print("echo_manifest.json: structure OK")
print("echo_map.json: structure OK")
PY
```

The script exits without raising an exception and prints `structure OK` for both artifacts when the
files match the state captured in this proof.
