#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DEFAULT_OUT="${ROOT_DIR}/out/constellation/graph.json"

cd "${ROOT_DIR}"

python -m tools.echo_constellation.scan --roots "${ROOT_DIR}" --out "${DEFAULT_OUT}"

if [ -d "${ROOT_DIR}/viewer/constellation_app/public" ]; then
  cp "${DEFAULT_OUT}" "${ROOT_DIR}/viewer/constellation_app/public/graph.json"
fi

git add "${DEFAULT_OUT}"
if [ -d "${ROOT_DIR}/viewer/constellation_app/public" ]; then
  git add "${ROOT_DIR}/viewer/constellation_app/public/graph.json"
fi

if git diff --cached --quiet; then
  echo "No constellation changes detected; skipping commit." >&2
  exit 0
fi

git commit -m "chore(constellation): refresh graph"
