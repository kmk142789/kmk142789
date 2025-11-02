"""Entry point for ``python -m codex`` matching the historical CLI."""
from __future__ import annotations

# ``codex`` proxied module exposes ``main`` at the top level.


def main() -> None:  # pragma: no cover - thin wrapper
    from . import main as codex_main  # type: ignore

    codex_main()


if __name__ == "__main__":  # pragma: no cover - module execution hook
    main()
