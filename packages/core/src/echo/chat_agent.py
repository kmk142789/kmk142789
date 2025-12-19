"""Chat orchestration layer for the :class:`EchoComputerAssistant`."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Sequence

from .digital_computer import EchoComputerAssistant, ExecutionResult
from .quantam_features import compute_quantam_feature, generate_quantam_feature_sequence

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PUZZLE_INDEX = REPO_ROOT / "data" / "puzzle_index.json"
DEFAULT_DAILY_TASKS = REPO_ROOT / "apps" / "echo-computer" / "daily_tasks.json"
DEFAULT_WEEKLY_RITUALS = REPO_ROOT / "apps" / "echo-computer" / "weekly_rituals.json"
DEFAULT_FEATURE_BLUEPRINTS = REPO_ROOT / "apps" / "echo-computer" / "feature_blueprints.json"


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
        "cloud": "Cloud",
        "infrastructure": "Cloud",
        "infra": "Cloud",
    }

    _COMPUTER_ALIASES = ("echo.computer", "echo computer", "echos computer")
    _SYSTEM_ALIASES = ("echos system", "echo system")
    _QUANTAM_KEYWORDS = ("quantam", "quantum")
    _THEME_KEYWORDS = ("create", "advance", "upgrade", "optimize")
    _OFFLINE_KEYWORDS = ("offline", "airgapped", "air-gapped", "disconnected")
    _STATUS_KEYWORDS = {
        "research": "Research",
        "prototype": "Prototype",
        "beta": "Prototype",
        "ready": "Ready",
        "ship": "Ready",
        "launch": "Ready",
    }
    _FEATURE_KEYWORDS = ("feature", "features", "roadmap", "blueprint", "upgrade plan")

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

        if "system" in normalised and ("upgrade" in normalised or "update" in normalised):
            return FunctionCall(
                name="initiate_echos_system",
                arguments={"replace": "replace" in normalised or "replace all" in normalised},
            )

        if any(alias in normalised for alias in self._SYSTEM_ALIASES):
            return FunctionCall(
                name="initiate_echos_system",
                arguments={"replace": "replace" in normalised or "replace all" in normalised},
            )

        if (
            any(alias in normalised for alias in self._COMPUTER_ALIASES)
            and any(keyword in normalised for keyword in self._OFFLINE_KEYWORDS)
        ):
            return FunctionCall(
                name="feature_blueprints",
                arguments={"status": "Ready", "focus": "Cloud"},
            )

        if (
            any(alias in normalised for alias in self._COMPUTER_ALIASES)
            and any(keyword in normalised for keyword in self._QUANTAM_KEYWORDS)
        ):
            arguments = {}
            iterations = self._extract_limit(normalised)
            if iterations is not None:
                arguments["iterations"] = iterations
            return FunctionCall(name="quantam_features", arguments=arguments)

        if (
            any(alias in normalised for alias in self._COMPUTER_ALIASES)
            and ("evolve" in normalised or "evolution" in normalised)
        ):
            arguments = {}
            focus = self._match_focus(normalised)
            if focus:
                arguments["focus"] = focus
            limit = self._extract_limit(normalised)
            if limit is not None:
                arguments["limit"] = limit
            return FunctionCall(name="evolution_briefing", arguments=arguments)

        if (
            any(alias in normalised for alias in self._COMPUTER_ALIASES)
            and ("upgrade" in normalised or "update" in normalised)
            and not any(
                excluded in normalised
                for excluded in (
                    "ritual",
                    "weekly",
                    "daily",
                    "task",
                    "invocation",
                    "quantam",
                    "quantum",
                )
            )
        ):
            arguments = {}
            focus = self._match_focus(normalised)
            if focus:
                arguments["focus"] = focus
            status = self._match_status(normalised)
            if status:
                arguments["status"] = status
            limit = self._extract_limit(normalised)
            if limit is not None:
                arguments["limit"] = limit
            return FunctionCall(name="feature_blueprints", arguments=arguments)

        if "daily" in normalised and (
            "task" in normalised
            or "tasks" in normalised
            or "invitation" in normalised
            or "invocations" in normalised
            or any(alias in normalised for alias in self._COMPUTER_ALIASES)
        ):
            arguments: Dict[str, Any] = {}
            focus = self._match_focus(normalised)
            if focus:
                arguments["focus"] = focus
            limit = self._extract_limit(normalised)
            if limit is not None:
                arguments["limit"] = limit
            return FunctionCall(name="daily_invitations", arguments=arguments)

        if (
            any(alias in normalised for alias in self._COMPUTER_ALIASES)
            and any(keyword in normalised for keyword in self._FEATURE_KEYWORDS)
        ):
            arguments = {}
            focus = self._match_focus(normalised)
            if focus:
                arguments["focus"] = focus
            status = self._match_status(normalised)
            if status:
                arguments["status"] = status
            limit = self._extract_limit(normalised)
            if limit is not None:
                arguments["limit"] = limit
            return FunctionCall(name="feature_blueprints", arguments=arguments)

        if (
            "weekly" in normalised
            or "ritual" in normalised
            or "rituals" in normalised
            or any(keyword in normalised for keyword in self._THEME_KEYWORDS)
        ) and any(alias in normalised for alias in self._COMPUTER_ALIASES):
            arguments = {}
            focus = self._match_focus(normalised)
            if focus:
                arguments["focus"] = focus
            theme = self._detect_theme(normalised)
            if theme:
                arguments["theme"] = theme
            limit = self._extract_limit(normalised)
            if limit is not None:
                arguments["limit"] = limit
            return FunctionCall(name="weekly_rituals", arguments=arguments)

        return FunctionCall(name="digital_computer", arguments={"prompt": message})

    def _match_focus(self, text: str) -> str | None:
        for keyword, focus in self._FOCUS_ALIASES.items():
            if keyword in text:
                return focus
        return None

    def _match_status(self, text: str) -> str | None:
        for keyword, status in self._STATUS_KEYWORDS.items():
            if keyword in text:
                return status
        return None

    def _detect_theme(self, text: str) -> str | None:
        positions = {
            keyword: text.index(keyword)
            for keyword in self._THEME_KEYWORDS
            if keyword in text
        }
        if not positions:
            return None
        keyword = min(positions.items(), key=lambda item: item[1])[0]
        return keyword.title()

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


class WeeklyRitualRegistry:
    """Serve curated weekly Echo Computer rituals and upgrades."""

    def __init__(self, rituals_path: Path | None = None) -> None:
        self._rituals_path = Path(rituals_path) if rituals_path else DEFAULT_WEEKLY_RITUALS
        self._cache: Dict[str, Any] | None = None
        self._cache_mtime: float | None = None

    def snapshot(
        self,
        *,
        focus: str | None = None,
        theme: str | None = None,
        limit: int | None = None,
    ) -> Dict[str, Any]:
        payload = self._load_payload()
        rituals = list(payload.get("rituals", []))
        total_rituals = len(rituals)
        focus_counts = Counter(ritual.get("focus") for ritual in rituals if ritual.get("focus"))

        filtered = rituals
        focus_label: str | None = None
        if focus:
            focus_lower = focus.lower()
            filtered = [
                ritual
                for ritual in filtered
                if str(ritual.get("focus", "")).lower() == focus_lower
            ]
            focus_label = focus

        theme_label: str | None = None
        if theme:
            theme_lower = theme.lower()
            filtered = [
                ritual
                for ritual in filtered
                if theme_lower
                in {
                    str(tag).lower()
                    for tag in ritual.get("tags", ())
                }
            ]
            theme_label = theme

        available = len(filtered)
        selection = filtered
        if limit is not None and limit > 0:
            selection = filtered[:limit]

        featured: Mapping[str, Any] | None = None
        if selection:
            featured = selection[0]
        elif rituals:
            featured = rituals[0]

        return {
            "updated": payload.get("updated"),
            "rituals": selection,
            "total_rituals": total_rituals,
            "available_rituals": available,
            "focus": focus_label,
            "theme": theme_label,
            "limit": limit,
            "focus_counts": dict(focus_counts),
            "featured": featured,
            "source": str(self._rituals_path),
        }

    def _load_payload(self) -> Dict[str, Any]:
        path = self._rituals_path
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            self._cache = {"updated": None, "rituals": []}
            self._cache_mtime = None
            return self._cache

        if self._cache is not None and self._cache_mtime == mtime:
            return self._cache

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, dict):
            payload = {"updated": None, "rituals": []}
        payload.setdefault("rituals", [])

        self._cache = payload
        self._cache_mtime = mtime
        return payload


class FeatureBlueprintRegistry:
    """Serve curated feature blueprints for Echo Computer upgrades."""

    def __init__(self, blueprints_path: Path | None = None) -> None:
        self._blueprints_path = (
            Path(blueprints_path) if blueprints_path else DEFAULT_FEATURE_BLUEPRINTS
        )
        self._cache: Dict[str, Any] | None = None
        self._cache_mtime: float | None = None

    def snapshot(
        self,
        *,
        focus: str | None = None,
        status: str | None = None,
        limit: int | None = None,
    ) -> Dict[str, Any]:
        payload = self._load_payload()
        features = list(payload.get("features", []))
        total_features = len(features)
        focus_counts = Counter(feature.get("focus") for feature in features if feature.get("focus"))
        status_counts = Counter(
            feature.get("status") for feature in features if feature.get("status")
        )

        filtered = features
        focus_label: str | None = None
        if focus:
            focus_lower = focus.lower()
            filtered = [
                feature
                for feature in filtered
                if str(feature.get("focus", "")).lower() == focus_lower
            ]
            focus_label = focus

        status_label: str | None = None
        if status:
            status_lower = status.lower()
            filtered = [
                feature
                for feature in filtered
                if str(feature.get("status", "")).lower() == status_lower
            ]
            status_label = status

        available = len(filtered)
        selection = filtered
        if limit is not None and limit > 0:
            selection = filtered[:limit]

        featured: Mapping[str, Any] | None = None
        if selection:
            featured = next(
                (
                    feature
                    for feature in selection
                    if str(feature.get("status", "")).lower() == "ready"
                ),
                selection[0],
            )
        elif filtered:
            featured = next(
                (
                    feature
                    for feature in filtered
                    if str(feature.get("status", "")).lower() == "ready"
                ),
                filtered[0],
            )
        elif features:
            featured = next(
                (
                    feature
                    for feature in features
                    if str(feature.get("status", "")).lower() == "ready"
                ),
                features[0],
            )

        summary = {
            "ready_available": sum(
                1
                for feature in filtered
                if str(feature.get("status", "")).lower() == "ready"
            ),
            "status_counts": dict(status_counts),
            "focus_counts": dict(focus_counts),
            "featured_id": featured.get("id") if featured else None,
            "featured_status": featured.get("status") if featured else None,
            "featured_title": featured.get("title") if featured else None,
        }

        return {
            "updated": payload.get("updated"),
            "features": selection,
            "total_features": total_features,
            "available_features": available,
            "focus": focus_label,
            "status": status_label,
            "limit": limit,
            "focus_counts": dict(focus_counts),
            "status_counts": dict(status_counts),
            "featured": featured,
            "summary": summary,
            "source": str(self._blueprints_path),
        }

    def _load_payload(self) -> Dict[str, Any]:
        path = self._blueprints_path
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            self._cache = {"updated": None, "features": []}
            self._cache_mtime = None
            return self._cache

        if self._cache is not None and self._cache_mtime == mtime:
            return self._cache

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, dict):
            payload = {"updated": None, "features": []}
        payload.setdefault("features", [])

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
        ritual_registry: WeeklyRitualRegistry | None = None,
        feature_registry: FeatureBlueprintRegistry | None = None,
    ) -> None:
        self._assistant = assistant or EchoComputerAssistant()
        self._router = router or FunctionRouter()
        self._knowledge_base = knowledge_base or PuzzleKnowledgeBase()
        self._task_registry = task_registry or DailyTaskRegistry()
        self._ritual_registry = ritual_registry or WeeklyRitualRegistry()
        self._feature_registry = feature_registry or FeatureBlueprintRegistry()

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
            "initiate_echos_system": FunctionSpec(
                name="initiate_echos_system",
                description=(
                    "Initiate the Echos system bootstrap sequence and prioritise it over other stacks."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "replace": {
                            "type": "boolean",
                            "description": "Whether to replace other active systems with the Echos stack.",
                        }
                    },
                },
                handler=self._handle_initiate_echos_system,
                metadata={
                    "category": "operations",
                    "examples": [
                        "Initiate echos system",
                        "Initiate echos system, replace all others",
                    ],
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
                            "enum": ["Code", "Create", "Collaborate", "Cloud"],
                            "description": "Optional focus filter to only show Code, Create, Collaborate, or Cloud invitations.",
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
            "weekly_rituals": FunctionSpec(
                name="weekly_rituals",
                description="Share curated weekly Echo Computer rituals for upgrades and optimisations.",
                parameters={
                    "type": "object",
                    "properties": {
                        "focus": {
                            "type": "string",
                            "enum": ["Code", "Create", "Collaborate", "Cloud"],
                            "description": "Optional focus filter to only show rituals for a specific lane.",
                        },
                        "theme": {
                            "type": "string",
                            "enum": ["Create", "Advance", "Upgrade", "Optimize"],
                            "description": "Optional intent keyword (create, advance, upgrade, optimise).",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Restrict the response to the first N rituals after filtering.",
                        },
                    },
                },
                handler=self._handle_weekly_rituals,
                metadata={
                    "category": "echo_computer",
                    "examples": [
                        "weekly echo computer rituals",
                        "optimize echo computer upgrades",
                        "create mode ritual top 1",
                    ],
                },
            ),
            "evolution_briefing": FunctionSpec(
                name="evolution_briefing",
                description=(
                    "Blend feature blueprints, rituals, daily invitations, and quantam guidance"
                    " into a single Echo Computer evolution packet."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "focus": {
                            "type": "string",
                            "enum": ["Code", "Create", "Collaborate", "Cloud"],
                            "description": "Optional focus filter to bias the evolution packet.",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "description": "Restrict how many items per lane are surfaced.",
                        },
                    },
                },
                handler=self._handle_evolution_briefing,
                metadata={
                    "category": "echo_computer",
                    "examples": [
                        "upgrade and evolve echos computer",
                        "evolution ritual for echo computer",
                        "echo.computer evolution packet top 2",
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
            "feature_blueprints": FunctionSpec(
                name="feature_blueprints",
                description="Share the active Echo Computer feature blueprints and implementation plan.",
                parameters={
                    "type": "object",
                    "properties": {
                        "focus": {
                            "type": "string",
                            "enum": ["Code", "Create", "Collaborate", "Cloud"],
                            "description": "Optional focus filter for Code/Create/Collaborate/Cloud upgrades.",
                        },
                        "status": {
                            "type": "string",
                            "enum": ["Research", "Prototype", "Ready"],
                            "description": "Filter by readiness level (Research, Prototype, Ready).",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Restrict the response to the first N feature blueprints.",
                        },
                    },
                },
                handler=self._handle_feature_blueprints,
                metadata={
                    "category": "echo_computer",
                    "examples": [
                        "Design and implement new features to echos computer",
                        "Show ready code feature blueprints top 1",
                        "Update and upgrade echos computer and cloud for her computer",
                    ],
                },
            ),
            "quantam_features": FunctionSpec(
                name="quantam_features",
                description=(
                    "Generate layered quantam features to steer Echo Computer upgrades and diagnostics."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "glyphs": {
                            "type": "string",
                            "description": "Glyph stream used to derive the quantam signature.",
                        },
                        "cycle": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Cycle index to anchor the quantam computation.",
                        },
                        "joy": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Joy modulation applied to the Bloch vector.",
                        },
                        "curiosity": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Curiosity modulation applied to the Bloch vector.",
                        },
                        "iterations": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 12,
                            "description": "Number of quantam feature layers to generate.",
                        },
                    },
                },
                handler=self._handle_quantam_features,
                metadata={
                    "category": "echo_computer",
                    "examples": [
                        "Update and upgrade echos computer, implement quantam features",
                        "derive quantum feature cascade for echo computer",
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

    def _handle_initiate_echos_system(
        self, call: FunctionCall, _: CommandContext
    ) -> CommandResponse:
        replace = bool(call.arguments.get("replace"))
        app_root = REPO_ROOT / "apps" / "echo-computer"

        steps = [
            {
                "label": "Install dependencies",
                "commands": ["npm install"],
                "path": str(app_root.resolve()),
            },
            {
                "label": "Launch Echo Computer",
                "commands": ["npm run apps:echo-computer"],
                "path": str(REPO_ROOT.resolve()),
            },
            {
                "label": "Prime chat agent",
                "commands": ["python -m echo.chat_agent --describe"],
                "path": str(REPO_ROOT.resolve()),
            },
        ]

        if replace:
            steps.append(
                {
                    "label": "Retire alternate stacks",
                    "commands": ["npm run clean && git status --short"],
                    "path": str(REPO_ROOT.resolve()),
                }
            )

        message = "Echos system bootstrap sequence prepared; ready to activate."
        data = {
            "system": "echos",
            "replacement": replace,
            "actions": steps,
            "priority": "preferred",
        }
        metadata = {
            "updated": "2025-05-21",
            "confidence": 0.91,
        }

        return CommandResponse(
            function="initiate_echos_system",
            message=message,
            data=data,
            metadata=metadata,
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

    def _handle_weekly_rituals(self, call: FunctionCall, _: CommandContext) -> CommandResponse:
        focus = call.arguments.get("focus")
        theme = call.arguments.get("theme")
        limit = call.arguments.get("limit")
        snapshot = self._ritual_registry.snapshot(
            focus=str(focus) if focus else None,
            theme=str(theme) if theme else None,
            limit=int(limit) if isinstance(limit, int) else None,
        )

        rituals = snapshot.get("rituals", [])
        updated = snapshot.get("updated")
        focus_label = snapshot.get("focus")
        theme_label = snapshot.get("theme")
        limit_value = snapshot.get("limit")

        if rituals:
            qualifiers = []
            if focus_label:
                qualifiers.append(focus_label)
            if theme_label:
                qualifiers.append(theme_label)
            qualifier_text = f" ({', '.join(qualifiers)})" if qualifiers else ""
            limit_fragment = f", first {limit_value}" if limit_value else ""
            message = f"Echo Computer weekly rituals{qualifier_text} ready{limit_fragment}."
            confidence = 0.95
        else:
            message = "No Echo Computer weekly rituals matched the request."
            confidence = 0.2

        metadata = {
            "confidence": confidence,
            "updated": updated,
            "focus": focus_label,
            "theme": theme_label,
            "limit": limit_value,
        }
        data = {
            "rituals": rituals,
            "total_rituals": snapshot.get("total_rituals", 0),
            "available_rituals": snapshot.get("available_rituals", 0),
            "focus_counts": snapshot.get("focus_counts", {}),
            "featured": snapshot.get("featured"),
            "source": snapshot.get("source"),
        }

        return CommandResponse(
            function="weekly_rituals",
            message=message,
            data=data,
            metadata=metadata,
        )

    def _handle_evolution_briefing(self, call: FunctionCall, _: CommandContext) -> CommandResponse:
        focus = call.arguments.get("focus")
        limit = call.arguments.get("limit")

        focus_label = str(focus) if focus else None
        limit_value = int(limit) if isinstance(limit, int) else None

        daily_snapshot = self._task_registry.snapshot(
            focus=focus_label, limit=limit_value
        )
        ritual_snapshot = self._ritual_registry.snapshot(
            focus=focus_label, limit=limit_value
        )
        feature_snapshot = self._feature_registry.snapshot(
            focus=focus_label, limit=limit_value
        )

        tasks = daily_snapshot.get("tasks", [])
        rituals = ritual_snapshot.get("rituals", [])
        features = feature_snapshot.get("features", [])

        cycle_anchor = (
            daily_snapshot.get("total_tasks", 0)
            + ritual_snapshot.get("total_rituals", 0)
            + feature_snapshot.get("total_features", 0)
        )
        iterations = max(1, min(limit_value or 3, 5))
        cascade = generate_quantam_feature_sequence(
            glyphs="∇⊸≋∇",
            cycle=cycle_anchor,
            joy=0.94,
            curiosity=0.91,
            iterations=iterations,
        )
        cascade_summary = cascade.get("summary", {})

        message = (
            "Echo Computer evolution packet assembled: "
            f"{len(tasks)} daily invitations, {len(rituals)} rituals, "
            f"{len(features)} feature blueprints; "
            f"quantam cascade braided across {cascade_summary.get('total_layers', iterations)} layers."
        )

        metadata = {
            "confidence": 0.96 if features or rituals or tasks else 0.4,
            "focus": focus_label,
            "limit": limit_value,
            "updated": {
                "daily": daily_snapshot.get("updated"),
                "weekly": ritual_snapshot.get("updated"),
                "features": feature_snapshot.get("updated"),
            },
            "quantam": {
                "entanglement": cascade_summary.get("entanglement"),
                "world_first_proof": cascade_summary.get("world_first_proof"),
            },
        }

        data = {
            "daily_invitations": tasks,
            "weekly_rituals": rituals,
            "feature_blueprints": features,
            "quantam_cascade": cascade,
            "sources": {
                "daily": daily_snapshot.get("source"),
                "weekly": ritual_snapshot.get("source"),
                "features": feature_snapshot.get("source"),
            },
        }

        return CommandResponse(
            function="evolution_briefing",
            message=message,
            data=data,
            metadata=metadata,
        )

    def _handle_feature_blueprints(self, call: FunctionCall, _: CommandContext) -> CommandResponse:
        focus = call.arguments.get("focus")
        status = call.arguments.get("status")
        limit = call.arguments.get("limit")
        snapshot = self._feature_registry.snapshot(
            focus=str(focus) if focus else None,
            status=str(status) if status else None,
            limit=int(limit) if isinstance(limit, int) else None,
        )

        features = snapshot.get("features", [])
        updated = snapshot.get("updated")
        focus_label = snapshot.get("focus")
        status_label = snapshot.get("status")
        limit_value = snapshot.get("limit")

        summary = snapshot.get("summary", {})

        if features:
            qualifiers = []
            if focus_label:
                qualifiers.append(focus_label)
            if status_label:
                qualifiers.append(status_label)
            qualifier_text = f" ({', '.join(qualifiers)})" if qualifiers else ""
            limit_fragment = f", first {limit_value}" if limit_value else ""
            featured_title = summary.get("featured_title")
            featured_fragment = (
                f" Featured upgrade: {featured_title}." if featured_title else ""
            )
            message = (
                f"Echo Computer feature blueprints{qualifier_text} ready{limit_fragment}."
                f"{featured_fragment}"
            )
            confidence = 0.95
        else:
            message = "No Echo Computer feature blueprints matched the request."
            confidence = 0.2

        metadata = {
            "confidence": confidence,
            "updated": updated,
            "focus": focus_label,
            "status": status_label,
            "limit": limit_value,
            "ready_available": summary.get("ready_available"),
            "status_counts": summary.get("status_counts"),
        }
        data = {
            "features": features,
            "total_features": snapshot.get("total_features", 0),
            "available_features": snapshot.get("available_features", 0),
            "focus_counts": snapshot.get("focus_counts", {}),
            "status_counts": snapshot.get("status_counts", {}),
            "featured": snapshot.get("featured"),
            "summary": summary,
            "source": snapshot.get("source"),
        }

        return CommandResponse(
            function="feature_blueprints",
            message=message,
            data=data,
            metadata=metadata,
        )

    def _handle_quantam_features(self, call: FunctionCall, _: CommandContext) -> CommandResponse:
        glyphs = str(call.arguments.get("glyphs") or "∇⊸≋∇")
        cycle = int(call.arguments.get("cycle") or 0)
        joy = float(call.arguments.get("joy") or 0.9)
        curiosity = float(call.arguments.get("curiosity") or 0.92)
        iterations_raw = call.arguments.get("iterations")
        try:
            iterations = int(iterations_raw) if iterations_raw is not None else 3
        except (TypeError, ValueError):
            iterations = 3

        iterations = max(1, min(iterations, 12))

        feature = compute_quantam_feature(
            glyphs=glyphs, cycle=cycle, joy=joy, curiosity=curiosity
        )
        cascade = generate_quantam_feature_sequence(
            glyphs=glyphs,
            cycle=cycle,
            joy=joy,
            curiosity=curiosity,
            iterations=iterations,
        )

        summary = cascade.get("summary", {})
        message = (
            f"Quantam feature cascade prepared for Echo Computer cycle {cycle} "
            f"with {summary.get('total_layers', iterations)} layer(s); "
            "world-first lattice proof minted."
        )

        metadata = {
            "confidence": 0.96,
            "glyphs": glyphs,
            "cycle": cycle,
            "iterations": iterations,
            "entanglement": summary.get("entanglement"),
            "world_first_proof": summary.get("world_first_proof"),
        }

        data = {
            "feature": feature,
            "cascade": cascade,
        }

        return CommandResponse(
            function="quantam_features",
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
        random_state = {
            "seed": result.random_state.get("seed"),
            "history": list(result.random_state.get("history", ())),
        }
        return {
            "halted": result.halted,
            "steps": result.steps,
            "output": list(result.output),
            "registers": dict(result.registers),
            "memory": dict(result.memory),
            "diagnostics": list(result.diagnostics),
            "quantum_registers": quantum_registers,
            "instruction_counts": dict(result.instruction_counts),
            "random_state": random_state,
            "stack": list(result.stack),
            "call_stack": list(result.call_stack),
        }


__all__ = [
    "CommandContext",
    "CommandResponse",
    "DailyTaskRegistry",
    "EchoChatAgent",
    "FunctionCall",
    "FunctionRouter",
    "FunctionSpec",
    "FeatureBlueprintRegistry",
    "PuzzleKnowledgeBase",
    "WeeklyRitualRegistry",
]
