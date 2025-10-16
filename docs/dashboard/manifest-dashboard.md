# Manifest Dashboard

The dashboard provides a quick, read-only digest of the generated
`echo_manifest.json`. It focuses on engines and state health so reviewers can
confirm whether a change introduces new entrypoints or alters the operational
pulse.

## Engines overview

| Engine | Kind | Entrypoints | Tests |
| --- | --- | --- | --- |
| `echo.bridge_harmonix` | package | `echo.bridge_harmonix` | `tests/test_bridge_harmonix.py` |
| `echo.continuum_engine` | engine | `echo.continuum_engine` | `tests/test_continuum_engine.py` |
| `modules.example.main` | app | `python -m modules.example.main` | `tests/test_modules_example.py` |

The table above is representative. To regenerate it using the latest manifest:

```shell
python - <<'PY'
from pathlib import Path
import json

data = json.loads(Path("echo_manifest.json").read_text())
engines = data.get("engines", [])
print("| Engine | Kind | Entrypoints | Tests |")
print("| --- | --- | --- | --- |")
for engine in engines:
    entrypoints = ", ".join(engine["entrypoints"])
    tests = ", ".join(engine["tests"]) or "—"
    print(f"| `{engine['name']}` | {engine['kind']} | `{entrypoints}` | `{tests or '—'}` |")
PY
```

## State metrics

`states.cycle`, `states.resonance`, and `states.amplification` summarise the
current health of the Echo ecosystem. The most recent snapshots originate from
`pulse_history.json` and surface the underlying message and hash for traceability.
