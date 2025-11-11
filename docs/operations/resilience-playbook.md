# Resilience Verification & Remediation Playbook

This playbook connects the automated load and chaos verification suites to
operational responses when reliability guardrails are exceeded.

## Test sources

- **Load tests** (`tests/load/critical_endpoints_load_test.js`): executed via k6
  with p95 latency, error rate, and throughput SLO thresholds that reflect our
  contractual commitments for health, ledger, and analytics services.
- **Chaos experiments** (`tests/chaos/run_chaos.sh`): executes pod deletion and
  network latency scenarios to validate that self-healing controllers and
  defensive patterns recover within a configured timeout.

Both suites export structured JSON summaries that the CI pipeline uploads as
artifacts. They are consumable by downstream analytics or observability sinks.

## Failure response expectations

When an SLO threshold fails during CI (non-zero exit from the load test job or a
`status="failed"` entry in chaos results), the owning team must:

1. **Acknowledge** the failure within 15 minutes in the `#resilience-alerts`
   Slack channel.
2. **Triage** by reviewing the uploaded artifacts and correlating them with
   production telemetry (Grafana dashboards: _Pulse Gateway Latency_ and _Ledger
   Availability_).
3. **Mitigate** within 4 hours or open an incident ticket that documents the
   workaround and estimated fix window.
4. **Document** learnings in the `resilience` section of the service runbook and
   link to root-cause analysis once complete.

If remediation exceeds the 4 hour window, escalate to the Staff on-call engineer
and notify product leadership.

## Alerting integration

Prometheus alerts (see `ops/resilience-alerts.yaml`) forward to Alertmanager,
which is configured to route to PagerDuty (`Resilience Primary` schedule) and
Slack (`#resilience-alerts`). To extend notifications to other platforms add new
receivers to Alertmanager and reference them from the rules file. Make sure
Alertmanager secrets remain in the infrastructure repository rather than this
codebase.

### Alert creation checklist

- Ensure Prometheus is scraping the exporter that publishes load/chaos results.
- Deploy `ops/resilience-alerts.yaml` to the monitoring cluster.
- Confirm alerts fire in staging by forcing an SLO breach (e.g. set a low
  threshold or inject a failure) before enabling in production.

## Runbook updates

Service runbooks **must** include:

- Links to the latest load and chaos artifacts.
- Known-good recovery times for pod disruption and network impairment.
- Owners responsible for closing SLO regressions.

These expectations are reviewed during quarterly reliability audits.
