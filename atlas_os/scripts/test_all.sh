#!/usr/bin/env bash
set -euo pipefail

pushd "$(dirname "$0")/.." >/dev/null

pytest atlas_kernel/tests atlas_storage/tests atlas_network/tests atlas_runtime/tests

popd >/dev/null
