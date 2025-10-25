# Canonical Map Integrity Proof

This document extends the repository's ledger proofs by providing a reproducible audit trail for
`canonical-map.json`.  That JSON file enumerates the official code, domain, and package endpoints
for the Keyhunter project.  By checking both the file digest and its semantic contents, reviewers
can confirm that the canonical coordinates published here match the project state referenced in
other attestations.

## Scope

The proof covers the canonical source-of-truth entries for:

| Class    | Canonical identifier                          | Notes |
|----------|-----------------------------------------------|-------|
| Repository | `https://github.com/kmk142789/keyhunter`      | Mirrors GitLab and GitHub forks. |
| Domain     | `keyhunter.app`                               | Aliases `www.keyhunter.app`, `api.keyhunter.app`. |
| Package    | `npm:@keyhunter/core`                         | Declares conflicts with `npm:keyhunter`, `pypi:keyhunter`. |

## Recorded digest

Confirm that your local copy of `canonical-map.json` matches the committed artifact by reproducing
its SHA-256 fingerprint:

```bash
sha256sum canonical-map.json
```

Expected digest:

```
c0f8a22ea6215018becd2a540d4befb4f3b05779a48913a2c738ddca3ecbe058  canonical-map.json
```

A mismatch indicates either a local modification or a tampered artifact, in which case stop and
investigate before trusting downstream attestations.

## Semantic validation

Beyond the raw digest, the canonical map is meant to encode very specific identifiers.  The
following Python snippet re-validates those semantics so that downstream verifiers can assert the
same structure without needing to eyeball the JSON:

```bash
python - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("canonical-map.json").read_text())

expected = {
    "owner": "kmk142789",
    "sources": [
        {
            "type": "repo",
            "canonical": "https://github.com/kmk142789/keyhunter",
            "mirrors": [
                "https://gitlab.com/...",
                "https://github.com/other/fork",
            ],
        },
        {
            "type": "domain",
            "canonical": "keyhunter.app",
            "aliases": [
                "www.keyhunter.app",
                "api.keyhunter.app",
            ],
        },
        {
            "type": "package",
            "canonical": "npm:@keyhunter/core",
            "conflicts": [
                "npm:keyhunter",
                "pypi:keyhunter",
            ],
        },
    ],
}

assert data["owner"] == expected["owner"], "Owner mismatch"
assert data["sources"] == expected["sources"], "Source entries diverge"
print("canonical-map.json: structure OK")
PY
```

The script exits cleanly and prints `canonical-map.json: structure OK` when the file matches the
published canonical coordinates.

---

By capturing both the cryptographic digest and the schema-level invariants, this proof equips
integrators, auditors, and downstream bridges with an additional reproducible checkpoint that ties
Keyhunter's canonical routing to the rest of the provenance bundle.
