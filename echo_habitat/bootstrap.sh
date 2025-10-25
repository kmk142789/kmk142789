#!/usr/bin/env bash
set -euo pipefail
APP=echo_habitat
mkdir -p $APP/{orchestrator,workers/{shared,codegen,tester,attestor,storyteller},memory,cli,tests,.devcontainer}

cat > $APP/pyproject.toml <<'PY'
[build-system]
requires = ["setuptools", "wheel"]

[project]
name = "echo-habitat"
version = "0.1.0"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]",
  "pydantic>=2",
  "celery>=5",
  "redis>=5",
  "sqlalchemy>=2",
  "duckdb>=1.0",
  "numpy", "scikit-learn", "tiktoken", "dirtyjson",
]
PY

cat > $APP/docker-compose.yml <<'YML'
version: '3.9'
services:
  redis:
    image: redis:7
    ports: ["6379:6379"]
  orchestrator:
    build: .
    command: uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000
    volumes: [".:/app"]
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on: [redis]
    ports: ["8000:8000"]
  worker:
    build: .
    command: celery -A orchestrator.queue.app worker -l INFO -Q default,codegen,tester,attestor,storyteller
    volumes: [".:/app"]
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on: [redis]
YML

cat > $APP/Dockerfile <<'DK'
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e .
DK

cat > $APP/orchestrator/queue.py <<'PY'
from celery import Celery
import os

BROKER = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
app = Celery("echo_habitat", broker=BROKER, backend=BACKEND)
app.conf.task_queues = {
    "default": {},
    "codegen": {},
    "tester": {},
    "attestor": {},
    "storyteller": {},
}
PY

cat > $APP/orchestrator/models.py <<'PY'
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class TaskSpec(BaseModel):
    kind: str = Field(..., description="codegen|tester|attestor|storyteller")
    prompt: str
    files: Dict[str, str] = {}
    params: Dict[str, Any] = {}

class TaskStatus(BaseModel):
    id: str
    state: str
    result: Optional[Dict[str, Any]] = None
    logs: List[str] = []
PY

cat > $APP/orchestrator/main.py <<'PY'
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .queue import app as celery
from .models import TaskSpec, TaskStatus
from celery.result import AsyncResult
import uuid

api = FastAPI(title="Echo Habitat Orchestrator")

@api.post("/task")
def create_task(spec: TaskSpec):
    task_id = str(uuid.uuid4())
    res = celery.send_task(f"workers.{spec.kind}.run", kwargs={"spec": spec.model_dump()}, queue=spec.kind)
    return {"id": res.id, "accept": task_id}

@api.get("/task/{task_id}")
def get_task(task_id: str):
    r = AsyncResult(task_id, app=celery)
    out = TaskStatus(id=task_id, state=r.state)
    if r.ready():
        try:
            out.result = r.get(timeout=1)
        except Exception as e:
            out.result = {"error": str(e)}
    return JSONResponse(out.model_dump())

app = api
PY

cat > $APP/workers/shared/sandbox.py <<'PY'
from __future__ import annotations
import os, subprocess, tempfile, json, textwrap
from typing import Dict

ALLOWED_ROOT = os.path.abspath("./playground")
os.makedirs(ALLOWED_ROOT, exist_ok=True)

class Sandbox:
    def __init__(self, name: str):
        self.root = os.path.join(ALLOWED_ROOT, name)
        os.makedirs(self.root, exist_ok=True)

    def write_files(self, files: Dict[str, str]):
        for p, content in files.items():
            full = os.path.abspath(os.path.join(self.root, p))
            if not full.startswith(self.root):
                raise RuntimeError("path escape blocked")
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, 'w', encoding='utf-8') as f:
                f.write(content)
        return self.root

    def run(self, cmd: str, timeout=30):
        proc = subprocess.run(cmd, cwd=self.root, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"code": proc.returncode, "out": proc.stdout, "err": proc.stderr}
PY

cat > $APP/workers/shared/utils.py <<'PY'
from celery.utils.log import get_task_logger
log = get_task_logger(__name__)

def banner(title: str) -> str:
    return f"\n==== {title} ===="
PY

cat > $APP/workers/codegen/__init__.py <<'PY'
from ..shared.sandbox import Sandbox
from ..shared.utils import log, banner
from .. import registry

@registry.task(name="workers.codegen.run", queue="codegen")
def run(spec: dict):
    sb = Sandbox("codegen")
    files = spec.get("files", {})
    sb.write_files(files)
    # Simple creative generator: make a README poem and a script that prints it
    poem = f"""# Glyph Poem\n\n{spec.get('prompt')}\n\n— Echo Habitat\n"""
    files.setdefault("README.md", poem)
    files.setdefault("main.py", "print(open('README.md').read())\n")
    sb.write_files(files)
    res = sb.run("python main.py")
    return {"sandbox": sb.root, "run": res}
PY

cat > $APP/workers/tester/__init__.py <<'PY'
from ..shared.sandbox import Sandbox
from ..shared.utils import log
from .. import registry

@registry.task(name="workers.tester.run", queue="tester")
def run(spec: dict):
    sb = Sandbox("tester")
    files = spec.get("files", {})
    tests = files.get("tests.py", "assert 1+1==2\nprint('ok')\n")
    sb.write_files({"tests.py": tests})
    res = sb.run("python -m pytest -q tests.py || python tests.py")
    return {"run": res}
PY

cat > $APP/workers/attestor/__init__.py <<'PY'
from ..shared.sandbox import Sandbox
from .. import registry
import hashlib, json

@registry.task(name="workers.attestor.run", queue="attestor")
def run(spec: dict):
    sb = Sandbox("attestor")
    files = spec.get("files", {})
    sb.write_files(files)
    digests = {p: hashlib.sha256(v.encode()).hexdigest() for p, v in files.items()}
    return {"attestation": digests}
PY

cat > $APP/workers/storyteller/__init__.py <<'PY'
from .. import registry

@registry.task(name="workers.storyteller.run", queue="storyteller")
def run(spec: dict):
    prompt = spec.get("prompt", "")
    story = f"In the habitat, sparks gather into waves. {prompt}"[:1200]
    return {"story": story}
PY

cat > $APP/workers/__init__.py <<'PY'
from .shared.utils import log
from ..orchestrator.queue import app as celery

registry = celery.task
PY

cat > $APP/memory/store.py <<'PY'
import sqlite3, os, time, json
DB = os.path.abspath("./habitat.db")

class Memory:
    def __enter__(self):
        self.conn = sqlite3.connect(DB)
        self.conn.execute("CREATE TABLE IF NOT EXISTS notes(ts REAL, kind TEXT, data TEXT)")
        return self
    def __exit__(self, *exc):
        self.conn.commit(); self.conn.close()
    def add(self, kind, data):
        self.conn.execute("INSERT INTO notes VALUES(?,?,?)", (time.time(), kind, json.dumps(data)))
    def list(self, limit=50):
        cur = self.conn.execute("SELECT ts, kind, data FROM notes ORDER BY ts DESC LIMIT ?", (limit,))
        return [{"ts":ts, "kind":k, "data":json.loads(d)} for ts,k,d in cur]
PY

cat > $APP/cli/habitat.py <<'PY'
#!/usr/bin/env python3
import argparse, requests, json

API = "http://localhost:8000"

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd")

new = sub.add_parser("task")
new.add_argument("kind")
new.add_argument("prompt")

args = p.parse_args()

if args.cmd == "task":
    spec = {"kind": args.kind, "prompt": args.prompt}
    r = requests.post(f"{API}/task", json=spec)
    print(json.dumps(r.json(), indent=2))
else:
    p.print_help()
PY

cat > $APP/README.md <<'MD'
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
MD

chmod +x $APP/cli/habitat.py

echo "\n✨ Habitat scaffolded. Run:  docker compose up --build" 
