# EchoField SwarmKit

EchoField SwarmKit is an offline-first swarm coordination and self-healing agent designed for fleets that operate in harsh or disconnected environments. Each node runs a lightweight agent that collaborates with nearby peers, shares health telemetry, and executes safe remediation steps even without internet access. When connectivity returns, nodes automatically reconcile their task ledgers using conflict-free rules.

## Features
- **Swarm gossip sync:** Exchange tasks and node health summaries over any transport (file drop, HTTP, sneaker-net) with deterministic merge semantics.
- **Task ledger:** CRDT-inspired task versions ensure the freshest update wins while keeping history on disk.
- **Geek Squad health engine:** Periodic health checks emit remediation tasks and update the node health summary.
- **Node agent loop:** Runs health cycles, executes local tasks, and syncs with peers on timers.
- **CLI:** Start the node agent or run a single health check cycle for quick diagnostics.
- **Offline hardening:** Atomic snapshot writes, stale-peer guarding, and automatic peer discovery keep file-drop gossip resilient when connectivity is sparse.

## Quick start
1. Adjust `echo_config.yaml` to set node identity, storage paths, and sync settings.
2. Install dependencies (Python 3.10+):
   ```bash
   pip install -r requirements.txt
   ```
3. Run a node in demo file-sync mode:
   ```bash
   python -m echo_field_swarmkit.cli --node-id node-a --sync-path /tmp/swarm_sync --health-interval 30 --sync-interval 10
   ```
4. Start another node pointing to the same `--sync-path` to watch gossip exchanges happen offline.

## Architecture
- `echo_node.py`: Main agent loop that coordinates health checks, task execution, and peer synchronization.
- `swarm_protocol.py`: Stateless gossip-style protocol that exports and merges task and node state snapshots.
- `task_ledger.py`: Task data model and helpers for creating new tasks.
- `health_engine.py`: Offline “Geek Squad” that emits remediation tasks based on local health signals.
- `storage.py`: Durable storage for tasks and node state using JSON on disk.
- `cli.py`: CLI entrypoint to start the agent or run one-off cycles.

## Safety notes
The default task handlers perform conservative actions and mark tasks as failed when unsupported. Extend `_handle_task` in `echo_node.py` with device-specific remediation steps (e.g., restarting services) after validating them in your environment.
