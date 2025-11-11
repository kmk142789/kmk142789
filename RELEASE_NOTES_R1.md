# Release R1 — v0.1.0

## Summary
- Unified the compliance engine with Atlas through the new Identity Bridge job that emits reports and highlights.
- Introduced an Atlas metrics service to capture counters and durations for compliance workflows.
- Automated the release path with a dedicated GitHub Actions workflow and Make targets that build, test, and publish documentation.

## Installation & Environment
1. `python -m pip install --upgrade pip`
2. `pip install -r requirements.txt`
3. `pip install -e .[dev]`
4. `pip install mkdocs mkdocs-material` (only required when generating docs locally)

## Running the Release Pipeline
1. Execute `make release-r1` to build the package, run tests, execute e2e identity verification, generate documentation, and emit compliance artifacts.
2. Inspect the generated compliance report at `reports/compliance/atlas_compliance_report.json` and the metrics snapshot at `reports/compliance/atlas_metrics.json`.
3. Review the static documentation site produced at `reports/site`.

## Artifacts
- `dist/` — Python distribution created via `python -m build`.
- `reports/compliance/atlas_compliance_report.json` — Structured compliance output for Atlas ingestion.
- `reports/compliance/atlas_metrics.json` — Metrics counters and timings for observability.
- `reports/site` — MkDocs site suitable for publishing.

## Next Milestones
- Expand Atlas job catalog with additional compliance detectors (Release R2 planning).
- Integrate Atlas metrics into dashboard visualisations for live monitoring.
- Harden telemetry pipelines with automated consent anomaly remediation.
