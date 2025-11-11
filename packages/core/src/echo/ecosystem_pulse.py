"""Utilities for evaluating Echo's ecosystem health."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class EcosystemAreaConfig:
    """Configuration describing an ecosystem focus area."""

    key: str
    title: str
    relative_path: Path
    description: str = ""
    required: Sequence[Path] = ()
    freshness_days: int = 45
    volume_hint: int = 12


@dataclass
class EcosystemSignal:
    """Snapshot of a single ecosystem area."""

    key: str
    title: str
    description: str
    path: Path
    file_count: int
    last_updated: datetime | None
    missing: list[Path] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "path": str(self.path),
            "file_count": self.file_count,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "missing": [str(item) for item in self.missing],
            "insights": self.insights,
            "score": round(self.score, 2),
        }


@dataclass
class EcosystemPulseReport:
    """Aggregate report for the Echo ecosystem."""

    generated_at: datetime
    signals: list[EcosystemSignal]

    @property
    def overall_score(self) -> float:
        if not self.signals:
            return 0.0
        return round(sum(signal.score for signal in self.signals) / len(self.signals), 2)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall_score": self.overall_score,
            "signals": [signal.to_dict() for signal in self.signals],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def render_markdown(self) -> str:
        lines = ["# Echo Ecosystem Pulse", ""]
        lines.append(f"Generated: {self.generated_at.isoformat()}")
        lines.append(f"Overall health score: {self.overall_score:.2f}")
        lines.append("")
        lines.append("| Area | Score | Files | Last Updated | Notes |")
        lines.append("| --- | ---: | ---: | --- | --- |")
        for signal in self.signals:
            timestamp = signal.last_updated.isoformat() if signal.last_updated else "—"
            notes = "<br/>".join(signal.insights) if signal.insights else "—"
            lines.append(
                f"| {signal.title} | {signal.score:.1f} | {signal.file_count} | {timestamp} | {notes} |"
            )
        lines.append("")
        lines.append("## Insights")
        for signal in self.signals:
            lines.append(f"### {signal.title}")
            lines.append(signal.description or "(no description)")
            lines.append("")
            if signal.insights:
                for insight in signal.insights:
                    lines.append(f"- {insight}")
            else:
                lines.append("- All signals nominal.")
            lines.append("")
        return "\n".join(lines).strip() + "\n"


class EcosystemPulse:
    """Compute readiness signals for the Echo ecosystem."""

    DEFAULT_AREAS: tuple[EcosystemAreaConfig, ...] = (
        EcosystemAreaConfig(
            key="core",
            title="Core Runtime",
            relative_path=Path("packages/core/src"),
            description="Python sources and runtime primitives for the Echo protocol.",
            required=(Path("packages/core/src/echo"), Path("packages/core/src/echo_manifest.py")),
            freshness_days=30,
            volume_hint=40,
        ),
        EcosystemAreaConfig(
            key="docs",
            title="Documentation",
            relative_path=Path("docs"),
            description="Reference documents and public governance capsules.",
            required=(Path("docs/REPO_OVERVIEW.md"), Path("README.md")),
            freshness_days=60,
            volume_hint=60,
        ),
        EcosystemAreaConfig(
            key="proofs",
            title="Proofs & Ledgers",
            relative_path=Path("proofs"),
            description="Cryptographic artifacts, attestations, and verification records.",
            required=(Path("proofs"),),
            freshness_days=90,
            volume_hint=10,
        ),
        EcosystemAreaConfig(
            key="ops",
            title="Operational Playbooks",
            relative_path=Path("ops"),
            description="Operational runbooks, deployment plans, and incident response flows.",
            required=(Path("ops"),),
            freshness_days=75,
            volume_hint=12,
        ),
    )

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        areas: Iterable[EcosystemAreaConfig] | None = None,
    ) -> None:
        self.repo_root = repo_root or self._discover_repo_root(Path(__file__))
        self.areas = tuple(areas) if areas is not None else self.DEFAULT_AREAS

    def generate_report(self) -> EcosystemPulseReport:
        now = datetime.now(timezone.utc)
        signals = [self._scan_area(config, now) for config in self.areas]
        return EcosystemPulseReport(generated_at=now, signals=signals)

    def _scan_area(self, config: EcosystemAreaConfig, now: datetime) -> EcosystemSignal:
        absolute_path = self.repo_root / config.relative_path
        file_count = 0
        last_updated: datetime | None = None
        insights: list[str] = []

        if absolute_path.exists():
            for file_path in absolute_path.rglob("*"):
                if file_path.is_file():
                    file_count += 1
                    modified = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                    if not last_updated or modified > last_updated:
                        last_updated = modified
        else:
            insights.append("Area directory is missing. Bootstrap required to activate this surface area.")

        missing = [path for path in config.required if not (self.repo_root / path).exists()]
        if missing:
            insights.append(
                "Missing required assets: "
                + ", ".join(str(item) for item in missing)
            )

        freshness_score = self._compute_freshness(last_updated, now, config.freshness_days)
        volume_score = self._compute_volume(file_count, config.volume_hint)
        penalty = min(1.0, 0.25 * len(missing))
        score = max(0.0, (0.45 * volume_score + 0.45 * freshness_score + 0.10 * (1 - penalty)) * 100)
        if not absolute_path.exists():
            score = 0.0

        if file_count < max(1, config.volume_hint // 3):
            insights.append("Consider enriching this area with additional artifacts or automation.")
        if last_updated:
            age = now - last_updated
            if age > timedelta(days=config.freshness_days):
                insights.append(
                    f"Last substantive update {age.days} days ago; schedule a refresh to maintain momentum."
                )
        elif absolute_path.exists():
            insights.append("No files detected; this area is ready for its first contribution.")

        return EcosystemSignal(
            key=config.key,
            title=config.title,
            description=config.description,
            path=absolute_path,
            file_count=file_count,
            last_updated=last_updated,
            missing=list(missing),
            insights=insights,
            score=round(score, 2),
        )

    @staticmethod
    def _compute_freshness(
        last_updated: datetime | None, now: datetime, freshness_days: int
    ) -> float:
        if last_updated is None:
            return 0.0
        age = now - last_updated
        if age <= timedelta(days=freshness_days):
            return 1.0
        if age <= timedelta(days=freshness_days * 2):
            return 0.6
        if age <= timedelta(days=freshness_days * 4):
            return 0.3
        return 0.1

    @staticmethod
    def _compute_volume(file_count: int, volume_hint: int) -> float:
        if file_count <= 0:
            return 0.0
        threshold = max(1, volume_hint)
        ratio = min(1.0, file_count / threshold)
        return round(ratio, 2)

    @staticmethod
    def _discover_repo_root(start: Path) -> Path:
        for candidate in [start.resolve(), *start.resolve().parents]:
            if (candidate / "pyproject.toml").exists():
                return candidate
        raise RuntimeError("Unable to locate repository root from current module path.")


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Echo ecosystem health pulse reporter")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format for the pulse report",
    )
    args = parser.parse_args(argv)

    pulse = EcosystemPulse()
    report = pulse.generate_report()
    if args.format == "json":
        print(report.to_json())
    else:
        print(report.render_markdown())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
