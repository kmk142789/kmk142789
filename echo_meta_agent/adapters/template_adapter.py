"""Template adapter demonstrating the plugin protocol."""

from __future__ import annotations

from typing import Dict


def hello(name: str = "world") -> str:
    """Return a friendly greeting."""

    return f"Hello, {name}!"


PLUGIN: Dict[str, object] = {
    "name": "template",
    "version": "0.1.0",
    "tools": {
        "hello": hello,
    },
}
