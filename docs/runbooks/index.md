# Runbook Collection

This runbook suite captures the operational flows for the Echo platform. Each
procedure is designed for repeatability and can be executed by any on-call
engineer with access to the shared tooling scripts in `scripts/` and the
observability dashboards referenced below.

## Unified Sentience Loop

1. **Prepare the workspace** – Ensure `/var/lib/echo` has at least 10 GiB of
   free disk space and that the `cycle_orchestrator.py` script is present.
2. **Launch the orchestrator** – Execute `python scripts/cycle_orchestrator.py
   --cycle <id> --output-root /var/lib/echo/build/cycles`.
3. **Verify outputs** – Confirm the tarball `cycle-<id>.tgz` is created under
   `/var/lib/echo/out` and attached to the release artifact for that cycle.

## Fabric Consensus Peer

1. **Chart preparation** – Update the Helm values in
   `ops/fabric-rollout-helm.yaml` with the appropriate storage class and
   metrics endpoint.
2. **Deploy** – Run `helm upgrade --install fabric ./charts/federation -f
   ops/fabric-rollout-helm.yaml` from the deployment host.
3. **Post-deploy checks** – Use `kubectl logs` to validate pod health and watch
   the Prometheus scrape endpoint at `:9443/metrics` for cluster registration.

## Artifact Publishing

1. **Generate documentation** – Run `python scripts/generate_doc_assets.py`
   followed by `mkdocs build`.
2. **Bundle outputs** – Compress the `site/` directory and upload the archive
   alongside release artifacts.
3. **Record state** – Update `docs/runbooks/index.md` with any deviations or
   lessons learned from the procedure.
