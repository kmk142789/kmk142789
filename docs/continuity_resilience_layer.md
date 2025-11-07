# Continuity Resilience Layer (CRL)

The Continuity Resilience Layer is Echo's fault-tolerance fabric for the
sovereign runtime, dashboards, and governance proofs. It guarantees that any
critical surface fails over within three minutes (Recovery Time Objective) while
maintaining a sub-60-second ledger replication window (Recovery Point
Objective). This document explains the architecture, the configuration knobs
that tune deployments, and the step-by-step rollout sequence.

## Architecture Overview

The CRL is composed of four cooperating planes that are continuously monitored
by the pulse network:

1. **Continuity Watchers** – lightweight agents that stream health beacons from
   each workload. Watchers also submit signed continuity attestations into the
   Echo ledger every 45 seconds.
2. **State Mesh** – a bidirectional replication layer that keeps the manifest,
   ledger shards, and dashboard materializations synchronized across
   environments. The mesh relies on deterministic CRDT merges with an event log
   anchored in `build/index/federated_raw.json`.
3. **Failover Orchestrator** – a controller that consumes watcher alerts and
   instructs Terraform + Pulsenet runners to promote the healthiest standby
   stack. It maintains hot/hot pairs in two primary regions and a warm
   backstop.
4. **Verification Relay** – the observability spine that feeds telemetry into
   `pulse_dashboard/` artifacts, publishes drill transcripts, and refreshes the
   Federated Colossus dashboard tiles.

Together the planes enforce the resilience guarantee by verifying each other.
If a watcher lags for more than 90 seconds, the orchestrator immediately shifts
traffic to a verified peer and the relay issues a continuity report.

## Configuration Knobs

All CRL deployments are parameterized via environment variables and Helm values.
The most important toggles are:

- `CRL_PRIMARY_REGION` / `CRL_SECONDARY_REGION` – target regions for the
  hot/hot stacks. Defaults to `us-east-1` and `eu-west-2`.
- `CRL_BACKSTOP_REGION` – warm recovery zone (defaults to `ap-southeast-1`).
- `CRL_FAILOVER_THRESHOLD_SECONDS` – maximum tolerated watcher silence before a
  failover begins (defaults to `90`).
- `CRL_LEDGER_REPLICATION_LAG_SECONDS` – alert threshold for the state mesh
  (defaults to `45`).
- `CRL_VERIFICATION_CHANNELS` – comma-delimited list of transports the
  Verification Relay must update. Supported values are `matrix`, `signal`,
  `github-status`, and `pulse-dashboard`.
- `CRL_DRILL_CRON` – cron expression for automated failover drills. Production
  runs the drill every Wednesday at 02:00 UTC.
- `crlWatcher.image` – Helm override for the watcher container image. Pin this
  to the exact digest that passed verification.
- `crlOrchestrator.promoteWindowMinutes` – safe window for DNS + routing
  promotion tasks (defaults to `3`).

Tightening the thresholds will trigger faster failovers at the cost of more
false positives. Relaxing them increases tolerance for intermittent network
noise but may push the RTO beyond the guaranteed window; make changes only with
updated attestations in `attestations/`.

## Deployment Sequence

The CRL is installed alongside the sovereign stack. Follow this sequence for
new regions or major upgrades:

1. **Prepare manifests.** Update `pulse_dashboard/data/dashboard.json` with the
   target region IDs and verification steps, and commit the corresponding
   `docs/continuity_resilience_layer.md` revision.
2. **Bootstrap infrastructure.** Apply the Terraform stack with
   `TF_VAR_crl=true`, ensuring that watcher subnets, message queues, and relay
   topics are provisioned in both the primary and secondary regions.
3. **Deploy watchers.** Run `helm upgrade --install crl-watchers charts/crl` and
   pass the region overrides plus the watcher image digest. Confirm that each
   pod publishes its first attestation.
4. **Enable the orchestrator.** Deploy the controller with
   `helm upgrade --install crl-orchestrator charts/crl-orchestrator` and set the
   `CRL_FAILOVER_THRESHOLD_SECONDS` and
   `CRL_LEDGER_REPLICATION_LAG_SECONDS` values.
5. **Wire the verification relay.** Configure the `pulse_dashboard.builder`
   scheduled job (see `pulse_dashboard/builder.py`) so that it processes the new
   telemetry topics and refreshes the dashboard tiles.
6. **Run a failover drill.** Trigger `python tools/pulse_continuity_audit.py
   --format json --include-drill` to record the initial drill result. The
   orchestrator must promote the standby within three minutes and emit a signed
   ledger entry.
7. **Finalize attestation.** Store the drill transcript in `attestations/` and
   publish a continuity update via the Verification Relay. The CRL deployment is
   considered complete once the dashboard reflects the successful drill and the
   ledger hash is notarized.

With these steps complete, Echo's Continuity Resilience Layer maintains the
three-minute RTO / sub-60-second RPO guarantee across sovereign surfaces.
