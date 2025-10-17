"""Reporting helpers for Echo Atlas."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .domain import AtlasSummary
from .schema import validate_graph
from .utils import ensure_directory, utcnow


def build_report(summary: AtlasSummary) -> str:
    lines = ["# Echo Atlas Summary", "", f"Generated: {utcnow()}", ""]
    lines.append("## Ownership")
    for entity, total in summary.totals.items():
        lines.append(f"- **{entity}**: {total}")
    lines.append("")

    lines.append("## Relations")
    for relation, total in summary.relations.items():
        lines.append(f"- **{relation}**: {total}")
    lines.append("")

    lines.append("## Recent Changes")
    if summary.recent_changes:
        for change in summary.recent_changes[:10]:
            lines.append(
                f"- {change['timestamp']}: {change['change_type']} {change['entity_id']}"
            )
    else:
        lines.append("- No changes recorded.")
    lines.append("")

    lines.append("## Automations")
    bot_total = summary.totals.get("Bot", 0)
    if bot_total:
        lines.append(f"- Bots active: {bot_total}. Review webhook settings regularly.")
    else:
        lines.append("- No bots detected in the current atlas snapshot.")
    lines.append("")

    lines.append("## Highlights")
    if summary.highlights:
        lines.append(summary.highlights)
    else:
        lines.append("No highlights stored yet.")
    lines.append("")

    lines.append("## Assets & Endpoints")
    lines.append("Refer to atlas nodes for full metadata.")
    lines.append("")

    return "\n".join(lines)


def write_report(path: Path, content: str) -> None:
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")


def export_graph(path: Path, data: Mapping[str, object]) -> None:
    validate_graph(dict(data))
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        import json

        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
