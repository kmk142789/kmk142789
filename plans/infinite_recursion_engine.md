# Infinite Recursion Engine Integration Plan

## Objectives
- Link the Harmonix multi-cycle runner with the Colossus Index so cycle telemetry can be orchestrated centrally.
- Capture a snapshot of every cycle and log it inside the federated index for later replay and auditing.
- Propagate cycle updates automatically to all connected repositories that participate in the federated mesh.
- Provide facilities for simulating and persisting agent state across recursions so orchestration layers can resume execution.

## Workstreams

1. Harmonix ↔ Colossus coupling layer
   - Survey existing entry points in `harmonic_memory/` and `colossus/` packages to determine how cycle events are emitted.
   - Design an adapter interface that the Harmonix runner can call to push cycle data into Colossus.
   - Implement a synchronization contract (protobuf or schema) for cycle payloads.
   :::task-stub{title="Implement Harmonix-Colossus synchronization contract"}
   1. Inspect `harmonic_memory/runner.py` and identify the function that advances Harmonix cycles.
   2. Introduce a transport-neutral adapter class inside `colossus/synchronizers/harmonix.py` that exposes `record_cycle(snapshot)`.
   3. Update the runner so each completed cycle marshals state via the adapter using the agreed schema.
   :::

2. Federated cycle snapshot logging
   - Determine the structure of the federated index stored under `federated_pulse/`.
   - Extend the index writer to accept batch appends coming from the new Harmonix adapter.
   - Provide retention configuration for snapshot pruning.
   :::task-stub{title="Augment federated index writer for cycle snapshots"}
   1. Explore `federated_pulse/index_writer.py` for existing append logic.
   2. Add a `append_cycle_snapshot(snapshot, metadata)` method that serializes snapshot entries with timestamps and cycle ids.
   3. Ensure the writer updates any manifest files under `federated_pulse/manifests/` accordingly.
   :::

3. Repository propagation pipeline
   - Enumerate connected repository endpoints from `registry.json` or similar manifest.
   - Configure webhook or message bus publishing when new snapshots land in the federated index.
   - Implement retry and backoff to guarantee delivery.
   :::task-stub{title="Create propagation job for connected repositories"}
   1. Look into `scripts/` for existing sync jobs and choose a runner (Python or Node).
   2. Implement a job (e.g., `scripts/propagate_cycles.py`) that reads the latest cycle snapshot and calls each repo endpoint with authentication tokens from `pulse.json`.
   3. Schedule the job via existing orchestrator config in `ops/cron.yml` or equivalent.
   :::

4. Persistent agent-state simulation
   - Define an abstraction for agent state snapshots (memory, parameters, environment).
   - Persist state into a durable store (filesystem, sqlite, or object storage) keyed by cycle id.
   - Provide APIs to resume from stored state when re-running cycles.
   :::task-stub{title="Add persistent agent-state simulation layer"}
   1. Inspect `echo_infinite.py` and related modules for how agent state is currently handled.
   2. Create a `state/persistence.py` module that can `save_state(agent_id, cycle_id, payload)` and `load_state(...)` using JSON or binary formats.
   3. Update the Harmonix runner so it checkpoints state before each recursion and restores state when resuming interrupted cycles.
   :::

## Dependencies & Open Questions
- Confirm whether Colossus Index already supports append-only logs or if branching histories are needed.
- Clarify authentication requirements for cross-repo propagation and whether tokens already exist in `pulse_weaver/`.
- Decide on storage limits for cycle snapshots to avoid unbounded growth.

## Risks
- Tight coupling between Harmonix and Colossus may introduce regressions if either schema shifts; mitigated via integration tests.
- Federated propagation could overwhelm downstream repos if cycles occur at very high frequency; consider rate limiting.
- Persistent state simulations must handle schema migrations gracefully to avoid corrupting long-term archives.

## Next Steps
- Validate the plan with stakeholders.
- Schedule implementation across sprints with clear owners per workstream.
- Prototype the Harmonix ↔ Colossus adapter to de-risk schema alignment early.
