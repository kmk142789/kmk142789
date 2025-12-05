# Governance Kernel Lifecycle

The governance kernel initializes with a deterministic state and immediately appends an `INIT` integrity event to the append-only ledger at `.echo/governance_ledger.jsonl`. The kernel maintains a `KernelState` object with a `phase`, current `sci` (sovereign confidence index), tracked `threads`, and the most recent change request ID.

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
