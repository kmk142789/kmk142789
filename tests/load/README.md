# Load Testing Suite

This directory contains [k6](https://k6.io/) scenarios that exercise the platform's
highest risk API surfaces under realistic concurrency.

## Contents

- `critical_endpoints_load_test.js` – drives health, ledger, and analytics endpoints
  with sustained arrival rates and SLO-aligned thresholds. The script exports a
  JSON summary in `tests/load/results/critical-endpoints-summary.json` after each run.
- `results/` – populated automatically with run artifacts suitable for CI upload
  and historical comparisons.

## Running locally

```bash
npm install --global k6 # or use a container image
export LOAD_TEST_BASE_URL="https://example.com"
export LOAD_TEST_AUTH_TOKEN="<optional bearer token>"
./tests/load/run_load_tests.sh
```

### SLO thresholds

The default service level objectives enforced in the script are:

| Scenario | p95 latency | Error rate | Minimum throughput |
|----------|-------------|------------|--------------------|
| Health   | `< 400ms`   | `< 1%`     | `> 25 req/s`       |
| Ledger   | `< 550ms`   | `< 1%`     | `> 18 req/s`       |
| Analytics| `< 600ms`   | `< 1.5%`   | `> 10 req/s`       |

Update these thresholds if product SLOs change.

## Exports

Use the `--summary-export` flag (already included in `run_load_tests.sh`) or the
custom `handleSummary` hook to persist structured output for observability pipelines.
