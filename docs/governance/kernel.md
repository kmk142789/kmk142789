# Governance Kernel Lifecycle

The governance kernel initializes with a deterministic state and immediately appends an `INIT` integrity event to the append-only ledger at `.echo/governance_ledger.jsonl`. The kernel maintains a `KernelState` object with a `phase`, current `sci` (sovereign confidence index), tracked `threads`, and the most recent change request ID.

## Echo governance kernel (extracted)
The canonical kernel configuration lives in `governance_kernel.json` and is treated as the machine-readable source of truth for replication. The kernel is composed of four cooperative subsystems that must remain aligned when running in new instances:

- **Manifest loader**: Discovers and validates governance-facing manifests from `manifest/*.json`, `governance/*.json`, and `contracts/*.json`. Validation includes JSON schema checks, signature chain verification, and UQL preflight validation.
- **UQL enforcer**: Applies constraint sets (`access_control`, `supply_bounds`, `ritual_safety`) through the `uql-integrated` solver. The fallback strategy is `reject_on_conflict`, so any constraint clash blocks the action.
- **State machine**: Enforces the governance lifecycle with `INITIAL → FUNCTIONAL → DEGRADED/RESET` transitions. Guard conditions (`uql_enforced`, `manifest_validated`, `incident_logged`, `ritual_reset`) must resolve true before transitions.
- **Event dispatcher**: Routes governance events through topics (`governance.cr`, `ledger.append`, `ritual.invoke`) and handlers (`validate_cr`, `record_attestation`, `hash_event`, `store_integrity`, `apply_ritual`, `state_correction`). It retries three times before sending failures to `logs/dispatcher.dlq`.

Keep the kernel config, integrity events, and the runtime state machine aligned with this file when documenting or replicating the kernel.

## Instance boundaries (authoritative vs. local)
When replicating the Echo governance kernel, draw a hard boundary between **authoritative governance artifacts** and **instance-local operational state**. Only the authoritative artifacts are eligible for federation replication.

**Authoritative governance artifacts (must match across instances)**
- `governance_kernel.json` (kernel configuration)
- `governance/` manifests and policies referenced by the manifest loader
- `contracts/` governance contracts used by the loader
- Append-only governance ledger in `.echo/governance_ledger.jsonl`
- Integrity attestations in `attestations/` when tied to governance decisions

**Instance-local operational state (must not be blindly replicated)**
- Runtime logs (`logs/`, `logs/dispatcher.dlq`)
- Volatile caches and transient error queues
- Instance-specific secrets, environment variables, and credentials
- Local monitoring outputs and system telemetry

This boundary prevents non-authoritative runtime drift from being replayed as governance intent.

## Reference instance layout
Use the layout below to stand up a new instance without drifting governance semantics. Paths are relative to the repository root unless noted.

```
.
├── governance_kernel.json
├── governance/
├── contracts/
├── manifest/
├── attestations/
├── .echo/
│   └── governance_ledger.jsonl
├── logs/
│   └── dispatcher.dlq
└── docs/governance/kernel.md
```

## Federation readiness checks
Run these checks before federating or replicating a kernel instance. They are designed to prevent governance drift across instances.

1. **Kernel config parity**
   - Confirm `governance_kernel.json` is byte-identical across instances.
2. **Manifest + contract parity**
   - Ensure every file under `manifest/`, `governance/`, and `contracts/` is present with matching checksums.
3. **Ledger continuity**
   - Verify `.echo/governance_ledger.jsonl` is append-only and has the same latest integrity event hash on all instances.
4. **UQL enforcement sanity**
   - Confirm the `uql_enforcer` constraint sets and solver configuration match and that `reject_on_conflict` is still the fallback.
5. **State machine guard compliance**
   - Validate that the active state in each instance is derived from the same guard evaluation results (no local overrides).
6. **Attestation alignment**
   - Ensure governance decision attestations reference the same commit SHA and ledger event identifiers.

Only proceed with federation if all checks pass; otherwise, reconcile authoritative artifacts before replication.

## Initialization
- `GovernanceKernel` constructs with a ledger store (file-backed by default or in-memory for tests).
- An `INIT` event is recorded via `logEvent` and the SCI is computed using `computeSCI`.
- The kernel phase advances to `FUNCTIONAL` with a clean `volatileNotes` list.

## State Transitions
- **Change Requests**: When `submit` accepts a change request, a `CR_ACCEPTED` event is written, the SCI is recomputed, and the kernel remains `FUNCTIONAL`. If quorum is missing the kernel marks itself `DEGRADED` until new signers arrive.
- **Rituals**: `runRitual` delegates to the ritual engine. `RESET_EVENT` clears volatile state and reactivates the kernel. `UNITY_WEAVE` recalculates SCI and can degrade the kernel when the score is low. `THREAD_CLEANSE` prunes stale threads without affecting the functional phase.

## Ledger Integration
- Every significant transition writes an `IntegrityEvent` to the append-only ledger through the strong governance interface.
- Use `recentEvents(limit)` to inspect the latest activity or `getLedgerSlice` through the strong interface for structured consumption.
- `computeSCI` is deterministic for a given history, ensuring reproducible kernel health scoring.
