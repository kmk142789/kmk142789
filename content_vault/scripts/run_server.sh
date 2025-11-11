#!/usr/bin/env bash
set -euo pipefail

export VAULT_CONFIG_PATH="${VAULT_CONFIG_PATH:-$(pwd)/configs/config.v2.json}"
python -m vault_api.main
