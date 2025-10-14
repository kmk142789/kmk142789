"""Shared types for the Echo Meta Agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol


class Tool(Protocol):
    """Callable signature for a tool."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - Protocol stub
        ...


@dataclass(slots=True)
class ToolCallEvent:
    """Representation of a tool call logged to memory."""

    timestamp: datetime
    plugin: str
    tool: str
    args: List[Any]
    kwargs: Dict[str, Any]
    success: bool
    result_summary: str
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable dictionary representation."""

        payload: Dict[str, Any] = {
            "timestamp": self.timestamp.isoformat(),
            "plugin": self.plugin,
            "tool": self.tool,
            "args": self.args,
            "kwargs": self.kwargs,
            "success": self.success,
            "result_summary": self.result_summary,
        }
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass(slots=True)
class ToolCallResult:
    """Response payload returned to callers."""

    plugin: str
    tool: str
    success: bool
    result: Any
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        """Convert to JSON friendly dict."""

        payload: Dict[str, Any] = {
            "plugin": self.plugin,
            "tool": self.tool,
            "success": self.success,
            "result": self.result,
        }
        if self.error is not None:
            payload["error"] = self.error
        return payload


PluginSpec = Dict[str, Any]
ToolMap = Dict[str, Tool]
