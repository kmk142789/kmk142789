"""Creative bloom utilities for cultivating Echo ideas."""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Sequence, Tuple

from echo.thoughtlog import thought_trace

__all__ = [
    "BloomSeed",
    "BloomPetal",
    "BloomReport",
    "CreativeBloom",
    "render_bloom_table",
]


@dataclass(frozen=True)
class BloomSeed:
    """Seed information used to cultivate creative blooms.

    Parameters
    ----------
    theme:
        Human readable description of the seed.
    intensity:
        A floating point value between ``0`` and ``1`` capturing how vibrant the
        idea currently feels.
    sparks:
        Optional descriptors that offer additional colour for the bloom.
    """

    theme: str
    intensity: float
    sparks: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        cleaned = self.theme.strip()
        if not cleaned:
            raise ValueError("theme must not be empty")
        object.__setattr__(self, "theme", cleaned)
        object.__setattr__(self, "intensity", _clamp(self.intensity))
        object.__setattr__(
            self,
            "sparks",
            tuple(spark.strip() for spark in self.sparks if spark and spark.strip()),
        )


@dataclass(frozen=True)
class BloomPetal:
    """A single cultivated bloom petal."""

    headline: str
    vividness: float
    tags: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "headline", self.headline.strip())
        object.__setattr__(self, "vividness", round(_clamp(self.vividness), 6))
        object.__setattr__(self, "tags", tuple(tag.strip() for tag in self.tags if tag.strip()))


@dataclass(frozen=True)
class BloomReport:
    """Summary of cultivated bloom petals."""

    petals: Tuple[BloomPetal, ...]
    average_vividness: float
    theme_summary: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "petals", tuple(self.petals))
        object.__setattr__(self, "theme_summary", tuple(theme.strip() for theme in self.theme_summary))
        object.__setattr__(self, "average_vividness", round(_clamp(self.average_vividness), 6))

    @property
    def petal_count(self) -> int:
        """Return the number of petals captured in the report."""

        return len(self.petals)


class CreativeBloom:
    """Cultivate :class:`BloomPetal` collections from :class:`BloomSeed` inputs."""

    def __init__(self, base_vividness: float = 0.5) -> None:
        self._base_vividness = _clamp(base_vividness)

    def cultivate(self, seeds: Sequence[BloomSeed], *, cycles: int = 3) -> BloomReport:
        """Grow bloom petals from the provided *seeds*.

        Parameters
        ----------
        seeds:
            A non-empty sequence of :class:`BloomSeed` instances.
        cycles:
            Number of iterations used to expand each seed.  Higher values result
            in more petals and gradually increase vividness towards the seed's
            intensity.
        """

        if not seeds:
            raise ValueError("seeds must not be empty")
        if cycles <= 0:
            raise ValueError("cycles must be a positive integer")

        task = "echo.creative_bloom.cultivate"
        meta = {"seed_count": len(seeds), "cycles": cycles, "base": self._base_vividness}

        with thought_trace(task=task, meta=meta) as tl:
            petals: list[BloomPetal] = []
            themes: list[str] = []

            for seed in seeds:
                themes.append(seed.theme)
                for cycle in range(1, cycles + 1):
                    vividness = self._blend_vividness(seed.intensity, cycle, cycles)
                    headline = f"{seed.theme} :: cycle {cycle}"
                    tags = seed.sparks + (f"cycle-{cycle}",)
                    petal = BloomPetal(headline=headline, vividness=vividness, tags=tags)
                    petals.append(petal)
                    tl.logic(
                        "petal",
                        task,
                        "petal cultivated",
                        {"theme": seed.theme, "cycle": cycle, "vividness": petal.vividness},
                    )

            average = mean(petal.vividness for petal in petals) if petals else 0.0
            report = BloomReport(petals=tuple(petals), average_vividness=average, theme_summary=tuple(themes))
            tl.harmonic("report", task, "bloom report prepared", {"petals": report.petal_count})
            return report

    def _blend_vividness(self, target: float, cycle: int, total_cycles: int) -> float:
        ratio = cycle / total_cycles
        return self._base_vividness + (target - self._base_vividness) * ratio


def render_bloom_table(report: BloomReport) -> str:
    """Render a readable table describing the bloom *report*."""

    if not report.petals:
        return "No bloom petals available. Invite new seeds to the garden."

    header = ("Petal", "Vividness", "Tags")
    rows = []
    for index, petal in enumerate(report.petals, start=1):
        tags = ", ".join(petal.tags) if petal.tags else "(untagged)"
        rows.append((f"{index}. {petal.headline}", f"{petal.vividness:.3f}", tags))

    widths = [
        max(len(header[col]), max(len(row[col]) for row in rows)) for col in range(len(header))
    ]

    lines = [f"Average vividness :: {report.average_vividness:.3f}", ""]
    lines.append(" | ".join(h.ljust(widths[i]) for i, h in enumerate(header)))
    lines.append("-+-".join("".ljust(widths[i], "-") for i in range(len(header))))
    for row in rows:
        lines.append(" | ".join(value.ljust(widths[i]) for i, value in enumerate(row)))
    return "\n".join(lines)


def _clamp(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value
