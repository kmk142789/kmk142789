#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${PACKAGE_ROOT}/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

cd "${REPO_ROOT}"
"${PYTHON_BIN}" "${PACKAGE_ROOT}/scripts/sync.py"
