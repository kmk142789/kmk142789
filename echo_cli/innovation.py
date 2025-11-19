"""Innovation intelligence Typer utilities."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import List, Mapping, Optional, Sequence

try:  # pragma: no cover - optional dependency
    import typer
except ModuleNotFoundError:  # pragma: no cover - fallback Typer shim
    class _FallbackExit(SystemExit):
        def __init__(self, code: int = 0):
            super().__init__(code)

    class _FallbackContext:
        def __init__(self) -> None:
            self.obj: dict[str, object] | None = None

    class _FallbackTyper:
        def __init__(self, *_, **__):
            self.commands: dict[str, object] = {}

        def command(self, *_, **__):
            def decorator(func):
                return func

            return decorator

        def __call__(self, *_, **__):  # pragma: no cover - unused
            raise RuntimeError("Typer is unavailable in this environment")

    def _option(default=None, *_, **__):
        return default

    def _echo(message: object = "") -> None:
        print(message)

    typer = SimpleNamespace(  # type: ignore[assignment]
        Typer=_FallbackTyper,
        Context=_FallbackContext,
        Option=_option,
        Argument=_option,
        Exit=_FallbackExit,
        BadParameter=ValueError,
        echo=_echo,
    )

try:  # pragma: no cover - optional dependency
    from rich.console import Console
    from rich.table import Table
except ModuleNotFoundError:  # pragma: no cover - fallback printing
    Console = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]

from .progressive_features import (
    generate_innovation_hotspots,
    generate_innovation_orbit,
    generate_innovation_radar,
)

app = typer.Typer(help="Innovation intelligence utilities", no_args_is_help=True)
console = Console() if Console else None


def _parse_node_specs(specs: Sequence[str]) -> list[dict[str, object]]:
    parsed: list[dict[str, object]] = []
    for spec in specs:
        parts = spec.split(":")
        if len(parts) not in {5, 6, 7}:
            raise ValueError(
                "nodes must follow 'name:novelty:adoption:risk:investment[:horizon[:signal]]' format"
            )
        name = parts[0].strip()
        if not name:
            raise ValueError("node name cannot be empty")
        try:
            novelty = float(parts[1])
            adoption = float(parts[2])
            risk = float(parts[3])
            investment = float(parts[4])
        except ValueError as exc:
            raise ValueError("node metrics must be numeric") from exc
        node: dict[str, object] = {
            "name": name,
            "novelty": novelty,
            "adoption": adoption,
            "risk": risk,
            "investment": investment,
        }
        if len(parts) >= 6 and parts[5].strip():
            node["horizon"] = parts[5].strip()
        if len(parts) == 7 and parts[6].strip():
            try:
                node["signal_strength"] = float(parts[6])
            except ValueError as exc:  # pragma: no cover - defensive
                raise ValueError("signal must be numeric") from exc
        parsed.append(node)
    return parsed


def _load_nodes_file(path: Path | None) -> list[dict[str, object]]:
    if path is None:
        return []
    try:
        data = path.read_text()
    except OSError as exc:  # pragma: no cover - file access
        raise ValueError(str(exc)) from exc
    import json

    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError("innovation profile must be valid JSON") from exc
    if not isinstance(payload, list):
        raise ValueError("innovation profile must be a JSON array")
    nodes: list[dict[str, object]] = []
    for idx, entry in enumerate(payload):
        if not isinstance(entry, Mapping):
            raise ValueError(f"invalid node at index {idx}")
        nodes.append(dict(entry))
    return nodes


def _emit_table(columns: Sequence[str], rows: Sequence[Sequence[object]], title: str) -> None:
    if console is None or Table is None:
        header = " | ".join(columns)
        typer.echo(title)
        typer.echo(header)
        for row in rows:
            typer.echo(" | ".join(str(value) for value in row))
        return
    table = Table(title=title)
    for column in columns:
        table.add_column(column)
    for row in rows:
        table.add_row(*[str(value) for value in row])
    console.print(table)


@app.command("radar")
def innovation_radar(
    node: List[str] = typer.Option(
        [],
        "--node",
        "-n",
        help="Node formatted as 'Name:novelty:adoption:risk:investment[:horizon[:signal]]'.",
    ),
    profile_file: Optional[Path] = typer.Option(
        None,
        "--profile-file",
        exists=True,
        readable=True,
        resolve_path=True,
        help="JSON file describing innovation nodes.",
    ),
    json_mode: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Emit the raw JSON payload instead of a formatted summary.",
    ),
) -> None:
    """Generate a multi-horizon innovation radar."""

    try:
        nodes = _load_nodes_file(profile_file) + _parse_node_specs(node)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if not nodes:
        raise typer.BadParameter("provide --node or --profile-file")

    payload = generate_innovation_radar(nodes)
    if json_mode:
        import json

        typer.echo(json.dumps(payload))
        return

    summary = [
        f"Nodes analyzed : {payload['node_count']}",
        f"Novelty index  : {payload['novelty_index']:.2f}",
        f"Adoption index : {payload['adoption_index']:.2f}",
        f"Risk index     : {payload['risk_index']:.2f}",
        f"Signal index   : {payload['signal_index']:.2f}",
        f"Orbital momentum : {payload['orbital_momentum']:.2f}",
        f"Pioneer ratio  : {payload['pioneer_ratio']:.1%}",
        f"Investment pool : {payload['investment_total']:.2f}",
    ]
    typer.echo("\n".join(summary))

    horizon_rows = [
        (
            horizon.title(),
            details["count"],
            f"{details['avg_signal']:.2f}",
            f"{details['momentum']:.2f}",
            f"{details['risk']:.2f}",
        )
        for horizon, details in sorted(
            payload["horizon_profile"].items(), key=lambda item: item[1]["momentum"], reverse=True
        )
    ]
    if horizon_rows:
        _emit_table(
            ["Horizon", "Nodes", "Signal", "Momentum", "Risk"],
            horizon_rows,
            "Horizon profile",
        )

    signal_rows = [
        (
            entry["name"],
            entry["horizon"],
            f"{float(entry['momentum']):.2f}",
            f"{float(entry['portfolio_bias']):.2f}",
            f"{float(entry['risk']):.2f}",
        )
        for entry in sorted(
            payload["signal_matrix"], key=lambda item: item["portfolio_bias"], reverse=True
        )[:5]
    ]
    if signal_rows:
        _emit_table(
            ["Node", "Horizon", "Momentum", "Bias", "Risk"],
            signal_rows,
            "Signal vanguard",
        )

    breakthrough_rows = [
        (
            entry["name"],
            entry["horizon"],
            f"{float(entry['momentum']):.2f}",
            f"{float(entry['signal_strength']):.2f}",
        )
        for entry in payload["breakthrough_candidates"]
    ]
    if breakthrough_rows:
        _emit_table(
            ["Candidate", "Horizon", "Momentum", "Signal"],
            breakthrough_rows,
            "Breakthrough watchlist",
        )

    wavefront_rows = [
        (
            entry["horizon"].title(),
            f"T+{entry['activation_window_weeks']}w",
            f"{entry['signal_focus']:.2f}",
            f"{entry['momentum_index']:.2f}",
        )
        for entry in payload["wavefront_projection"]
    ]
    if wavefront_rows:
        _emit_table(
            ["Horizon", "Activation", "Signal", "Momentum"],
            wavefront_rows,
            "Wavefront projection",
        )


@app.command("orbit")
def innovation_orbit(
    node: List[str] = typer.Option(
        [],
        "--node",
        "-n",
        help="Node formatted as 'Name:novelty:adoption:risk:investment[:horizon[:signal]]'.",
    ),
    profile_file: Optional[Path] = typer.Option(
        None,
        "--profile-file",
        exists=True,
        readable=True,
        resolve_path=True,
        help="JSON file describing innovation nodes.",
    ),
    waves: int = typer.Option(3, "--waves", "-w", min=1, help="Number of foresight waves to emit."),
    foresight_window: int = typer.Option(
        18,
        "--foresight",
        "-f",
        min=2,
        help="Total foresight window (weeks) used to space waves.",
    ),
    json_mode: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Emit the raw JSON payload instead of a formatted summary.",
    ),
) -> None:
    """Compose an orbital innovation storyline."""

    try:
        nodes = _load_nodes_file(profile_file) + _parse_node_specs(node)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if not nodes:
        raise typer.BadParameter("provide --node or --profile-file")

    payload = generate_innovation_orbit(nodes, waves=waves, foresight_window_weeks=foresight_window)
    if json_mode:
        import json

        typer.echo(json.dumps(payload))
        return

    summary = [
        f"Nodes analyzed : {payload['node_count']}",
        f"Field intensity: {payload['field_intensity']:.3f}",
        f"Flux index    : {payload['flux_index']:.3f} ({payload['flux_alert']})",
        f"Foresight     : {payload['foresight_window_weeks']} weeks",
    ]
    typer.echo("\n".join(summary))

    synergy_rows = [
        (
            horizon.title(),
            details["volume"],
            f"{details['stability']:.2f}",
            f"{details['expansion']:.2f}",
            details["vanguard"],
        )
        for horizon, details in sorted(
            payload["horizon_synergy"].items(), key=lambda item: item[1]["expansion"], reverse=True
        )
    ]
    if synergy_rows:
        _emit_table(
            ["Horizon", "Volume", "Stability", "Expansion", "Vanguard"],
            synergy_rows,
            "Horizon synergy",
        )

    resonance_rows = [
        (
            entry["name"],
            entry["horizon"],
            f"{float(entry['orbit_score']):.2f}",
            f"{float(entry['stability']):.2f}",
            f"{float(entry['expansion']):.2f}",
        )
        for entry in payload["resonance_field"]
    ]
    if resonance_rows:
        _emit_table(
            ["Node", "Horizon", "Orbit", "Stability", "Expansion"],
            resonance_rows,
            "Resonance field",
        )

    waves_rows = [
        (
            entry["wave"],
            entry["horizon"].title(),
            f"T+{entry['activation_week']}w",
            f"{entry['confidence']:.2f}",
            entry["thesis"],
        )
        for entry in payload["orbit_waves"]
    ]
    if waves_rows:
        _emit_table(
            ["Wave", "Horizon", "Activation", "Confidence", "Thesis"],
            waves_rows,
            "Orbital foresight",
        )

    if payload["insight_threads"]:
        typer.echo("\n" + "\n".join(f"• {thread}" for thread in payload["insight_threads"]))


@app.command("hotspots")
def innovation_hotspots(
    node: List[str] = typer.Option(
        [],
        "--node",
        "-n",
        help="Node formatted as 'Name:novelty:adoption:risk:investment[:horizon[:signal]]'.",
    ),
    profile_file: Optional[Path] = typer.Option(
        None,
        "--profile-file",
        exists=True,
        readable=True,
        resolve_path=True,
        help="JSON file describing innovation nodes.",
    ),
    limit: int = typer.Option(5, "--limit", "-l", min=1, max=12, help="Number of highlights to show."),
    json_mode: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Emit the raw JSON payload instead of a formatted summary.",
    ),
) -> None:
    """Highlight innovation hotspots and portfolio pressure points."""

    try:
        nodes = _load_nodes_file(profile_file) + _parse_node_specs(node)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if not nodes:
        raise typer.BadParameter("provide --node or --profile-file")

    payload = generate_innovation_hotspots(nodes, limit=limit)
    if json_mode:
        import json

        typer.echo(json.dumps(payload))
        return

    summary = [
        f"Nodes analyzed : {payload['node_count']}",
        f"Avg novelty    : {payload['portfolio']['avg_novelty']:.2f}",
        f"Avg adoption   : {payload['portfolio']['avg_adoption']:.2f}",
        f"Avg risk       : {payload['portfolio']['avg_risk']:.2f}",
        f"Novelty gap    : {payload['portfolio']['novelty_gap']:.3f}",
    ]
    typer.echo("\n".join(summary))

    focus_mix = payload["portfolio"].get("focus_mix", {})
    if focus_mix:
        mix_rows = [
            (focus.title(), f"{share:.1%}")
            for focus, share in sorted(focus_mix.items(), key=lambda item: item[1], reverse=True)
        ]
        _emit_table(["Focus", "Share"], mix_rows, "Focus mix")

    leader_rows = [
        (
            entry["name"],
            entry["horizon"],
            f"{entry['momentum']:.3f}",
            f"{entry['novelty_gap']:.3f}",
            entry["focus_area"].title(),
        )
        for entry in payload["momentum_leaders"]
    ]
    if leader_rows:
        _emit_table(
            ["Node", "Horizon", "Momentum", "Gap", "Focus"],
            leader_rows,
            "Momentum leaders",
        )

    pressure_rows = [
        (
            entry["name"],
            entry["horizon"],
            f"{entry['pressure']:.3f}",
            f"{entry['readiness']:.3f}",
            f"{entry['investment']:.2f}",
        )
        for entry in payload["pressure_points"]
    ]
    if pressure_rows:
        _emit_table(
            ["Node", "Horizon", "Pressure", "Readiness", "Investment"],
            pressure_rows,
            "Pressure watchlist",
        )

    activation_rows = [
        (
            entry["horizon"].title(),
            f"{entry['gap']:.3f}",
            f"T+{entry['activation_window_weeks']}w",
            entry["priority"].title(),
        )
        for entry in payload["activation_wave"]
    ]
    if activation_rows:
        _emit_table(
            ["Horizon", "Gap", "Activation", "Priority"],
            activation_rows,
            "Activation wave",
        )


def main() -> None:  # pragma: no cover - CLI helper
    """Entry point used by ``python -m echo_cli.innovation``."""

    app()


if __name__ == "__main__":  # pragma: no cover - script execution
    main()
