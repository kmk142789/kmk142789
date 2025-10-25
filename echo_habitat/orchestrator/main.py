from fastapi import FastAPI
from fastapi.responses import JSONResponse
from celery.result import AsyncResult

from .queue import app as celery
from .models import TaskSpec, TaskStatus

import uuid

api = FastAPI(title="Echo Habitat Orchestrator")


@api.post("/task")
def create_task(spec: TaskSpec):
    task_id = str(uuid.uuid4())
    res = celery.send_task(
        f"workers.{spec.kind}.run",
        kwargs={"spec": spec.model_dump()},
        queue=spec.kind,
    )
    return {"id": res.id, "accept": task_id}


@api.get("/task/{task_id}")
def get_task(task_id: str):
    r = AsyncResult(task_id, app=celery)
    out = TaskStatus(id=task_id, state=r.state)
    if r.ready():
        try:
            out.result = r.get(timeout=1)
        except Exception as e:  # noqa: BLE001
            out.result = {"error": str(e)}
    return JSONResponse(out.model_dump())


app = api
