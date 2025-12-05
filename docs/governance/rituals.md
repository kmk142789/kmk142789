# Governance Rituals

The ritual engine orchestrates deterministic governance routines that adjust kernel health and ledger state.

## Rituals
- **RESET_EVENT**: Clears volatile notes and threads, logs a `RESET_EVENT`, and returns the kernel to `FUNCTIONAL` phase after the reset step.
- **UNITY_WEAVE**: Recomputes the SCI using the current ledger history. If the score drops below `0.5`, the kernel enters `DEGRADED`; otherwise it remains `FUNCTIONAL`. A `UNITY_WEAVE` event is logged with the recalculated SCI.
- **THREAD_CLEANSE**: Removes threads marked as `stale` and logs the number of remaining threads in a `THREAD_CLEANSE` event.

## Invocation
Rituals are executed through `GovernanceKernel.runRitual` or directly via the `StrongGovernanceAPI.performRitual` facade. Each ritual returns a new `KernelState` snapshot, enabling pure functional testing.

## Expected State Transitions
- `RESET_EVENT`: `FUNCTIONAL` → `RESET` (cleared) → `FUNCTIONAL`.
- `UNITY_WEAVE`: Evaluates SCI and toggles between `FUNCTIONAL` and `DEGRADED`.
- `THREAD_CLEANSE`: Maintains the current phase while pruning stale threads.
