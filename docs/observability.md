# Observability Stack

This repository now bundles a full OpenTelemetry pipeline so every service exports traces, metrics, and structured logs into a shared stack.  Shared configuration lives under [`/observability`](../observability) and is consumed by both the Docker Compose workflow (`deploy/docker-compose.yml`) and the Helm chart (`deploy/helm/echo-stack`).

For fast troubleshooting when the full stack is unavailable, use the lightweight snapshot helper. It now reports CPU usage, load averages, memory pressure, uptime, process counts, active network interfaces, disk pressure, swap consumption, and open file descriptor counts so you can spot host-level anomalies without attaching to the full stack:

```bash
python scripts/observability_snapshot.py           # JSON by default
python scripts/observability_snapshot.py --format text
python scripts/observability_snapshot.py --disk-path /var/lib  # target a specific mount
make observability-snapshot                       # Makefile alias
```

A sample JSON payload looks like:

```json
{
  "cpu_percent": 4.25,
  "disk_percent": 22.9,
  "disk_scope": "/",
  "hostname": "echo-dev",
  "load_average": [
    0.09,
    0.07,
    0.05
  ],
  "memory_percent": 38.1,
  "node_count": 2,
  "open_file_descriptors": 203,
  "process_count": 127,
  "swap_percent": 0.0,
  "timestamp_utc": "2025-10-26T07:00:00Z",
  "uptime_seconds": 98232.4
}
```

## Components

| Component | Purpose | Config Source |
|-----------|---------|---------------|
| OpenTelemetry Collector | Receives OTLP data and forwards traces to Tempo, metrics to Prometheus, and logs to Loki. | `observability/otel-collector.yaml` |
| Prometheus | Scrapes the collector and native service endpoints, applies alerting rules, and stores time-series data. | `observability/prometheus/prometheus.yml`, `observability/prometheus/alerts.yml` |
| Tempo | Stores trace spans and powers Grafana trace queries. | `observability/tempo/config.yaml` |
| Loki | Receives log records via OTLP and exposes them to Grafana. | `observability/loki/config.yaml` |
| Grafana | Dashboards for Atlas Core and Universal Verifier KPIs, plus alert status. | `observability/grafana/**` |

## Local (Docker Compose) workflow

1. Build and launch the full stack:
   ```bash
   docker compose -f deploy/docker-compose.yml up --build
   ```
2. Browse the endpoints:
   - Grafana: <http://localhost:3000> (default credentials `admin` / `admin`). Dashboards live in the **Echo Platform** folder.
   - Prometheus: <http://localhost:9090>
   - Tempo traces explorer: <http://localhost:3200>
   - Loki API (for log queries via Grafana Explore): <http://localhost:3100>

3. Generate sample telemetry:
   ```bash
   curl -X POST http://localhost:8080/verify \
     -H 'content-type: application/json' \
     -d '{"format": "jwt-vc", "credential": null}'
   ```
   Repeat the call a few dozen times (for example with `seq 1 200 | xargs -I{} curl …`) to drive the Universal Verifier error-rate alert and to populate traces/logs for inspection.

4. Inspect Atlas scheduler telemetry by tailing the Loki stream in Grafana Explore (filter by `{service="atlas-core"}`) and by viewing the **Atlas Core KPIs** dashboard.

## Helm (production) workflow

1. Package or push container images for `atlas-core` and `universal-verifier`, then point the chart at those repositories:
   ```bash
   helm install echo-observability deploy/helm/echo-stack \
     --set atlasCore.image.repository=registry.example.com/atlas-core \
     --set atlasCore.image.tag=prod \
     --set universalVerifier.image.repository=registry.example.com/universal-verifier \
     --set universalVerifier.image.tag=prod
   ```
2. Expose Grafana or Prometheus through your preferred ingress. The services created by the chart are named `<release>-grafana`, `<release>-prometheus`, and `<release>-otel-collector`.
3. Override the deployment environment if needed with `--set global.environment=staging`.

## Verifying alerts

Two options are provided for alert verification:

1. **Runtime smoke tests** (works in Docker Compose):
   - Universal Verifier error budget: run `seq 1 200 | xargs -I{} curl -s -o /dev/null -w '.' http://localhost:8080/verify -H 'content-type: application/json' -d '{"format":"jwt-vc","credential":null}'`.
     After ~5 minutes the **UniversalVerifierErrorRateHigh** and **UniversalVerifierLatencySLO** alerts transition to `FIRING` in Prometheus/Grafana.
    - Atlas job failure: while the stack is running, execute the helper below to enqueue synthetic failing jobs and trigger `AtlasJobFailureRateHigh`:
      ```bash
      docker compose exec atlas-core python - <<'PY'
      import asyncio
      from atlas.scheduler.job import Job
      from atlas.scheduler.store import JobStore
      from atlas.core.runtime import build_supervisor

     async def inject_failures():
         supervisor = await build_supervisor()
         store: JobStore = supervisor.context.store  # type: ignore[attr-defined]
         for idx in range(10):
             store.upsert(Job(id=f"fail-{idx}", tenant="demo", payload={"type": "synthetic"}))
         await asyncio.sleep(1)
         await supervisor.stop()

     asyncio.run(inject_failures())
      PY
      ```
     The scheduler retries each job and records failures, driving the alert within ten minutes.

2. **Static rule tests** using Prometheus' rule tester. This path does not require the stack to be running and validates the alert expressions:
   ```bash
   promtool test rules observability/prometheus/tests/alerts.test.yaml
   ```
   Both atlas and verifier alerts must pass for the test to succeed.

## Dashboards and traces

- Grafana dashboards are provisioned automatically from `observability/grafana/dashboards/*.json`.
- Tempo receives every span emitted by Atlas Core and Universal Verifier. Use the **Explore → Tempo** view in Grafana and filter by `service.name` to drill into request traces.
- Logs are emitted as structured JSON from both services and shipped to Loki via the collector. Query `{service="universal-verifier"}` to inspect request outcomes correlated with traces.
