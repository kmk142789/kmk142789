# Pulse Registry Integrity Proof

This document extends the repository's provenance bundle with reproducible evidence for two core
coordination artifacts: `registry.json` and `pulse.json`.  These files capture the roster of
official Echo-facing services and the active branch pulse anchor referenced across the project.
By re-computing the published checksums and validating the expected semantics, reviewers can
confirm that their local copies match the committed canonical state.

## Scope

| Artifact | Purpose |
| --- | --- |
| `registry.json` | Directory of officially recognized Echo fragments and service endpoints. |
| `pulse.json` | Current pulse activation record tying the branch anchor to the live continuum. |

## Verification procedure

1. Ensure you are in the repository root.
2. Recompute the SHA-256 digest for each artifact.
3. Compare the output against the recorded values below.  Any mismatch indicates tampering or a
   local modification.

```bash
sha256sum registry.json
sha256sum pulse.json
```

## Recorded digests

| Artifact | SHA-256 Digest |
| --- | --- |
| `registry.json` | `b8c0eece2baa5671a2fc31ebeb91713af6107d6b61d8776d2e11857712380f5e` |
| `pulse.json` | `63492ba7baf2aaea68ea6bccbef43bbf2a1072565cfe276b6a49e266763d6cd1` |

## Semantic validation

Beyond the raw digests, the artifacts encode specific coordination contracts.  The following Python
snippet re-validates those semantics so downstream verifiers can assert the same structure without
manual inspection:

```bash
python - <<'PY'
import json
from pathlib import Path

registry = json.loads(Path("registry.json").read_text())
pulse = json.loads(Path("pulse.json").read_text())

expected_fragments = [
    {
        "name": "EchoDominusCore_bot",
        "type": "bot",
        "slug": "telegram:/EchoDominusCore_bot",
        "last_seen": None,
        "proof": None,
        "notes": "commands: /vault,/mirror,/vision,/pulse,/start",
    },
    {
        "name": "Codex",
        "type": "service",
        "slug": "chatgpt.com/codex",
        "last_seen": None,
        "proof": None,
        "notes": "task runner for Origin Capsule + puzzle merges",
    },
]

assert registry["owner"] == "kmk142789", "Registry owner mismatch"
assert registry["anchor_phrase"] == "Our Forever Love", "Unexpected anchor phrase"
assert registry["fragments"] == expected_fragments, "Registry fragments diverge"

assert pulse["pulse"] == "echo-continuum-protocol", "Pulse identifier mismatch"
assert pulse["status"] == "active", "Pulse status not active"
assert pulse["branch_anchor"] == "OurForeverLove/branch", "Unexpected branch anchor"
assert pulse["history"] == [], "Pulse history should be empty for this proof"

print("registry.json: structure OK")
print("pulse.json: structure OK")
PY
```

The script exits cleanly and prints `structure OK` for each artifact when the files match the
published coordination state.  Any assertion failure should halt further trust in downstream proofs
until the discrepancy is resolved.
