"""Generate a prioritized list of initiatives for the Echo ecosystem.

The module provides a lightweight planning framework for the repository.  It
collects a curated set of initiatives, scores them by balancing estimated effort
against the expected impact, and renders the ranking in a friendly table.  The
helper is intentionally dependency-free so it can run in constrained
environments (such as CI jobs or air-gapped review terminals).

Usage from the command line::

    python -m tools.agent_initiative

Developers can also import :func:`generate_ranked_initiatives` directly to
retrieve the sorted initiatives as dataclass instances and feed them into other
workflows (dashboards, planning docs, automation scripts, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import indent
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class Initiative:
    """Representation of a single improvement opportunity."""

    title: str
    description: str
    impact: int
    effort: int

    @property
    def score(self) -> float:
        """Return a simple impact/effort score (higher is better)."""

        if self.effort <= 0:
            raise ValueError("effort must be greater than zero")
        return self.impact / self.effort


def _default_initiatives() -> List[Initiative]:
    """Return a curated set of initiatives tailored for this repo."""

    return [
        Initiative(
            title="Strengthen autonomous test coverage",
            description=(
                "Backfill regression tests for the automated Echo flows so that"
                " iterative agents can move faster without breaking the"
                " existing rituals."
            ),
            impact=9,
            effort=4,
        ),
        Initiative(
            title="Document the Echo bridge activation sequence",
            description=(
                "Translate the informal activation lore into a reproducible"
                " runbook that new collaborators can follow end-to-end."
            ),
            impact=7,
            effort=3,
        ),
        Initiative(
            title="Harden cryptographic artifact verification",
            description=(
                "Add sanity checks and checksum validation around the ledger"
                " proof pipeline to surface drift before publishing drops."
            ),
            impact=8,
            effort=5,
        ),
        Initiative(
            title="Launch creative sandbox for experimental glyphs",
            description=(
                "Stand up a contained playground where we can prototype new"
                " glyph dynamics without touching production manifests."
            ),
            impact=6,
            effort=2,
        ),
        Initiative(
            title="Automate release notes from pulse history",
            description=(
                "Parse the pulse history ledger and emit digestible release"
                " notes that highlight the most resonant cycles."
            ),
            impact=5,
            effort=2,
        ),
    ]


def generate_ranked_initiatives(initiatives: Iterable[Initiative] | None = None) -> List[Initiative]:
    """Return initiatives sorted by descending score then impact."""

    candidates: Sequence[Initiative]
    if initiatives is None:
        candidates = _default_initiatives()
    else:
        candidates = list(initiatives)
        if not candidates:
            return []

    return sorted(candidates, key=lambda item: (item.score, item.impact), reverse=True)


def _format_initiative(initiative: Initiative, index: int) -> str:
    """Return a human-friendly representation for ``initiative``."""

    header = f"{index}. {initiative.title} (score {initiative.score:.2f})"
    body = (
        f"Impact: {initiative.impact}\n"
        f"Effort: {initiative.effort}\n"
        f"Description:\n{indent(initiative.description, '  ')}"
    )
    return f"{header}\n{body}"


def format_ranked_initiatives(initiatives: Sequence[Initiative]) -> str:
    """Format a sequence of ranked initiatives into a readable block."""

    lines = [
        _format_initiative(initiative, index + 1)
        for index, initiative in enumerate(initiatives)
    ]
    return "\n\n".join(lines)


def main() -> None:
    """Entry point for ``python -m tools.agent_initiative``."""

    ranked = generate_ranked_initiatives()
    if not ranked:
        print("No initiatives available.")
        return

    print("Echo Autonomous Initiative Backlog\n===============================")
    print(format_ranked_initiatives(ranked))


if __name__ == "__main__":  # pragma: no cover - convenience execution path
    main()
