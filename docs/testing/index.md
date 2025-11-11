# Testing Instructions

Follow these workflows to validate the Echo platform before each release.

## Automated Checks

1. **Unit tests** – Run `pytest` from the repository root to execute the fast
   verification suite.
2. **Generated client smoke tests** – After running
   `python scripts/generate_clients.py`, execute
   `pytest tests/test_generated_clients.py -k smoke`.
3. **Documentation build** – Invoke `python scripts/generate_doc_assets.py` and
   then `mkdocs build` to ensure reference integrity.

## Manual Validation

1. **Pulse dashboard review** – Confirm the most recent orchestrator cycle is
   visible and that the metrics charts load without missing data points.
2. **API contract review** – Inspect `docs/generated/api_index.md` for breaking
   changes. Diff the file between releases to confirm endpoint stability.
3. **Service dependency spot check** – Render the Mermaid graph in the docs site
   to confirm new services are represented and their dependencies are correct.

## Release Gate

A release can ship only when all automated checks pass and manual validation is
recorded in the release notes. Capture any follow-up actions in the runbook
section to close the loop with operations.
