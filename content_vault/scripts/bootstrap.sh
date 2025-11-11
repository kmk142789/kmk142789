#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

python - <<'PYTHON'
from pathlib import Path

required = [
    Path("configs/config.v2.json"),
    Path("schema/config.schema.json"),
    Path("src/vault_api/main.py"),
]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit(f"Missing required artefacts: {', '.join(missing)}")
print("Environment validated.")
PYTHON

python scripts/update_config_changelog.py

printf "Bootstrap complete. Run scripts/run_server.sh to start the API.\n"
