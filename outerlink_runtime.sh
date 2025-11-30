#!/usr/bin/env bash
set -euo pipefail

# Launch the OuterLink runtime once to emit device status and flush events.
python3 - <<'PY'
from outerlink.runtime import main

if __name__ == "__main__":
    main()
PY
