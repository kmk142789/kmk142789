#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

echo "[ECHOWORLD] Launching EchoWorld Bootstrap from Termux…"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ECHOWORLD] python3 not found. Please install Python in Termux." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

if ! python3 -m echo.echo_world_bootstrap --dry-run; then
  echo "[ECHOWORLD] Dry-run failed; aborting live launch." >&2
  exit 1
fi

python3 -m echo.echo_world_bootstrap
