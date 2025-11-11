# Atlas OS Runbook

## Overview

Atlas OS is composed of modular services for scheduling, storage, networking, identity, and metrics. Each service can be run independently using the CLI or orchestrated through Docker Compose.

## Startup

1. Install Python dependencies: `pip install -r requirements.txt`.
2. Install dashboard dependencies: `cd dashboard && npm install`.
3. Launch the stack: `make up`.
4. Access the dashboard at `http://localhost:5173`.

## Maintenance

- **Scheduler**: Jobs are persisted in `data/scheduler.db`. Use `atlas schedule due` to inspect pending work.
- **Storage**: Receipts are stored in `data/last_receipt.json`. Drivers include memory, filesystem, and the vault adapter.
- **Network**: Node registry lives in `data/nodes.json`. Update weights with `atlas route set`.
- **Identity**: Issued credentials are cached in `data/last_credential.json`. DID documents are cached in `data/did_cache.json`.
- **Metrics & Observability**: Prometheus-compatible metrics at `http://localhost:9100/` and WebSocket updates at `ws://localhost:9101/`. Full OpenTelemetry wiring, dashboards, and alert procedures are documented in [`docs/observability.md`](observability.md).

## Recovery

- Restart services with `make run`.
- Clear scheduler backlog by truncating `data/scheduler.db`.
- Rotate identity keys with `atlas id issue --subject did:example:holder --claims '{"role":"reset"}'` to ensure new proofs are generated.
