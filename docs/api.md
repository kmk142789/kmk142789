# Atlas OS API Routes

## Metrics
- `GET /metrics` – Prometheus exposition.
- `WS /metrics` – WebSocket stream of metric snapshots.

## Scheduler
- `GET /api/scheduler/due` – Returns due jobs as JSON.
- `POST /api/scheduler/jobs` – Enqueue a new job payload.

## Storage
- `POST /api/storage/{driver}` – Store content, returns receipt.
- `GET /api/storage/{driver}` – Retrieve content by receipt.

## Network
- `GET /api/nodes` – Node registry listing.
- `POST /api/nodes` – Register a node.
- `POST /api/routes` – Update link weights.

## Identity
- `POST /api/credentials` – Issue a new credential.
- `POST /api/credentials/verify` – Verify a credential payload.

All APIs return JSON responses and expect deterministic configuration values sourced from environment variables and `atlas.yaml`.
