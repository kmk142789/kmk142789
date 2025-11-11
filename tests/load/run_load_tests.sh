#!/usr/bin/env bash
set -euo pipefail

RESULT_DIR=${RESULT_DIR:-tests/load/results}
SUMMARY_EXPORT="${RESULT_DIR}/k6-summary.json"

mkdir -p "${RESULT_DIR}"

if ! command -v k6 >/dev/null 2>&1; then
  cat <<JSON >"${SUMMARY_EXPORT}"
{
  "status": "skipped",
  "reason": "k6 binary not found in PATH"
}
JSON
  echo "k6 not available; skipping load tests" >&2
  exit 0
fi

if [[ -z "${LOAD_TEST_BASE_URL:-}" ]]; then
  cat <<JSON >"${SUMMARY_EXPORT}"
{
  "status": "skipped",
  "reason": "LOAD_TEST_BASE_URL is not configured"
}
JSON
  echo "LOAD_TEST_BASE_URL not set; skipping load tests" >&2
  exit 0
fi

set +e
k6 run \
  --summary-export "${SUMMARY_EXPORT}" \
  tests/load/critical_endpoints_load_test.js
rc=$?
set -e

if [[ $rc -ne 0 ]]; then
  echo "k6 run exited with status ${rc}" >&2
fi

exit $rc
