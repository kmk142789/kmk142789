"""Thin orchestration helpers around :mod:`dominion.cascade`."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from dominion.cascade import build_cascade_plan
from dominion.plans import DominionPlan

__all__ = [
    "DominionCascadeConfig",
    "DominionCascadeResult",
    "run_dominion_cascade",
    "main",
]


@dataclass(frozen=True)
class DominionCascadeConfig:
    """Configuration describing how a cascade plan should be generated."""

    output_dir: Path
    plan_dir: Path
    plan_name: str | None = None
    manifest_chars: int = 240
    glyph_cycle: Sequence[str] | None = None
    timestamp: int | None = None
    ascii_width: int = 41
    ascii_height: int = 21
    enable_network: bool = False
    persist_artifact: bool = False


@dataclass(frozen=True)
class DominionCascadeResult:
    """Container bundling the generated plan and persisted location."""

    plan: DominionPlan
    plan_path: Path

    def to_dict(self) -> dict[str, object]:
        payload = self.plan.to_dict()
        payload["plan_path"] = str(self.plan_path)
        return payload


def run_dominion_cascade(config: DominionCascadeConfig) -> DominionCascadeResult:
    """Generate a Dominion cascade plan according to ``config``."""

    if config.manifest_chars <= 0:
        raise ValueError("manifest_chars must be positive")
    if config.ascii_width <= 0 or config.ascii_height <= 0:
        raise ValueError("ascii dimensions must be positive")

    plan = build_cascade_plan(
        config.output_dir,
        manifest_chars=config.manifest_chars,
        glyph_cycle=list(config.glyph_cycle) if config.glyph_cycle else None,
        timestamp=config.timestamp,
        ascii_width=config.ascii_width,
        ascii_height=config.ascii_height,
        enable_network=config.enable_network,
        persist_artifact=config.persist_artifact,
        source="echo.dominion_cascade",
    )

    plan_dir = config.plan_dir
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_filename = config.plan_name or f"plan_{plan.plan_id}.json"
    plan_path = plan_dir / plan_filename
    plan.write(plan_path)

    return DominionCascadeResult(plan=plan, plan_path=plan_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a Dominion cascade plan using safe defaults.")
    parser.add_argument("--output-dir", type=Path, default=Path("build/dominion/cascade"), help="Directory for cascade artefacts.")
    parser.add_argument(
        "--plan-dir",
        type=Path,
        default=Path("build/dominion/plans"),
        help="Directory where the Dominion plan will be written.",
    )
    parser.add_argument("--plan-name", help="Optional filename for the emitted plan (defaults to plan_<digest>.json).")
    parser.add_argument(
        "--manifest-chars",
        type=int,
        default=240,
        help="Number of characters captured in the manifest excerpt (default: 240).",
    )
    parser.add_argument(
        "--glyph-cycle",
        help="Optional glyph sequence forwarded to the cascade renderer (e.g. ∇⊸≋∇).",
    )
    parser.add_argument("--timestamp", type=int, help="Optional timestamp forwarded to the cascade renderer.")
    parser.add_argument("--ascii-width", type=int, default=41, help="Width of the ASCII constellation map (default: 41).")
    parser.add_argument("--ascii-height", type=int, default=21, help="Height of the ASCII constellation map (default: 21).")
    parser.add_argument("--enable-network", action="store_true", help="Allow the cascade to perform real network propagation.")
    parser.add_argument(
        "--persist-artifact",
        action="store_true",
        help="Persist the evolver artefact produced during the cascade run.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the plan metadata as JSON.")
    return parser


def _format_summary(result: DominionCascadeResult) -> str:
    plan = result.plan
    lines = [
        f"Dominion plan {plan.plan_id} written to {result.plan_path}",
        f"Source: {plan.source}",
        f"Intents recorded: {len(plan.intents)}",
    ]
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    glyph_cycle = list(args.glyph_cycle) if args.glyph_cycle else None

    try:
        config = DominionCascadeConfig(
            output_dir=args.output_dir,
            plan_dir=args.plan_dir,
            plan_name=args.plan_name,
            manifest_chars=args.manifest_chars,
            glyph_cycle=glyph_cycle,
            timestamp=args.timestamp,
            ascii_width=args.ascii_width,
            ascii_height=args.ascii_height,
            enable_network=args.enable_network,
            persist_artifact=args.persist_artifact,
        )
        result = run_dominion_cascade(config)
    except ValueError as exc:
        parser.error(str(exc))
        raise SystemExit(2)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(_format_summary(result))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
