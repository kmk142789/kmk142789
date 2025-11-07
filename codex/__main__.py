"""Entry point for invoking :mod:`codex` as a module or script.

The historical tooling supported ``python -m codex`` as well as the slightly
less conventional ``python path/to/codex`` form that executes the package's
``__main__`` module directly.  The latter sets ``__package__`` to ``None`` which
breaks relative imports.  To preserve backwards compatibility we detect that
scenario, ensure the repository root is importable, and then delegate to the
package-level :func:`codex.main` implementation.
"""

from __future__ import annotations

from pathlib import Path
import sys


def _load_package_main():
    """Return the :func:`codex.main` callable regardless of execution context."""

    if __package__ in {None, ""}:
        package_root = Path(__file__).resolve().parent
        repo_root = package_root.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from codex import main as codex_main  # type: ignore
    else:  # pragma: no cover - exercised when imported as a module
        from . import main as codex_main  # type: ignore

    return codex_main


def main() -> None:  # pragma: no cover - thin wrapper
    codex_main = _load_package_main()
    codex_main()


if __name__ == "__main__":  # pragma: no cover - module execution hook
    main()
