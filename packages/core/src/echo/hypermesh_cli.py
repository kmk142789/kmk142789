"""Typer-based CLI for the HyperMesh resonance engine."""

from __future__ import annotations

from pathlib import Path
from typing import List

import json

import typer

from .hypermesh_engine import HyperMeshBlueprint, PulseCascadePlanner

try:  # pragma: no cover - fallback only triggered in dev environments
    from rich.console import Console  # type: ignore
except Exception:  # pragma: no cover - fallback implementation
    class Console:  # type: ignore[misc]
        def print(self, value: object) -> None:
            if hasattr(value, "columns") and hasattr(value, "rows"):
                headers = [c["header"] for c in value.columns]
                print(" | ".join(headers))
                print("-" * (len(headers) * 8))
                for row in value.rows:
                    print(" | ".join(row))
            else:
                print(value)

        def print_json(self, *, data: object) -> None:
            print(json.dumps(data, indent=2))

        def rule(self, text: str) -> None:
            print(f"--- {text} ---")


app = typer.Typer(add_completion=False, help="HyperMesh constellation simulator")
console = Console()


def _load_blueprint(path: Path) -> HyperMeshBlueprint:
    if not path.exists():
        raise typer.BadParameter(f"Blueprint not found: {path}")
    return HyperMeshBlueprint.from_file(path)


@app.command()
def simulate(
    blueprint: Path = typer.Argument(..., help="Path to a HyperMesh blueprint JSON file"),
    steps: int = typer.Option(6, help="Number of propagation steps"),
    damping: float = typer.Option(0.82, help="Damping applied to each iteration"),
    noise: float = typer.Option(0.03, help="Thermal noise amplitude"),
) -> None:
    """Simulate a pulse cascade and display a rich table."""

    spec = _load_blueprint(blueprint)
    mesh = spec.build()
    seed = spec.seed
    history = mesh.propagate_pulse(seed, steps=steps, damping=damping, thermal_noise=noise)
    console.print(mesh.generate_report(history))


@app.command()
def plan(
    blueprint: Path = typer.Argument(..., help="Path to a HyperMesh blueprint JSON file"),
    seeds: List[str] = typer.Option([], "--seed", help="Seed nodes for cascade planning"),
    horizon: int = typer.Option(5, help="Propagation horizon for each seed"),
) -> None:
    """Plan a multi-seed cascade strategy."""

    spec = _load_blueprint(blueprint)
    mesh = spec.build()
    seeds = seeds or [spec.seed]
    planner = PulseCascadePlanner(mesh)
    plan_payload = planner.plan(seeds=seeds, horizon=horizon)
    console.rule("Pulse Cascade Planner")
    console.print_json(data=json.loads(json.dumps(plan_payload)))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
