"""Core agent that orchestrates plugin execution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from . import memory
from .registry import PluginRegistry
from .types import ToolCallEvent, ToolCallResult
from .utils import fuzzy_find, parse_arguments, safe_truncate


class EchoAgent:
    """Interactive orchestrator for plugin tools."""

    def __init__(self, registry: PluginRegistry | None = None) -> None:
        self.registry = registry or PluginRegistry()

    def route(self, text: str) -> Dict[str, Any]:
        """Parse a text command and execute it."""

        text = text.strip()
        if not text:
            return ToolCallResult("", "", False, None, "Empty command").as_dict()

        try:
            plugin, tool, args, kwargs = self._parse_command(text)
        except ValueError as exc:
            return ToolCallResult("", "", False, None, str(exc)).as_dict()

        return self.execute(plugin, tool, *args, **kwargs)

    def execute(self, plugin: str, tool: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute a tool from a plugin and log the result."""

        success = True
        result: Any = None
        error: str | None = None
        try:
            result = self.registry.call(plugin, tool, *args, **kwargs)
        except Exception as exc:
            success = False
            error = str(exc)

        event = ToolCallEvent(
            timestamp=datetime.utcnow(),
            plugin=plugin,
            tool=tool,
            args=list(args),
            kwargs=dict(kwargs),
            success=success,
            result_summary=safe_truncate(result),
            error=error,
        )
        memory.log_event(event)

        payload = ToolCallResult(plugin=plugin, tool=tool, success=success, result=result, error=error)
        return payload.as_dict()

    # ------------------------------------------------------------------
    def _parse_command(self, text: str) -> Tuple[str, str, List[str], Dict[str, Any]]:
        tokens = text.split()
        if not tokens:
            raise ValueError("No command provided")

        plugin: str | None = None
        tool: str | None = None
        remainder: List[str] = []

        first = tokens[0]
        if "." in first:
            plugin, tool = first.split(".", 1)
            remainder = tokens[1:]
        elif len(tokens) >= 2 and tokens[0] in self.registry.list_plugins():
            plugin = tokens[0]
            tool = tokens[1]
            remainder = tokens[2:]
        else:
            plugin = self._fuzzy_plugin(first)
            if plugin:
                tool = self._fuzzy_tool(plugin, tokens[1] if len(tokens) > 1 else text)
                remainder = tokens[2:]

        if not plugin:
            plugin = self._fuzzy_plugin(text)
        if plugin and not tool:
            tool = self._fuzzy_tool(plugin, text)

        if not plugin or not tool:
            raise ValueError("Unable to determine plugin and tool from input")

        args, kwargs = parse_arguments(remainder)
        return plugin, tool, args, kwargs

    def _fuzzy_plugin(self, query: str) -> str | None:
        plugins = self.registry.list_plugins()
        if query in plugins:
            return query
        return fuzzy_find(query, plugins)

    def _fuzzy_tool(self, plugin: str, query: str) -> str | None:
        try:
            tools = self.registry.list_tools(plugin)
        except KeyError:
            return None
        if query in tools:
            return query
        return fuzzy_find(query, tools)


__all__ = ["EchoAgent"]
