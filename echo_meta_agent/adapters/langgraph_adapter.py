"""Stub adapter for LangGraph repositories."""

from __future__ import annotations

from typing import Dict, List


def repositories() -> List[str]:
    """List placeholder LangGraph forks detected locally."""

    return [
        "LangGraph-core",
        "LangGraph-experiments",
    ]


def roadmap() -> Dict[str, str]:
    """Return a speculative roadmap description."""

    return {
        "focus": "Prototype integrations with the LangGraph planning engine.",
        "todo": "TODO: connect to LangGraph APIs when available.",
    }


PLUGIN: Dict[str, object] = {
    "name": "langgraph",
    "version": "0.1.0",
    "tools": {
        "repositories": repositories,
        "roadmap": roadmap,
    },
}
