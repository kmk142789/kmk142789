"""Generate a Markdown table describing the Echo manifest."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from echo import load_manifest


def _format_dependencies(dependencies: Iterable[str]) -> str:
    deps = list(dependencies)
    if not deps:
        return "—"
    return ", ".join(deps)


def build_table() -> str:
    manifest = load_manifest()
    headers = ["Name", "Type", "Path", "Version", "Digest", "Dependencies"]
    rows = []
    for component in manifest.get("components", []):
        rows.append(
            [
                component.get("name", ""),
                component.get("type", ""),
                component.get("path", ""),
                component.get("version", ""),
                component.get("digest", ""),
                _format_dependencies(component.get("dependencies", [])),
            ]
        )
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def main() -> None:
    print(build_table())


if __name__ == "__main__":
    main()
