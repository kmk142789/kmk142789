"""Stub adapter for the aladdin_app repository."""

from __future__ import annotations

from typing import Dict


def status() -> Dict[str, str]:
    """Return placeholder status information."""

    return {
        "repository": "aladdin_app",
        "status": "ok",
        "details": "TODO: integrate with aladdin_app API",
    }


def list_examples() -> Dict[str, list[str]]:
    """Return illustrative examples."""

    return {
        "examples": [
            "Launch core workflow",
            "Query recent research notes",
        ],
        "note": "Replace with real data once the SDK is available.",
    }


PLUGIN: Dict[str, object] = {
    "name": "aladdin",
    "version": "0.1.0",
    "tools": {
        "status": status,
        "list_examples": list_examples,
    },
}
