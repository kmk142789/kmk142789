#!/usr/bin/env bash
set -euo pipefail

pushd "$(dirname "$0")/.." >/dev/null

python -m compileall atlas_kernel atlas_storage atlas_network atlas_runtime atlas_cli

if command -v npm >/dev/null; then
  pushd atlas_ui >/dev/null
  npm install
  npm run build
  popd >/dev/null
else
  echo "npm not available; skipping atlas_ui build" >&2
fi

popd >/dev/null
