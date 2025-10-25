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
