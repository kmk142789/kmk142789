# End-to-End and Contract Testing Guide

This guide covers how to run the full-stack end-to-end (E2E) scenarios and the OpenAPI contract checks that keep the generated SDKs aligned with the specification.

## Prerequisites

- **Docker** with the Compose plugin (`docker compose` must be available on your `PATH`).
- **Python 3.11+** with `pip` to install the project dependencies from `requirements.txt`.
- **Node.js** (optional) if you plan to re-build the TypeScript client while debugging.
- **Kind** and **kubectl** (optional) if you prefer to run the stack inside a local Kubernetes cluster instead of Docker Compose.

Install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Running the full E2E suite

The orchestrator lives at `tests/e2e/runner.py`. It provisions the stack, waits for the public API to come online, runs the scenario-driven tests, and archives logs and traces into `artifacts/e2e/`.

```bash
python -m tests.e2e.runner \
  --stack compose \
  --compose-file docker-compose.federation.yml
```

Key options:

- `--compose-build` – rebuild images before the run.
- `--scenario-dir` – point to an alternative directory of scenario JSON files.
- `--artifact-dir` – customize where run artifacts land. By default they are timestamped inside `artifacts/e2e/`.
- `--timeout` – increase the readiness timeout if you are running on slower hardware.

### Using Kind instead of Compose

Provide the `--stack kind` flag. By default the runner reuses or creates a cluster named `echo-e2e`. You can optionally supply a manifest to deploy your services:

```bash
python -m tests.e2e.runner \
  --stack kind \
  --kind-manifest ops/unified_sentience_loop.yaml
```

Set `--keep-kind` if you want to keep the cluster alive after the test run for additional debugging.

## Debugging scenarios

Scenario definitions live in `tests/e2e/scenarios/` and are expressed as JSON. Each scenario provides a `base_url` and an ordered list of HTTP steps. During a run the harness records both a structured result (`*_results.json`) and metadata (`*_metadata.json`) for every scenario inside the artifact directory.

Helpful overrides:

- `E2E_BASE_URL` – force every scenario to target a single base URL.
- `E2E_BASE_URL_<SCENARIO_NAME>` – override the base URL for a single scenario (the name is upper-cased with dashes replaced by underscores).
- `pytest` arguments – pass extra flags to the runner after `--` to run a single scenario, e.g. `python -m tests.e2e.runner -- --maxfail=1 -k continuum_agent`.

Inspect the generated artifacts to review request latency, response headers, and trimmed response bodies. The Compose stack logs are saved as `compose.log` alongside the results, while Kind deployments capture `kubectl get all -A` output.

## OpenAPI contract tests

Contract checks live in `tests/contract/test_openapi_clients.py`. They guarantee that:

- The Python, TypeScript, and Go SDKs all expose the same fields that the OpenAPI schema defines.
- Client classes include methods for every operation in the spec.

Run them directly via `pytest`:

```bash
pytest tests/contract/test_openapi_clients.py
```

Because the contract tests operate purely on source files, they do not require any running services.

## Troubleshooting tips

- If Docker services fail to start, inspect `artifacts/e2e/<timestamp>/compose.log` for container errors.
- When debugging responses, rerun the runner with `--timeout` to give slower services additional warm-up time.
- Use `docker compose ps -a` (or `kubectl get pods -A`) after a failure—the runner leaves the stack up until teardown, so you can investigate in another terminal before it stops.
- For iterative development, run `pytest tests/e2e/test_scenarios.py -k <name>` without the orchestrator to exercise scenarios against an already running stack.
