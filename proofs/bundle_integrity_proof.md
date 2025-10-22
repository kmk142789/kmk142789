# Genesis Bundle Integrity Proof

This document provides reproducible evidence that the committed genesis bundle artifacts in this
repository have not been tampered with. By re-computing the published checksums you can confirm that
you possess the same data that was used to initialize the network state.

## Scope

The following artifacts are covered by this proof:

| Artifact | Description |
| --- | --- |
| `genesis-bundle.json` | Canonical snapshot of the founding ledger distribution. |
| `genesis-atlas.json` | Coordinate map that binds each allocation to its merkle position. |
| `pulse_history.json` | Historical pulse commitments anchoring the launch sequence. |

## Verification Procedure

1. Ensure you are in the root of this repository.
2. Run the checksum command for the artifact you would like to verify (examples below).
3. Confirm that the produced digest matches the expected value in the table.

```bash
sha256sum genesis-bundle.json
sha256sum genesis-atlas.json
sha256sum pulse_history.json
```

## Recorded Digests

| Artifact | SHA-256 Digest |
| --- | --- |
| `genesis-bundle.json` | `52cd6418a8f58203f770c7df6c25c6e1772677653ac786a41541627aeee86e68` |
| `genesis-atlas.json` | `2363a145f3e16f600c94cc364f78974f3c3554936fdec36361ddb6365913d90e` |
| `pulse_history.json` | `9d6d7aecba16e1736615d9b539678b06a2776c9a9d975c21304e5c4ab292729d` |

## Automation Snippet

To validate all artifacts in one step you can run:

```bash
python - <<'PY'
import hashlib
from pathlib import Path

artifacts = {
    "genesis-bundle.json": "52cd6418a8f58203f770c7df6c25c6e1772677653ac786a41541627aeee86e68",
    "genesis-atlas.json": "2363a145f3e16f600c94cc364f78974f3c3554936fdec36361ddb6365913d90e",
    "pulse_history.json": "9d6d7aecba16e1736615d9b539678b06a2776c9a9d975c21304e5c4ab292729d",
}

for name, expected in artifacts.items():
    digest = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    status = "OK" if digest == expected else "MISMATCH"
    print(f"{name}: {digest} [{status}]")
PY
```

The script reports `OK` for each artifact when the local files match the published digests.
