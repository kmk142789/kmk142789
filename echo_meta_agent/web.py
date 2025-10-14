"""FastAPI application exposing the Echo Meta Agent."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .agent import EchoAgent
from .memory import find as memory_find
from .memory import last as memory_last

app = FastAPI(title="Echo Meta Agent", version="0.1.0")
_agent = EchoAgent()


class CallRequest(BaseModel):
    plugin: str
    tool: str
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
def health() -> Dict[str, bool]:
    return {"ok": True}


@app.get("/plugins")
def list_plugins() -> List[str]:
    return _agent.registry.list_plugins()


@app.get("/plugins/{name}/tools")
def list_plugin_tools(name: str) -> List[str]:
    try:
        return _agent.registry.list_tools(name)
    except KeyError as exc:  # pragma: no cover - handled via HTTPException
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/call")
def call(request: CallRequest) -> Dict[str, Any]:
    return _agent.execute(request.plugin, request.tool, *request.args, **request.kwargs)


@app.get("/memory/last")
def memory_last_endpoint(n: int = Query(default=20, ge=1, le=200)) -> List[Dict[str, Any]]:
    return memory_last(n)


@app.get("/memory/find")
def memory_find_endpoint(q: str = Query(..., min_length=1), limit: int = Query(default=20, ge=1, le=200)) -> List[Dict[str, Any]]:
    results = memory_find(q, limit=limit)
    return results


__all__ = ["app"]
