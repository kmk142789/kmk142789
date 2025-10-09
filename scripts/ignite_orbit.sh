#!/usr/bin/env bash
set -euo pipefail
# Simple helper to spin the orbital loop with sane defaults.
# Usage: ./scripts/ignite_orbit.sh [period_seconds] [max_cycles]
PERIOD="${1:-12}"
MAX="${2:-}"
if [[ -n "$MAX" ]]; then
  python -m echo.orbital_loop ignite --period "$PERIOD" --max-cycles "$MAX"
else
  python -m echo.orbital_loop ignite --period "$PERIOD"
fi
