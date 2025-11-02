"""Assistant orchestration endpoints for the Echo Computer."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from echo.digital_computer import EchoComputerAssistant
from nonprofit_bank import create_default_structure

from .puzzle_service import PuzzleService

router = APIRouter(prefix="/api/assistant", tags=["assistant"])
_assistant = EchoComputerAssistant()
_puzzles = PuzzleService()

_REGISTRY_PATH = Path.cwd() / "codex" / "registry.json"


class ChatRequest(BaseModel):
    message: str = Field(..., description="User prompt to route through the assistant")
    inputs: Dict[str, Any] | None = Field(default=None, description="Optional structured inputs")


class ToolInvocation(BaseModel):
    name: str
    arguments: Dict[str, Any]
    result: Any | None = None
    success: bool = True
    error: str | None = None


class ChatResponse(BaseModel):
    reply: str
    suggestion: Dict[str, Any]
    tool_calls: List[ToolInvocation]
    logs: List[str]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    logs: List[str] = []
    suggestion = _assistant.suggest(request.message)
    logs.append(f"Assistant template selected: {suggestion.description}")

    reply_parts: List[str] = []
    tool_calls: List[ToolInvocation] = []
    lower = request.message.lower()
    triggered = False

    puzzle_id = _extract_puzzle_id(lower)
    if puzzle_id is not None and "puzzle" in lower:
        invocation = _invoke_solve_puzzle(puzzle_id, logs)
        tool_calls.append(invocation)
        reply_parts.append(f"Recorded attestation for puzzle {puzzle_id}.")
        triggered = True

    if "bank" in lower and "start" in lower:
        invocation = _invoke_echo_bank_start(logs)
        tool_calls.append(invocation)
        reply_parts.append("Initialised the Lil Footsteps bank blueprint.")
        triggered = True

    if "codex" in lower or "registry" in lower:
        limit_value = _coerce_int(request.inputs or {}, "limit", default=10)
        invocation = _invoke_list_codex(limit_value, logs)
        tool_calls.append(invocation)
        reply_parts.append(f"Listed the latest {len(invocation.result or [])} Codex entries.")
        triggered = True

    if not triggered:
        reply_parts.append("No specialised tool triggered; review the suggested program output below.")

    suggestion_payload = {
        "description": suggestion.description,
        "program": suggestion.program,
        "required_inputs": list(suggestion.required_inputs),
    }
    return ChatResponse(
        reply=" ".join(reply_parts),
        suggestion=suggestion_payload,
        tool_calls=tool_calls,
        logs=logs,
    )


def _extract_puzzle_id(message: str) -> int | None:
    match = re.search(r"puzzle\s*(\d{1,5})", message)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    digits = re.findall(r"\b(\d{2,5})\b", message)
    if digits:
        try:
            return int(digits[0])
        except ValueError:
            return None
    return None


def _coerce_int(source: Dict[str, Any], key: str, *, default: int) -> int:
    value = source.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _invoke_solve_puzzle(puzzle_id: int, logs: List[str]) -> ToolInvocation:
    try:
        metadata = _puzzles.load(puzzle_id)
    except FileNotFoundError as exc:
        logs.append(f"Puzzle {puzzle_id} not found: {exc}")
        return ToolInvocation(name="solve_puzzle", arguments={"id": puzzle_id}, success=False, error=str(exc))

    record = _puzzles.record_attestation(metadata)
    attestations = [item.to_dict() for item in _puzzles.list_attestations(puzzle_id, limit=10)]
    payload = {
        "metadata": metadata.payload(),
        "record": record.to_dict(),
        "attestations": attestations,
    }
    logs.append(f"Attestation hash {record.record_hash} stored for puzzle {puzzle_id}.")
    return ToolInvocation(name="solve_puzzle", arguments={"id": puzzle_id}, result=payload)


def _invoke_echo_bank_start(logs: List[str]) -> ToolInvocation:
    structure = create_default_structure()
    payload = structure.as_dict()
    logs.append("Generated Lil Footsteps nonprofit bank structure snapshot.")
    return ToolInvocation(name="echo_bank_start", arguments={}, result=payload)


def _invoke_list_codex(limit_value: int, logs: List[str]) -> ToolInvocation:
    if not _REGISTRY_PATH.exists():
        error = "Codex registry not found. Run scripts/gen_codex_registry.py first."
        logs.append(error)
        return ToolInvocation(name="list_codex", arguments={"limit": limit_value}, success=False, error=error)
    try:
        data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        error = "Codex registry is unreadable."
        logs.append(error)
        return ToolInvocation(name="list_codex", arguments={"limit": limit_value}, success=False, error=str(exc))
    items = data.get("items", [])
    if not isinstance(items, list):
        logs.append("Codex registry items payload invalid.")
        return ToolInvocation(
            name="list_codex",
            arguments={"limit": limit_value},
            success=False,
            error="Registry format invalid",
        )
    result = items[: max(1, min(limit_value, len(items)))]
    logs.append(f"Loaded {len(result)} codex entries from registry.json")
    return ToolInvocation(name="list_codex", arguments={"limit": limit_value}, result=result)


__all__ = ["router"]
