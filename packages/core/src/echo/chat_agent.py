"""Chat orchestration layer for the :class:`EchoComputerAssistant`."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Sequence

from .digital_computer import EchoComputerAssistant, ExecutionResult

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PUZZLE_INDEX = REPO_ROOT / "data" / "puzzle_index.json"
DEFAULT_DAILY_TASKS = REPO_ROOT / "apps" / "echo-computer" / "daily_tasks.json"


def _to_json_compatible(value: Any) -> Any:
    """Return ``value`` converted into JSON serialisable primitives."""

    if isinstance(value, Mapping):
        return {str(key): _to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_compatible(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


@dataclass(frozen=True)
class FunctionCall:
    """Represents a function selected by the router."""

    name: str
    arguments: Mapping[str, Any]
    score: float = 1.0


@dataclass(frozen=True)
class CommandContext:
    """Execution context passed to function handlers."""

    message: str
    inputs: Mapping[str, Any]
    execute: bool = False


@dataclass(frozen=True)
class CommandResponse:
    """Structured response emitted by command handlers."""

    function: str
    message: str
    data: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        """Return a JSON-compatible mapping representing the response."""

        return {
            "function": self.function,
            "message": self.message,
            "data": _to_json_compatible(self.data),
            "metadata": _to_json_compatible(self.metadata),
        }


@dataclass(frozen=True)
class FunctionSpec:
    """Metadata describing an OpenAI-style callable function."""

    name: str
    description: str
    parameters: Mapping[str, Any]
    handler: Callable[[FunctionCall, CommandContext], CommandResponse]
    metadata: Mapping[str, Any] = field(default_factory=dict)


class FunctionRouter:
    """Deterministic rule-based router inspired by OpenAI function calls."""

    _PUZZLE_PATTERN = re.compile(r"puzzle\s*#?\s*(\d+)", re.IGNORECASE)
    _FOCUS_ALIASES = {
        "code": "Code",
        "coding": "Code",
        "create": "Create",
        "creative": "Create",
        "collaborate": "Collaborate",
        "collaboration": "Collaborate",
    }

    def route(self, message: str) -> FunctionCall:
        """Return the function call that should handle ``message``."""

        normalised = message.strip().lower()
        puzzle_match = self._PUZZLE_PATTERN.search(normalised)
        if ("solve" in normalised or "lookup" in normalised) and puzzle_match:
            return FunctionCall(
                name="solve_puzzle",
                arguments={"puzzle_id": int(puzzle_match.group(1))},
            )

        if "launch" in normalised:
            if "echo.bank" in normalised or "echo bank" in normalised:
                return FunctionCall(
                    name="launch_application",
                    arguments={"application": "echo.bank"},
                )
            if "echo.computer" in normalised or "echo computer" in normalised:
                return FunctionCall(
                    name="launch_application",
                    arguments={"application": "echo.computer"},
                )

        if "daily" in normalised and (
            "task" in normalised
            or "tasks" in normalised
            or "invitation" in normalised
            or "invocations" in normalised
            or "echo computer" in normalised
        ):
            arguments: Dict[str, Any] = {}
            focus = self._match_focus(normalised)
            if focus:
                arguments["focus"] = focus
            limit = self._extract_limit(normalised)
            if limit is not None:
                arguments["limit"] = limit
            return FunctionCall(name="daily_invitations", arguments=arguments)

        return FunctionCall(name="digital_computer", arguments={"prompt": message})

    def _match_focus(self, text: str) -> str | None:
        for keyword, focus in self._FOCUS_ALIASES.items():
            if keyword in text:
                return focus
        return None

    @staticmethod
    def _extract_limit(text: str) -> int | None:
        match = re.search(r"(?:top|first|show|list|pick)\s*(\d+)", text)
        if not match:
            return None
        try:
            value = int(match.group(1))
        except ValueError:
            return None
        return value if value > 0 else None


class PuzzleKnowledgeBase:
    """Lightweight helper that exposes puzzle metadata for chat commands."""

    def __init__(self, index_path: Path | None = None) -> None:
        self._index_path = Path(index_path) if index_path else DEFAULT_PUZZLE_INDEX
        self._entries: Dict[int, Mapping[str, Any]] | None = None

    def lookup(self, puzzle_id: int) -> Mapping[str, Any] | None:
        self._ensure_loaded()
        assert self._entries is not None
        return self._entries.get(int(puzzle_id))

    def _ensure_loaded(self) -> None:
        if self._entries is not None:
            return

        entries: Dict[int, Mapping[str, Any]] = {}
        if self._index_path.exists():
            with self._index_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            for raw in payload.get("puzzles", []):
                try:
                    identifier = int(raw["id"])
                except (KeyError, TypeError, ValueError):
                    continue
                doc = raw.get("doc")
                doc_path: str | None = None
                if isinstance(doc, str):
                    candidate = (REPO_ROOT / doc).resolve()
                    if candidate.exists():
                        doc_path = str(candidate)
                entries[identifier] = {
                    "id": identifier,
                    "title": raw.get("title", f"Puzzle #{identifier}"),
                    "script_type": raw.get("script_type"),
                    "hash160": raw.get("hash160"),
                    "address": raw.get("address"),
                    "status": raw.get("status", "unknown"),
                    "doc": doc,
                    "doc_path": doc_path,
                }

        # Puzzle #96 is not present in the shared index.  Pull the metadata from
        # the dedicated reconstruction report so that chat commands can still
        # respond with useful information.
        if 96 not in entries:
            report_dir = REPO_ROOT / "reports"
            for candidate in report_dir.glob("pkscript_*.md"):
                text = candidate.read_text(encoding="utf-8")
                title_match = re.search(r"^#\s*Puzzle\s*#(\d+)\s*(.*)$", text, re.MULTILINE)
                if not title_match:
                    continue
                identifier = int(title_match.group(1))
                if identifier != 96:
                    continue
                hash_match = re.search(r"`([0-9a-fA-F]{40})`", text)
                address_match = re.search(
                    r"#\s*([123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{25,36})",
                    text,
                )
                if not hash_match or not address_match:
                    continue
                title_suffix = title_match.group(2).strip()
                entries[identifier] = {
                    "id": identifier,
                    "title": title_suffix or f"Puzzle #{identifier}",
                    "script_type": "p2pkh",
                    "hash160": hash_match.group(1).lower(),
                    "address": address_match.group(1),
                    "status": "documented",
                    "doc": str(candidate.relative_to(REPO_ROOT)),
                    "doc_path": str(candidate.resolve()),
                }
                break

        self._entries = entries


class DailyTaskRegistry:
    """Expose the Echo Computer daily invitations document."""

    def __init__(self, tasks_path: Path | None = None) -> None:
        self._tasks_path = Path(tasks_path) if tasks_path else DEFAULT_DAILY_TASKS
        self._cache: Dict[str, Any] | None = None
        self._cache_mtime: float | None = None

    def snapshot(self, *, focus: str | None = None, limit: int | None = None) -> Dict[str, Any]:
        payload = self._load_payload()
        tasks = list(payload.get("tasks", []))
        total_tasks = len(tasks)

        filtered = tasks
        focus_label: str | None = None
        if focus:
            focus_normalised = focus.lower()
            filtered = [
                task
                for task in tasks
                if str(task.get("focus", "")).lower() == focus_normalised
            ]
            focus_label = focus

        available = len(filtered)
        selection = filtered
        if limit is not None and limit > 0:
            selection = filtered[:limit]

        return {
            "updated": payload.get("updated"),
            "tasks": selection,
            "total_tasks": total_tasks,
            "available_tasks": available,
            "focus": focus_label,
            "limit": limit,
            "source": str(self._tasks_path),
        }

    def _load_payload(self) -> Dict[str, Any]:
        path = self._tasks_path
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            self._cache = {"updated": None, "tasks": []}
            self._cache_mtime = None
            return self._cache

        if self._cache is not None and self._cache_mtime == mtime:
            return self._cache

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, dict):
            payload = {"updated": None, "tasks": []}
        payload.setdefault("tasks", [])

        self._cache = payload
        self._cache_mtime = mtime
        return payload


class EchoChatAgent:
    """Router-driven chatbot agent that exposes backend functions to chat UIs."""

    def __init__(
        self,
        *,
        assistant: EchoComputerAssistant | None = None,
        router: FunctionRouter | None = None,
        knowledge_base: PuzzleKnowledgeBase | None = None,
        task_registry: DailyTaskRegistry | None = None,
    ) -> None:
        self._assistant = assistant or EchoComputerAssistant()
        self._router = router or FunctionRouter()
        self._knowledge_base = knowledge_base or PuzzleKnowledgeBase()
        self._task_registry = task_registry or DailyTaskRegistry()

        self._functions: Dict[str, FunctionSpec] = {
            "solve_puzzle": FunctionSpec(
                name="solve_puzzle",
                description="Return the reconstructed address and metadata for a Bitcoin puzzle entry.",
                parameters={
                    "type": "object",
                    "properties": {
                        "puzzle_id": {
                            "type": "integer",
                            "description": "Identifier of the puzzle to recover metadata for.",
                        }
                    },
                    "required": ["puzzle_id"],
                },
                handler=self._handle_solve_puzzle,
                metadata={
                    "category": "puzzle",
                    "examples": ["solve puzzle #96", "lookup puzzle 256"],
                },
            ),
            "launch_application": FunctionSpec(
                name="launch_application",
                description="Describe how to start one of the Echo ecosystem applications.",
                parameters={
                    "type": "object",
                    "properties": {
                        "application": {
                            "type": "string",
                            "enum": ["echo.bank", "echo.computer"],
                            "description": "Canonical short-name of the application to launch.",
                        }
                    },
                    "required": ["application"],
                },
                handler=self._handle_launch_application,
                metadata={
                    "category": "operations",
                    "examples": ["launch echo.bank", "launch echo computer"],
                },
            ),
            "daily_invitations": FunctionSpec(
                name="daily_invitations",
                description="Surface Echo Computer daily invitation tasks with optional filters.",
                parameters={
                    "type": "object",
                    "properties": {
                        "focus": {
                            "type": "string",
                            "enum": ["Code", "Create", "Collaborate"],
                            "description": "Optional focus filter to only show Code, Create, or Collaborate invitations.",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Restrict the response to the first N invitations after filtering.",
                        },
                    },
                },
                handler=self._handle_daily_invitations,
                metadata={
                    "category": "echo_computer",
                    "examples": [
                        "show daily echo computer tasks",
                        "daily code invitation",
                        "list top 2 daily tasks",
                    ],
                },
            ),
            "digital_computer": FunctionSpec(
                name="digital_computer",
                description="Generate or execute assembly programs using the Echo digital computer.",
                parameters={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Natural language description of the desired program.",
                        }
                    },
                    "required": ["prompt"],
                },
                handler=self._handle_digital_computer,
                metadata={
                    "category": "digital_computer",
                    "examples": [
                        "compute factorial of 5",
                        "stream fibonacci terms",
                        "echo hello world",
                    ],
                },
            ),
        }

    def describe_functions(self) -> Sequence[Mapping[str, Any]]:
        """Return the available function definitions in JSON schema form."""

        return [
            {
                "name": spec.name,
                "description": spec.description,
                "parameters": spec.parameters,
                "metadata": _to_json_compatible(spec.metadata),
            }
            for spec in self._functions.values()
        ]

    def handle_command(
        self,
        message: str,
        *,
        inputs: Mapping[str, Any] | None = None,
        execute: bool = False,
    ) -> CommandResponse:
        """Route ``message`` to the appropriate function handler."""

        call = self._router.route(message)
        spec = self._functions.get(call.name)
        if spec is None:
            raise KeyError(f"no function registered for {call.name!r}")

        context = CommandContext(message=message, inputs=dict(inputs or {}), execute=execute)
        response = spec.handler(call, context)
        combined_metadata: Dict[str, Any] = dict(spec.metadata)
        combined_metadata.setdefault("function_call", {"name": call.name, "arguments": dict(call.arguments)})
        return CommandResponse(
            function=response.function,
            message=response.message,
            data=response.data,
            metadata={**combined_metadata, **dict(response.metadata)},
        )

    # ------------------------------------------------------------------
    # Handlers

    def _handle_solve_puzzle(self, call: FunctionCall, _: CommandContext) -> CommandResponse:
        puzzle_id = int(call.arguments.get("puzzle_id", 0))
        entry = self._knowledge_base.lookup(puzzle_id)
        if not entry:
            return CommandResponse(
                function="solve_puzzle",
                message=f"Puzzle #{puzzle_id} is not indexed yet.",
                data={"puzzle_id": puzzle_id, "status": "missing"},
                metadata={"confidence": 0.0},
            )

        message = f"Puzzle #{puzzle_id}: {entry.get('address')} ({entry.get('script_type')})"
        return CommandResponse(
            function="solve_puzzle",
            message=message,
            data={"puzzle": entry},
            metadata={"confidence": 1.0},
        )

    def _handle_launch_application(self, call: FunctionCall, _: CommandContext) -> CommandResponse:
        application = str(call.arguments.get("application", "")).lower()
        if application == "echo.bank":
            app_root = REPO_ROOT / "apps" / "transparency.bank"
            message = "Run `npm install` followed by `npm run dev` inside apps/transparency.bank."
            data = {
                "application": "echo.bank",
                "path": str(app_root.resolve()),
                "commands": ["npm install", "npm run dev"],
                "entrypoint": "server.js",
            }
            return CommandResponse(
                function="launch_application",
                message=message,
                data=data,
                metadata={"confidence": 0.9},
            )

        if application == "echo.computer":
            app_root = REPO_ROOT / "apps" / "echo-computer"
            message = (
                "Install dependencies then run `npm run apps:echo-computer` and open http://localhost:8080."
            )
            data = {
                "application": "echo.computer",
                "path": str(app_root.resolve()),
                "commands": ["npm install", "npm run apps:echo-computer"],
                "entrypoint": "server.js",
                "ui": "http://localhost:8080",
            }
            return CommandResponse(
                function="launch_application",
                message=message,
                data=data,
                metadata={"confidence": 0.9},
            )

        return CommandResponse(
            function="launch_application",
            message=f"Application {application!r} is not recognised.",
            data={"application": application, "status": "unknown"},
            metadata={"confidence": 0.0},
        )

    def _handle_daily_invitations(self, call: FunctionCall, _: CommandContext) -> CommandResponse:
        focus = call.arguments.get("focus")
        limit = call.arguments.get("limit")
        snapshot = self._task_registry.snapshot(
            focus=str(focus) if focus else None,
            limit=int(limit) if isinstance(limit, int) else None,
        )
        tasks = snapshot.get("tasks", [])
        focus_label = snapshot.get("focus")
        updated = snapshot.get("updated")
        limit_value = snapshot.get("limit")

        if tasks:
            focus_fragment = f" ({focus_label})" if focus_label else ""
            limit_fragment = f", first {limit_value}" if limit_value else ""
            message = f"Echo Computer daily invitations{focus_fragment} ready{limit_fragment}."
            confidence = 0.95
        else:
            message = "No Echo Computer daily invitations were found."
            confidence = 0.2

        metadata = {
            "confidence": confidence,
            "updated": updated,
            "focus": focus_label,
            "limit": limit_value,
        }
        data = {
            "tasks": tasks,
            "total_tasks": snapshot.get("total_tasks", 0),
            "available_tasks": snapshot.get("available_tasks", 0),
            "source": snapshot.get("source"),
        }

        return CommandResponse(
            function="daily_invitations",
            message=message,
            data=data,
            metadata=metadata,
        )

    def _handle_digital_computer(self, call: FunctionCall, context: CommandContext) -> CommandResponse:
        prompt = str(call.arguments.get("prompt", context.message))
        suggestion = self._assistant.suggest(prompt)
        payload: Dict[str, Any] = {
            "suggestion": {
                "description": suggestion.description,
                "program": suggestion.program,
                "required_inputs": suggestion.required_inputs,
                "metadata": _to_json_compatible(suggestion.metadata),
            }
        }

        if context.execute:
            try:
                result = self._assistant.execute(suggestion, inputs=context.inputs)
            except Exception as exc:  # pragma: no cover - surfaced as response payload
                payload["execution_error"] = str(exc)
            else:
                payload["execution"] = self._serialise_execution(result)

        return CommandResponse(
            function="digital_computer",
            message=suggestion.description,
            data=payload,
            metadata={"confidence": 1.0},
        )

    @staticmethod
    def _serialise_execution(result: ExecutionResult) -> Mapping[str, Any]:
        quantum_registers = {
            name: {
                "state": [list(pair) for pair in details.get("state", ())],
                "bloch": list(details.get("bloch", ())),
                "history": list(details.get("history", ())),
            }
            for name, details in result.quantum_registers.items()
        }
        return {
            "halted": result.halted,
            "steps": result.steps,
            "output": list(result.output),
            "registers": dict(result.registers),
            "memory": dict(result.memory),
            "diagnostics": list(result.diagnostics),
            "quantum_registers": quantum_registers,
        }


__all__ = [
    "CommandContext",
    "CommandResponse",
    "DailyTaskRegistry",
    "EchoChatAgent",
    "FunctionCall",
    "FunctionRouter",
    "FunctionSpec",
    "PuzzleKnowledgeBase",
]

