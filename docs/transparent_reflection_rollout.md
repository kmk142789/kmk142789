# Transparent Reflection Layer Rollout Guide

## Overview

The Transparent Reflection Layer introduces a shared `/reflection` endpoint across CLI,
services, and dashboard tooling. Follow the checklist below to deploy the v1 release.

## Prerequisites

1. Build images with the new reflection module:
   ```bash
   docker compose -f docker-compose.federation.yml build reflection
   ```
2. Ensure environment variables include `REFLECTION_LAYER_ENABLED=true` for the reflection
   service (already present in the compose file).

## Deployment Steps

1. **Bootstrap telemetry storage**
   * Confirm `state/pulse_dashboard/worker_events.jsonl` is writable on the target host.
   * Optionally point `TransparentReflectionLayer` to a consent-approved telemetry
     collector before enabling remote forwarding.
2. **Launch the reflection service**
   ```bash
   docker compose -f docker-compose.federation.yml up -d reflection
   ```
   This exposes the `/reflection` endpoint on port `8400`.
3. **Verify safeguards**
   * Run `pytest tests/test_transparent_reflection_layer.py::test_universal_verifier_reflection_endpoint_reports_metrics`
     to validate endpoint responses and safeguard declarations.
   * Inspect `reports/data/reflection_transparency.json` after running the diagnostics
     pipeline to confirm aggregated metrics.
4. **Document operational ownership**
   * Record the deployment timestamp and operator in the observability runbook.
   * Notify downstream teams that reflection snapshots are available at `/reflection`.

## Rollback Plan

1. Stop the reflection service: `docker compose -f docker-compose.federation.yml stop reflection`.
2. Remove any generated JSON reports if they contain inaccurate diagnostics.
3. Revert to the previous Git commit and redeploy the baseline stack.

## Monitoring Checklist

* Watch the aggregated metrics emitted by `build_reflection_report` for unexpected spikes
  in `requests_failed` or missing safeguards.
* Confirm Worker Hive logs continue to append `"status": "reflection"` entries after CLI
  operations.
* Track telemetry consent compliance when forwarding reflection events to external sinks.
