"""Bot Forge module for dynamically provisioning Echo Habitat workers."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from celery import signals
from celery.result import AsyncResult

from ..memory.store import Memory
from ..orchestrator.queue import app as celery

TRACE_ROOT = Path(os.getenv("ECHO_FORGE_TRACE_ROOT", Path(__file__).resolve().parent / "traces"))
TRACE_ROOT.mkdir(parents=True, exist_ok=True)

TRACE_FILE = "trace.json"
LOG_FILE = "logs.jsonl"
OUTPUT_FILE = "outputs.json"


@dataclass
class BotTemplate:
    """Configuration template for a forged bot."""

    archetype: str
    kind: str
    queue: str
    description: str
    default_prompt: str
    capabilities: List[str] = field(default_factory=list)
    default_params: Dict[str, Any] = field(default_factory=dict)


TEMPLATES: Dict[str, BotTemplate] = {
    "codesmith": BotTemplate(
        archetype="CodeSmith",
        kind="codegen",
        queue="codegen",
        description="Autonomous code generation and refactoring smith",
        default_prompt="Synthesize a functional code artifact based on the provided intent.",
        capabilities=["codegen", "analysis", "refinement"],
        default_params={"mode": "synthesis"},
    ),
    "testpilot": BotTemplate(
        archetype="TestPilot",
        kind="tester",
        queue="tester",
        description="Launches validation suites, coverage scans, and runtime probes",
        default_prompt="Execute diagnostic test flights for the referenced project scope.",
        capabilities=["testing", "monitoring", "reporting"],
        default_params={"mode": "diagnostics"},
    ),
    "archivist": BotTemplate(
        archetype="Archivist",
        kind="attestor",
        queue="attestor",
        description="Harvests artifacts, notarises outputs, and persists bundles",
        default_prompt="Collect and notarise the supplied artifacts and ledger notes.",
        capabilities=["data-harvest", "attestation", "trace"],
        default_params={"mode": "ingest"},
    ),
    "storyweaver": BotTemplate(
        archetype="StoryWeaver",
        kind="storyteller",
        queue="storyteller",
        description="Narrative synthesis, visualisation cues, and mythic summaries",
        default_prompt="Compose a resonant narrative based on the given signals.",
        capabilities=["story", "visualizer", "summaries"],
        default_params={"mode": "narrative"},
    ),
}


class ForgeError(RuntimeError):
    """Raised when forging cannot be completed."""


def _normalize_archetype(archetype: str) -> str:
    key = archetype.lower()
    if key not in TEMPLATES:
        raise ForgeError(f"Unknown bot archetype: {archetype}")
    return key


def _trace_dir(bot_id: str) -> Path:
    path = TRACE_ROOT / bot_id
    path.mkdir(parents=True, exist_ok=True)
    (path / "artifacts").mkdir(exist_ok=True)
    return path


def _json_safe(payload: Any) -> Any:
    try:
        json.dumps(payload)
        return payload
    except TypeError:
        return repr(payload)


def _write_trace(bot_id: str, data: Dict[str, Any]) -> None:
    trace_path = _trace_dir(bot_id) / TRACE_FILE
    with trace_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def _append_history(bot_id: str, entry: Dict[str, Any]) -> None:
    entry = {"ts": time.time(), **entry}
    log_path = _trace_dir(bot_id) / LOG_FILE
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    _to_memory("forge.log", {"bot_id": bot_id, **entry})


def _update_outputs(bot_id: str, outputs: Dict[str, Any]) -> None:
    outputs_path = _trace_dir(bot_id) / OUTPUT_FILE
    with outputs_path.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(outputs), handle, indent=2)


def _load_trace(bot_id: str) -> Dict[str, Any]:
    trace_path = _trace_dir(bot_id) / TRACE_FILE
    if not trace_path.exists():
        raise ForgeError(f"Trace bundle missing for bot {bot_id}")
    with trace_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _to_memory(kind: str, payload: Dict[str, Any]) -> None:
    try:
        with Memory() as mem:
            mem.add(kind, _json_safe(payload))
    except Exception:  # pragma: no cover - memory channel best-effort
        pass


def spawn_bot(
    archetype: str,
    intent: str = "",
    *,
    params: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Spawn a new forged bot instance and dispatch its primary task."""

    key = _normalize_archetype(archetype)
    template = TEMPLATES[key]
    bot_id = f"forge-{key}-{uuid4().hex[:8]}"

    merged_params: Dict[str, Any] = {**template.default_params, **(params or {})}
    forge_payload = {
        "bot_id": bot_id,
        "archetype": template.archetype,
        "intent": intent or template.default_prompt,
        "capabilities": template.capabilities,
        "spawned_at": time.time(),
    }
    merged_params.setdefault("forge", forge_payload)

    task_spec = {
        "kind": template.kind,
        "prompt": intent or template.default_prompt,
        "params": merged_params,
        "files": files or {},
    }

    result = celery.send_task(
        f"workers.{template.kind}.run",
        kwargs={"spec": task_spec},
        queue=template.queue,
    )

    bundle = {
        "bot_id": bot_id,
        "archetype": template.archetype,
        "queue": template.queue,
        "kind": template.kind,
        "intent": intent or template.default_prompt,
        "task_id": result.id,
        "history": [
            {
                "task_id": result.id,
                "reason": "spawned",
                "ts": time.time(),
            }
        ],
        "params": merged_params,
        "files": files or {},
        "capabilities": template.capabilities,
        "description": template.description,
    }
    _write_trace(bot_id, bundle)
    _append_history(bot_id, {"event": "spawned", "task_id": result.id})
    _to_memory(
        "forge.spawn",
        {
            "bot_id": bot_id,
            "archetype": template.archetype,
            "task_id": result.id,
            "queue": template.queue,
            "intent": intent or template.default_prompt,
        },
    )

    return {
        "bot_id": bot_id,
        "archetype": template.archetype,
        "queue": template.queue,
        "task_id": result.id,
        "state": "PENDING",
        "trace_bundle": str(_trace_dir(bot_id)),
        "capabilities": template.capabilities,
        "intent": intent or template.default_prompt,
    }


def check_health(bot_id: str) -> Dict[str, Any]:
    """Evaluate the health of a forged bot and auto-restart if needed."""

    bundle = _load_trace(bot_id)
    task_id = bundle["task_id"]
    result = AsyncResult(task_id, app=celery)
    state = result.state

    response: Dict[str, Any] = {
        "bot_id": bot_id,
        "task_id": task_id,
        "state": state,
        "restarted": False,
    }

    if state in {"FAILURE", "REVOKED"}:
        response["restarted"] = True
        response["restart_reason"] = state
        response["previous_task_id"] = task_id
        restart = celery.send_task(
            f"workers.{bundle['kind']}.run",
            kwargs={"spec": {
                "kind": bundle["kind"],
                "prompt": bundle["intent"],
                "params": bundle.get("params", {}),
                "files": bundle.get("files", {}),
            }},
            queue=bundle["queue"],
        )
        response["restart_task_id"] = restart.id
        bundle["task_id"] = restart.id
        bundle.setdefault("history", []).append(
            {
                "task_id": restart.id,
                "reason": "auto-restart",
                "ts": time.time(),
            }
        )
        _write_trace(bot_id, bundle)
        _append_history(
            bot_id,
            {
                "event": "auto-restart",
                "task_id": restart.id,
                "previous_task_id": task_id,
                "state": state,
            },
        )
        _to_memory(
            "forge.restart",
            {
                "bot_id": bot_id,
                "from": task_id,
                "to": restart.id,
                "state": state,
            },
        )
    else:
        _append_history(bot_id, {"event": "health", "state": state})
        _to_memory("forge.health", response)

    return response


def _dispatch_trace_update(bot_id: str, event: str, payload: Dict[str, Any]) -> None:
    _append_history(bot_id, {"event": event, **payload})
    if payload:
        trace = _load_trace(bot_id)
        trace.setdefault("events", []).append({"event": event, **payload, "ts": time.time()})
        _write_trace(bot_id, trace)


def _handle_task_success(sender=None, task_id=None, args=None, kwargs=None, retval=None, state=None, **_):
    if state and state != "SUCCESS":
        return
    spec = (kwargs or {}).get("spec", {})
    forge_meta = spec.get("params", {}).get("forge")
    if not forge_meta:
        return
    bot_id = forge_meta.get("bot_id")
    if not bot_id:
        return
    payload = {
        "task_id": task_id,
        "state": "SUCCESS",
        "result": _json_safe(retval),
    }
    _update_outputs(bot_id, payload)
    _dispatch_trace_update(bot_id, "completed", payload)
    _to_memory("forge.complete", {"bot_id": bot_id, **payload})


def _handle_task_failure(sender=None, task_id=None, args=None, kwargs=None, exception=None, einfo=None, **_):
    spec = (kwargs or {}).get("spec", {})
    forge_meta = spec.get("params", {}).get("forge")
    if not forge_meta:
        return
    bot_id = forge_meta.get("bot_id")
    if not bot_id:
        return
    payload = {
        "task_id": task_id,
        "state": "FAILURE",
        "error": repr(exception),
    }
    if einfo is not None:
        payload["traceback"] = str(einfo)
    _update_outputs(bot_id, payload)
    _dispatch_trace_update(bot_id, "failed", payload)
    _to_memory("forge.failure", {"bot_id": bot_id, **payload})


signals.task_postrun.connect(_handle_task_success)
signals.task_failure.connect(_handle_task_failure)

__all__ = [
    "spawn_bot",
    "check_health",
    "ForgeError",
    "TEMPLATES",
]
