#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
export ATLAS_ROOT="$ROOT"
export ATLAS_CONFIG="$ROOT/config/atlas.yaml"

python -m atlas.core.runtime &
CORE_PID=$!
trap 'kill $CORE_PID >/dev/null 2>&1 || true' EXIT
sleep 2

pytest -q

curl -fsS http://localhost:9100/ || true

python -m compileall atlas
