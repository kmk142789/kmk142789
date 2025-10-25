# Echo Habitat

Local multi-bot lab for creative coding, testing, and attestations. Start with Docker or local Python.

## Quick start
```bash
docker compose up --build
```

In another terminal:
```bash
python -m pip install -e .
python cli/habitat.py task codegen "Write a tiny poem about auroras"
```

Bots available: `codegen`, `tester`, `attestor`, `storyteller`.

## Bot Forge

The Bot Forge can mint specialised workers at runtime and register them with the
orchestrator. Spawn a new archetype from the CLI:

```bash
python cli/habitat.py forge spawn codesmith "Build a test harness for the new API"
```

The forge writes a trace bundle with logs and outputs under
`echo_habitat/forge/traces/` and reports activity to the Memory Nexus. Check the
live health of a forged worker and trigger auto-restarts when needed:

```bash
python cli/habitat.py forge health forge-codesmith-XXXXXX
```

## Extend with your own worker
Create a new folder under `workers/yourbot/__init__.py` and register a task:
```python
from .. import registry

@registry.task(name="workers.yourbot.run", queue="yourbot")
def run(spec: dict):
    # do magic, return dict
    return {"ok": True}
```

Add the queue name to `orchestrator/queue.py` and to the Celery worker command in `docker-compose.yml`.
