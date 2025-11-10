"""Utility for locating ``AGENTS.md`` files within the repository.

The assistant guidelines rely on ``AGENTS.md`` files that can live anywhere in
the tree. When working on large repos it is easy to miss a nested set of
instructions, so this helper walks the tree and reports their locations along
with the directory scope they govern.  It is intentionally lightweight so it
can run quickly from the command line or inside other tooling.

Example::

    $ python scripts/find_agents.py
    Found 2 AGENTS.md files
    - AGENTS.md (scope: .)
    - apps/service/AGENTS.md (scope: apps/service)

You can also scan a subset of the tree by providing a path argument::

    $ python scripts/find_agents.py apps

This script skips common dependency folders (``.git``, ``node_modules``,
``__pycache__``) to avoid unnecessary filesystem churn.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable


SKIP_DIRS: tuple[str, ...] = (".git", "node_modules", "__pycache__")


def iter_agent_files(root: Path) -> Iterable[Path]:
    """Yield ``AGENTS.md`` files under *root*.

    The walk is performed iteratively with a manual stack so we can filter
    directories before the OS does the recursion.  This keeps the traversal
    snappy even in large repositories.
    """

    stack = [root]
    while stack:
        current = stack.pop()
        try:
            for entry in current.iterdir():
                if entry.is_dir():
                    if entry.name in SKIP_DIRS:
                        continue
                    stack.append(entry)
                elif entry.name == "AGENTS.md":
                    yield entry
        except PermissionError:
            # If we do not have access to a directory we simply skip it.
            continue


def describe_scope(path: Path, base: Path) -> str:
    """Return a human-readable scope for the discovered ``AGENTS.md`` file."""

    relative_parent = path.parent.relative_to(base)
    if relative_parent == Path("."):
        return "."
    return str(relative_parent)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "start",
        nargs="?",
        default=Path.cwd(),
        type=Path,
        help="Path to start the search from (defaults to current working directory)",
    )
    args = parser.parse_args()

    start_path = args.start.resolve()
    if not start_path.exists():
        parser.error(f"start path does not exist: {start_path}")

    agents = sorted(iter_agent_files(start_path))
    if not agents:
        print("No AGENTS.md files found.")
        return os.EX_OK

    print(f"Found {len(agents)} AGENTS.md file{'s' if len(agents) != 1 else ''}")
    for agent in agents:
        scope = describe_scope(agent, start_path)
        print(f"- {agent.relative_to(start_path)} (scope: {scope})")

    return os.EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
