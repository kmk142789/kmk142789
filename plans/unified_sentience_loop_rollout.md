# Unified Sentience Loop Rollout Plan

## Overview
The Unified Sentience Loop packages the cycle orchestrator into a managed
service and wires its telemetry into the Pulse dashboard. This plan outlines
how to roll the service into staging and production while ensuring loop health
is observable end-to-end.

## Prerequisites
- Container image or virtualenv containing the repository at `/opt/echo`.
- Access to the federation Kubernetes cluster or process supervisor.
- Prometheus scrape configuration capable of ingesting local metrics at
  `http://127.0.0.1:9410/metrics`.
- GitHub Actions secrets for artifact upload already configured.

## Deployment Steps
1. **Bootstrap filesystem**
   - `mkdir -p /var/lib/echo/build/cycles /var/lib/echo/out /var/log/echo`.
   - Ensure the service account `echo` owns the directories.
2. **Install service definition**
   - Apply `ops/unified_sentience_loop.yaml` to the runtime supervisor.
   - Override `CYCLE_ID` via environment, config map, or runtime argument as
     needed for staged cycles.
3. **Dry-run orchestration**
   - Execute `/usr/bin/env python3 /opt/echo/scripts/cycle_orchestrator.py --cycle 1 --output-root /var/lib/echo/build/cycles --no-federate`.
   - Confirm artifacts land in `/var/lib/echo/build/cycles/cycle_00001` and
     telemetry logs appear under `/var/lib/echo/build/cycles/cycle_00001/logs`.
4. **Enable metrics shipping**
   - Point Prometheus to scrape the loop metrics endpoint on port `9410`.
   - Validate the Pulse dashboard reflects `loop_health` updates after the dry
     run by running `python -m pulse_dashboard.builder` locally or via CI.
5. **Activate CI pipeline**
   - Merge the updated `.github/workflows/echo-ci.yml` configuration.
   - Monitor the `smoke-package` job for successful smoke tests and artifact
     bundle uploads.
6. **Promote to production**
   - Remove `--no-federate` from the runtime command when ready for canonical
     federation writes.
   - Configure rotation for `/var/log/echo/unified-sentience-loop.log` and the
     packaged tarballs in `/var/lib/echo/out`.

## Rollback
- Stop the `unified-sentience-loop` service in the supervisor.
- Remove the cycle directories created during the rollout if they are not
  needed for audit purposes.
- Revert `.github/workflows/echo-ci.yml` if the smoke-package job must be
  disabled temporarily.
