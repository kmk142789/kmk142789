#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="packages/core/src:${PYTHONPATH-}"
python -m echo_evolver "$@"
