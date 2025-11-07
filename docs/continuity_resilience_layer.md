# Continuity Resilience Layer Notes

## 1. Existing invariants and extension seams

### `packages/core/src/echo/bank/continuity.py`
- `ContinuitySafeguards` persists a `ContinuityConfig` whose invariants include:
  - Every configured mirror directory exists before mirroring occurs.
  - Trustee roster and threshold are stored alongside the mirrored ledger artifacts for multi-sig recovery logging.
  - Mirroring only copies artifacts that currently exist on disk, protecting against partially generated bundles.
- Extension seams:
  - `ContinuityConfig.mirrors` can be extended to include new categories (e.g., geo-partitioned mirrors) as long as they resolve to `Path` objects.
  - `ContinuitySafeguards.mirror_artifacts` is the central interception point for augmenting mirroring behaviour (e.g., integrity hashing or remote transports).
  - `record_multisig_checkpoint` writes JSONL entries; adding new recovery metadata stays backward compatible as long as keys are appended per-line.

### `ledger/continuity_guardian.py`
- `ContinuityGuardian` coordinates replica nodes and state exports with the following invariants:
  - Each `ReplicaNode` creates a stable directory layout (`ledger/`, `proofs/`, `puzzles/`, `compliance/`) before copies begin.
  - `sync_entry` always exports the authoritative state JSON after mirroring, guaranteeing that recovery operators have the latest digest even when no replicas are configured.
  - The optional `MultiSigRecoveryPlan` embeds trustee data in exports without mutating runtime mirroring state.
- Extension seams:
  - `ReplicaNode.ensure_structure` is the single location to extend storage surfaces (e.g., add `receipts/` mirrors).
  - `ContinuityGuardian.sync_entry` can branch per-node to support typed replica classes (air-gapped, cloud) without disturbing the state export path.
  - The recovery payload produced by `_export_state` is JSON-serialised with predictable keys, easing downstream parsing.

### `packages/core/src/echo/echonet/poc.py`
- `accept_chain` enforces protocol invariants:
  - Every hop must possess a predecessor hash and pass signature verification.
  - Traversal halts when a known receipt is encountered or when 5,000 hops are inspected, bounding recursion depth.
  - Missing records or failed verifications immediately invalidate the candidate tip.
- Extension seams:
  - `ReceiptStore` and `Keyring` are defined as protocols, enabling drop-in replacements (remote stores, HSM-backed key verification).
  - Additional ledger actions can be captured by expanding the tuple encoded into the verification message while keeping previous fields stable.

## 2. Resilience profile data structures

The following data classes capture a richer continuity posture that can plug into existing safeguards:

```python
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Sequence

@dataclass(slots=True)
class MirrorSurface:
    """Describes a mirror target and the artifacts it should receive."""

    name: str
    root: Path
    artifacts: Sequence[str] = ("ledger", "proof", "ots")
    is_cold_storage: bool = False

@dataclass(slots=True)
class RecoveryWindow:
    """Defines how far back operators can rewind the ledger safely."""

    max_entries: int
    max_age: timedelta
    retention_policy: str = "rolling"

@dataclass(slots=True)
class QuorumRule:
    """Captures trustee signature requirements for a recovery action."""

    action: str
    threshold: int
    eligible_trustees: Sequence[str]

@dataclass(slots=True)
class ResilienceProfile:
    """Aggregates continuity safeguards for the bank."""

    mirrors: Sequence[MirrorSurface] = field(default_factory=tuple)
    recovery_window: RecoveryWindow | None = None
    quorum: Sequence[QuorumRule] = field(default_factory=tuple)
    last_evaluated: str | None = None
```

Interaction guidance:
- `ResilienceProfile.mirrors` can be mapped into `ContinuityConfig.mirrors`. A helper on `ContinuitySafeguards` can project mirror surfaces into filesystem paths while honouring `is_cold_storage` (e.g., skip hot copies, schedule async uploads).
- `RecoveryWindow` aligns with the JSONL stream produced by `record_multisig_checkpoint`; the window can cap file size or trigger pruning once checkpoints exceed `max_entries` or `max_age`.
- `QuorumRule` complements `ContinuityConfig.threshold` and `MultiSigRecoveryPlan.trustees` by introducing action-specific thresholds (e.g., "rotate-key", "restore-ledger"). `ContinuitySafeguards` can expose a method to fetch the relevant quorum before writing a checkpoint so operators know which trustees must co-sign.
- The profile’s `last_evaluated` timestamp can be stored next to `ContinuitySafeguards.config.json` to show when resilience posture was last audited.

## 3. Manifest and CLI touchpoints

To surface the resilience layer end-to-end:
- **Manifest (`packages/core/src/echo_manifest.py`)**
  - Extend `EchoManifest` to include an optional `resilience` section summarising the active `ResilienceProfile` (mirrors, recovery window bounds, quorum catalogue).
  - Populate the section inside `build_manifest` by querying `ContinuitySafeguards.continuity_report()` or a lightweight adaptor that translates the profile into manifest-ready dictionaries.

- **Ledger state export (`ledger/continuity_guardian.py`)**
  - Embed a `resilience_profile` payload in `_export_state` so replica operators and automation can cross-check that their mirrors satisfy the expected posture.

- **CLI (`echo_cli/main.py`)**
  - Add a `continuity` command group exposing subcommands like `profile show`, `profile verify`, and `profile rotate` that wrap `ContinuitySafeguards` helpers.
  - Provide JSON output flags so operators can integrate the resilience profile into dashboards or audits.

- **Configuration manifest files**
  - Ensure `echo_manifest.json` (and any derivative registry entries) reference the resilience section so downstream services receive the augmented schema.
  - Update any deployment manifests under `manifest/` or `ops/` that currently materialise `ContinuityConfig` to accept the richer profile (e.g., include cold storage descriptors or quorum overrides).

- **Documentation and schema updates**
  - Regenerate OpenAPI or JSON schemas in `schemas/` if external services validate manifest payloads—introduce `resilienceProfile` definitions mirroring the dataclasses above.

These touchpoints provide a cohesive path from resilience design to operator tooling while staying compatible with current safeguards.
