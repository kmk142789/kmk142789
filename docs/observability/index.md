# Observability Guide

The Echo observability stack surfaces telemetry from orchestrators, Fabric
peers, and generated artifacts. Use the following practices to maintain
operational awareness.

## Metrics

- **Prometheus scrapes** – Confirm every deployment exposes `/metrics` by using
  the annotations in `ops/unified_sentience_loop.yaml` and
  `ops/fabric-rollout-helm.yaml` as templates.
- **Dashboards** – The Pulse dashboard reads from the `PULSE_DASHBOARD_ROOT`
  path defined in service specs. Update the dashboards whenever a new metric or
  label is introduced.

## Logging

- Stream structured JSON logs to the Temporal Ledger sink, as configured in the
  Fabric Helm values file. Validate ingestion by tailing the ledger transport or
  by viewing the log shipping status indicators in the dashboard.
- Retain at least seven days of orchestrator logs under `/var/log/echo`. The
  `unified-sentience-loop` runbook includes rotation commands for large cycles.

## Alerting

- Configure warning alerts for CPU usage above 75% and for any orchestrator
  restart events inside a 30-second window.
- Page the on-call engineer when the Prometheus scrape status for a service is
  `down` for longer than two minutes.

## Tracing

- Distributed traces are optional today but the telemetry schema reserves the
  `orbital_hops` label to capture cross-region propagation should OpenTelemetry
  collectors be introduced.
