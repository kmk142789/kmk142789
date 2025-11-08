"""Typer CLI providing access to the Puzzle Lab utilities."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterable, List, Mapping, Optional

try:  # pragma: no cover - optional dependency
    import typer
except ModuleNotFoundError:  # pragma: no cover - fallback defined below
    typer = None  # type: ignore[assignment]

TYPER_AVAILABLE = typer is not None

try:  # pragma: no cover - optional dependency
    from rich.console import Console
    from rich.table import Table
except ModuleNotFoundError:  # pragma: no cover - provide minimal stand-ins
    Console = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]


if not TYPER_AVAILABLE:  # pragma: no cover - executed when typer is not installed
    class _FallbackExit(SystemExit):
        def __init__(self, code: int = 0):
            super().__init__(code)

    class _FallbackContext:
        def __init__(self) -> None:
            self.obj: dict[str, object] | None = None

    class _FallbackTyper:
        def __init__(self, *_, **__):
            self.commands: dict[str, Callable] = {}
            self.callback_fn: Callable | None = None

        def command(self, name: str | None = None):
            def decorator(func):
                command_name = name or func.__name__
                self.commands[command_name] = func
                return func

            return decorator

        def callback(self):
            def decorator(func):
                self.callback_fn = func
                return func

            return decorator

        def add_typer(self, sub_typer, name: str, **__):
            self.commands[name] = sub_typer
            return sub_typer

        def __call__(self) -> None:
            raise RuntimeError("Typer is unavailable in this environment")

    def _option(default=None, *_, **__):
        return default

    typer = SimpleNamespace(  # type: ignore[assignment]
        Typer=_FallbackTyper,
        Context=_FallbackContext,
        Option=_option,
        Argument=_option,
        Exit=_FallbackExit,
        BadParameter=ValueError,
    )

if Console is None:  # pragma: no cover - executed when rich is not installed
    class Console:  # type: ignore[override,assignment]
        def print(self, message: object) -> None:
            print(message)


if Table is None:  # pragma: no cover - executed when rich is not installed
    class Table:  # type: ignore[override,assignment]
        def __init__(self, *_, **__):
            self.rows: list[tuple] = []

        def add_column(self, *_: object, **__: object) -> None:
            return None

        def add_row(self, *values: object) -> None:
            self.rows.append(values)

FALLBACK_TABLE = Table.__module__ == __name__

from echo.deployment_meta_causal import (
    CONFIG_PATH as META_CAUSAL_CONFIG_PATH,
    MetaCausalRollout,
    load_meta_causal_config,
    plan_meta_causal_deployment,
    save_meta_causal_config,
)
from echo_puzzle_lab import (
    build_dataframe,
    ensure_map_exists,
    export_records,
    fetch_ud_metadata,
    has_ud_credentials,
    load_records,
    save_records,
    summarise,
    update_ud_records,
)
from echo.recursive_mythogenic_pulse import (
    PulseVoyageVisualizer,
    compose_voyage,
)
from echo.transcend import TranscendOrchestrator
from pulse_dashboard import WorkerHive

try:  # pragma: no cover - optional dependency
    from echo_puzzle_lab.charts import save_charts
except ModuleNotFoundError:  # pragma: no cover - charts require matplotlib
    save_charts = None  # type: ignore[assignment]

app = typer.Typer(help="Puzzle Lab utilities", no_args_is_help=True)
console = Console()
worker_hive = WorkerHive(project_root=Path(__file__).resolve().parent.parent)
deploy_app = typer.Typer(help="Deployment automation", no_args_is_help=True)
app.add_typer(deploy_app, name="deploy")


def _ensure_ctx(ctx: typer.Context) -> None:
    if ctx.obj is None:
        ctx.obj = {"json": False}


def _set_json_mode(ctx: typer.Context, enabled: bool) -> None:
    _ensure_ctx(ctx)
    if enabled:
        ctx.obj["json"] = True


def _normalise_iso_timestamp(value: str) -> str:
    """Normalise ISO 8601 timestamps to UTC ``YYYY-MM-DDTHH:MM:SSZ`` format."""

    text = value.strip()
    if not text:
        raise ValueError("timestamp cannot be empty")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(value) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_mapping_preview(mapping: Mapping[str, Any], *, limit: int = 3) -> str:
    """Render a concise preview of mapping contents for console output."""

    items: list[str] = []
    for index, (key, value) in enumerate(mapping.items()):
        if index >= limit:
            items.append("…")
            break
        if isinstance(value, (dict, list)):
            value_text = json.dumps(value, sort_keys=True)
        else:
            value_text = str(value)
        if len(value_text) > 40:
            value_text = f"{value_text[:37]}…"
        items.append(f"{key}={value_text}")
    return ", ".join(items)


def _summarise_event_details(
    event: Mapping[str, Any],
    *,
    include_metadata: bool,
    include_payload: bool,
) -> str:
    """Build a human readable summary for a worker hive event."""

    segments: list[str] = []
    metadata = event.get("metadata")
    payload = event.get("payload")

    if isinstance(payload, Mapping) and set(payload.keys()) == {"payload"}:
        inner = payload.get("payload")
        if isinstance(inner, Mapping):
            payload = inner

    if include_metadata and isinstance(metadata, Mapping) and metadata:
        segments.append(f"meta: {_format_mapping_preview(metadata)}")

    if include_payload and isinstance(payload, Mapping) and payload:
        segments.append(f"payload: {_format_mapping_preview(payload)}")

    if not segments:
        if isinstance(payload, Mapping) and payload:
            for key in (
                "summary",
                "status",
                "error",
                "path",
                "cycle",
                "updates",
                "count",
                "log_path",
            ):
                if key in payload:
                    segments.append(f"{key}={payload[key]}")
                    break
            else:
                segments.append(_format_mapping_preview(payload))
        elif isinstance(metadata, Mapping) and metadata:
            segments.append(_format_mapping_preview(metadata))

    return "; ".join(segments) if segments else "-"


def _echo(ctx: typer.Context, payload: dict[str, object], *, message: str | None = None) -> None:
    _ensure_ctx(ctx)
    if ctx.obj.get("json", False):
        console.print(json.dumps(payload))
    elif message:
        console.print(message)


def _format_meta_causal_summary(config: MetaCausalRollout, *, applied: bool) -> str:
    checks = ", ".join(config.preflight_checks) if config.preflight_checks else "none"
    status_text = "enabled" if config.enabled else "disabled"
    action = "configuration updated" if applied else "preview generated (use --apply to persist)"
    lines = [
        "Meta-causal engine deployment plan",
        f"  status        : {status_text}",
        f"  channel       : {config.rollout_channel}",
        f"  max_parallel  : {config.max_parallel_deployments}",
        f"  preflight     : {checks}",
        f"  artifact      : {config.artifact_path}",
        f"  manifest file : {META_CAUSAL_CONFIG_PATH}",
        f"  outcome       : {action}",
    ]
    return "\n".join(lines)


@deploy_app.command("meta-causal-engine")
def deploy_meta_causal_engine(
    ctx: typer.Context,
    status: Optional[str] = typer.Option(
        None,
        "--status",
        help="Set engine status to 'enabled' or 'disabled'.",
    ),
    channel: Optional[str] = typer.Option(
        None,
        "--channel",
        help="Override rollout channel (e.g. canary, production).",
    ),
    max_parallel: Optional[int] = typer.Option(
        None,
        "--max-parallel",
        help="Maximum concurrent deployment targets.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Persist configuration changes before returning the plan.",
    ),
) -> None:
    """Plan or apply a meta-causal engine deployment."""

    _ensure_ctx(ctx)
    metadata: dict[str, object] = {"apply": apply}
    if status is not None:
        metadata["status"] = status
    if channel is not None:
        metadata["channel"] = channel
    if max_parallel is not None:
        metadata["max_parallel"] = max_parallel

    with worker_hive.worker("deploy.meta_causal_engine", metadata=metadata) as task:
        config = load_meta_causal_config()
        updates: dict[str, object] = {}

        if status:
            normalised = status.strip().lower()
            if normalised not in {"enabled", "disabled"}:
                task.fail(error=f"invalid status {status!r}")
                raise typer.BadParameter("status must be 'enabled' or 'disabled'")
            config = config.with_overrides(enabled=normalised == "enabled")
            updates["status"] = normalised

        if channel:
            config = config.with_overrides(channel=channel)
            updates["channel"] = channel

        if max_parallel is not None:
            if max_parallel < 1:
                task.fail(error="max_parallel must be >= 1")
                raise typer.BadParameter("--max-parallel must be a positive integer")
            config = config.with_overrides(max_parallel=max_parallel)
            updates["max_parallel"] = max_parallel

        plan = plan_meta_causal_deployment(
            config,
            initiated_by="echo-cli",
            reason="manual deploy invocation",
        )
        plan["config_path"] = str(META_CAUSAL_CONFIG_PATH)
        if updates:
            plan["updates"] = updates

        payload = {"plan": plan, "applied": False}
        if apply:
            save_meta_causal_config(config)
            payload["applied"] = True

        summary = _format_meta_causal_summary(config, applied=payload["applied"])
        _echo(ctx, payload, message=summary)
        task.succeed(payload=payload)


@app.callback()
def cli_root(ctx: typer.Context) -> None:
    _ensure_ctx(ctx)


@app.command()
def history(
    ctx: typer.Context,
    limit: int = typer.Option(20, "--limit", "-n", help="Number of events to display"),
    since: Optional[str] = typer.Option(
        None,
        "--since",
        help="Only include events at or after the provided ISO timestamp",
    ),
    show_metadata: bool = typer.Option(
        False, "--show-metadata", help="Include metadata previews in the output"
    ),
    show_payload: bool = typer.Option(
        False, "--show-payload", help="Include payload previews in the output"
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Display recent worker hive telemetry for puzzle lab commands."""

    metadata = {
        "limit": limit,
        "since": since,
        "show_metadata": show_metadata,
        "show_payload": show_payload,
        "json": json_mode,
    }

    with worker_hive.worker("history", metadata=metadata) as task:
        if limit <= 0:
            task.fail(error="invalid_limit", limit=limit)
            raise typer.BadParameter("limit must be a positive integer")

        _set_json_mode(ctx, json_mode)
        since_marker: Optional[str] = None
        if since is not None:
            try:
                since_marker = _normalise_iso_timestamp(since)
            except ValueError as exc:
                task.fail(error="invalid_since", since=since)
                raise typer.BadParameter(f"Invalid ISO timestamp: {since}") from exc

        events = worker_hive.tail_events(limit=limit, since=since_marker)
        current_task_id = getattr(task, "task_id", None)
        ordered_events = [
            event for event in reversed(events) if event.get("task_id") != current_task_id
        ]

        payload: dict[str, object] = {
            "events": ordered_events,
            "log_path": str(worker_hive.log_path),
            "count": len(ordered_events),
        }

        if ctx.obj.get("json", False):
            _echo(ctx, payload)
        else:
            if not ordered_events:
                console.print(
                    "No worker activity recorded yet. Instrumented commands will appear here once executed."
                )
            else:
                if FALLBACK_TABLE:
                    console.print(
                        f"Recent worker events ({len(ordered_events)}) from {worker_hive.log_path}:"
                    )
                    for event in ordered_events:
                        timestamp = event.get("timestamp", "-")
                        name = event.get("name", "-")
                        status = event.get("status", "-")
                        details = _summarise_event_details(
                            event,
                            include_metadata=show_metadata,
                            include_payload=show_payload,
                        )
                        console.print(f"{timestamp} | {name} | {status} | {details}")
                else:
                    table = Table(title="Recent worker activity")
                    table.add_column("Timestamp", style="cyan")
                    table.add_column("Command", style="magenta")
                    table.add_column("Status", style="green")
                    table.add_column("Details")
                    for event in ordered_events:
                        timestamp = event.get("timestamp", "-")
                        name = event.get("name", "-")
                        status = event.get("status", "-")
                        details = _summarise_event_details(
                            event,
                            include_metadata=show_metadata,
                            include_payload=show_payload,
                        )
                        table.add_row(str(timestamp), str(name), str(status), details)
                    console.print(table)

        task.succeed(payload=payload)


@app.command()
def refresh(
    ctx: typer.Context,
    force: bool = typer.Option(
        False, "--force", "-f", help="Force regeneration even if the map exists"
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
    voyage_map: bool = typer.Option(
        False,
        "--voyage-map",
        help="Generate and display the converged pulse voyage atlas",
    ),
) -> None:
    """(Re)build ``echo_map.json`` using the project orchestrator."""
    with worker_hive.worker(
        "refresh",
        metadata={"force": force, "voyage_map": voyage_map, "json": json_mode},
    ) as task:
        _set_json_mode(ctx, json_mode)
        target = ensure_map_exists(force=force)
        payload = {"map_path": str(target)}

        if voyage_map:
            voyages = [
                compose_voyage(seed=seed, recursion_level=2 + (seed % 2))
                for seed in range(1, 4)
            ]
            visualizer = PulseVoyageVisualizer.from_voyages(voyages)
            atlas = visualizer.to_json()
            report_path = visualizer.write_markdown_report()
            atlas["markdown_report"] = str(report_path)
            payload["voyage_map"] = atlas

            if not ctx.obj.get("json", False):
                console.print("")
                console.print(visualizer.ascii_map())
                console.print(
                    f"[blue]Converged pulse voyage atlas saved to {report_path}[/blue]"
                )

        _echo(ctx, payload, message=f"Puzzle map available at {target}")
        task.succeed(payload=payload)


def _parse_puzzle_ids(puzzles: Optional[str]) -> set[int] | None:
    if not puzzles:
        return None
    parsed: set[int] = set()
    for item in puzzles.split(","):
        item = item.strip()
        if not item:
            continue
        parsed.add(int(item))
    return parsed


def _filter_records(records: Iterable, puzzles: set[int] | None) -> list:
    if puzzles is None:
        return list(records)
    return [record for record in records if record.puzzle in puzzles]


@app.command()
def verify(
    ctx: typer.Context,
    puzzles: Optional[str] = typer.Option(
        None,
        "--puzzles",
        help="Comma-separated puzzle numbers to verify",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Re-derive addresses locally and exit non-zero on mismatch."""
    with worker_hive.worker(
        "verify",
        metadata={"puzzles": puzzles, "json": json_mode},
    ) as task:
        _set_json_mode(ctx, json_mode)
        records = load_records()
        selected = _filter_records(records, _parse_puzzle_ids(puzzles))
        frame = build_dataframe(selected)
        mismatches = frame[frame["Mismatch"]]

        payload = {
            "checked": len(frame),
            "mismatches": len(mismatches),
            "puzzles": mismatches["Puzzle"].tolist(),
        }

        if ctx.obj.get("json", False):
            _echo(ctx, payload)
        else:
            table = Table(title="Puzzle verification")
            table.add_column("Puzzle", justify="right")
            table.add_column("Address")
            table.add_column("Derived")
            for _, row in mismatches.iterrows():
                table.add_row(str(row["Puzzle"]), row["Address"], row["Derived"] or "-")
            if mismatches.empty:
                console.print("[green]All puzzles verified successfully.[/green]")
            else:
                console.print(table)
        if mismatches.empty:
            task.succeed(payload=payload)
            raise typer.Exit(code=0)
        task.fail(payload=payload)
        raise typer.Exit(code=1)


@app.command()
def stats(
    ctx: typer.Context,
    build_charts_flag: bool = typer.Option(
        False,
        "--build-charts",
        help="Save chart artefacts to reports/figures/",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Print summary statistics for the current puzzle map."""
    with worker_hive.worker(
        "stats",
        metadata={"build_charts": build_charts_flag, "json": json_mode},
    ) as task:
        _set_json_mode(ctx, json_mode)
        records = load_records()
        summary = summarise(records)

        if ctx.obj.get("json", False):
            _echo(ctx, summary)
        else:
            table = Table(title="Puzzle Lab overview")
            table.add_column("Metric")
            table.add_column("Value")
            table.add_row("Total puzzles", str(summary["total_puzzles"]))
            families = ", ".join(
                f"{family}: {count}" for family, count in summary["families"].items()
            )
            table.add_row("Families", families or "(none)")
            bound = summary["ud_bound"]
            table.add_row(
                "UD coverage",
                f"bound={bound['bound']} unbound={bound['unbound']}",
            )
            table.add_row("Mismatches", str(summary["mismatches"]))
            console.print(table)

        charts_payload: dict[str, object] | None = None
        if build_charts_flag:
            if save_charts is None:
                task.fail(error="charts_unavailable", summary=summary)
                raise typer.Exit(code=1)
            frame = build_dataframe(records)
            outputs = save_charts(frame, Path("reports") / "figures")
            charts_payload = {
                key: [str(p) for p in paths]
                for key, paths in outputs.items()
            }
            task.progress(stage="charts", generated=sum(len(v) for v in charts_payload.values()))
            if not ctx.obj.get("json", False):
                for key, paths in outputs.items():
                    console.print(f"[blue]{key}[/blue]: {', '.join(str(p) for p in paths)}")

        payload = {"summary": summary}
        if charts_payload:
            payload["charts"] = charts_payload
        task.succeed(payload=payload)


@app.command("enrich-ud")
def enrich_ud(
    ctx: typer.Context,
    owners: Optional[int] = typer.Option(
        None,
        "--owners",
        help="Only enrich the first N owner records (defaults to all)",
    ),
    refresh_cache: bool = typer.Option(
        False, "--refresh-cache", help="Ignore cached UD lookups"
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Populate UD metadata for existing map entries (skips when no creds)."""
    with worker_hive.worker(
        "enrich-ud",
        metadata={
            "owners": owners,
            "refresh_cache": refresh_cache,
            "json": json_mode,
        },
    ) as task:
        _set_json_mode(ctx, json_mode)
        if not has_ud_credentials():
            payload = {"updated": 0, "status": "missing_credentials"}
            _echo(
                ctx,
                payload,
                message="UD credentials not configured; skipping enrichment.",
            )
            task.skip(**payload)
            return

        records = load_records()
        frame = build_dataframe(records)
        pending = frame[~frame["UD_Bound"]]["Address"].tolist()
        if owners is not None:
            pending = pending[:owners]

        if not pending:
            payload = {"updated": 0, "status": "nothing_to_update"}
            _echo(
                ctx,
                payload,
                message="All visible puzzles already have UD metadata.",
            )
            task.skip(**payload)
            return

        metadata = fetch_ud_metadata(pending, refresh=refresh_cache)
        updated_records = update_ud_records(records, metadata)
        save_records(updated_records)

        payload = {"updated": len(metadata), "addresses": list(metadata.keys())}
        _echo(ctx, payload, message=f"Updated UD metadata for {len(metadata)} puzzles.")
        task.succeed(payload=payload)


@app.command()
def transcend(
    ctx: typer.Context,
    infinite: bool = typer.Option(
        False,
        "--infinite",
        help="Run continuously until interrupted",
    ),
    cycles: int = typer.Option(
        1,
        "--cycles",
        "-c",
        help="Number of cycles to execute (ignored with --infinite)",
    ),
    interval_minutes: float = typer.Option(
        0.0,
        "--interval-minutes",
        "-i",
        help="Minutes to wait between cycles",
    ),
    at_midnight: bool = typer.Option(
        False,
        "--at-midnight",
        help="Align cycles to the next UTC midnight",
    ),
    target: Optional[List[str]] = typer.Option(
        None,
        "--target",
        help="Record sync receipts for the given target (repeat for multiple)",
    ),
    ledger_path: Path = typer.Option(
        Path("ledger/transcend_log.jsonl"),
        "--ledger-path",
        help="Path to the permanent transcend ledger",
    ),
    ritual_dir: Path = typer.Option(
        Path("ledger/rituals"),
        "--ritual-dir",
        help="Directory where ritual entries are written",
    ),
    stream_dir: Path = typer.Option(
        Path("ledger/transcend_streams"),
        "--stream-dir",
        help="Directory for per-target sync receipts",
    ),
    base_dir: Path = typer.Option(
        Path("."),
        "--base-dir",
        help="Project root containing COLOSSUS artifacts",
    ),
    json_mode: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Emit JSON payloads instead of rich text",
    ),
) -> None:
    """Automate recurring EchoInfinite rituals."""
    metadata = {
        "infinite": infinite,
        "cycles": cycles,
        "interval_minutes": interval_minutes,
        "at_midnight": at_midnight,
        "targets": target,
        "json": json_mode,
    }
    with worker_hive.worker("transcend", metadata=metadata) as task:
        if not infinite and cycles <= 0:
            task.fail(error="invalid_cycles", cycles=cycles)
            raise typer.BadParameter("cycles must be a positive integer")

        _set_json_mode(ctx, json_mode)
        targets = target or ["github", "firebase", "codex"]

        try:
            orchestrator = TranscendOrchestrator(
                base_dir=base_dir,
                interval_minutes=interval_minutes,
                at_midnight=at_midnight,
                max_cycles=None if infinite else cycles,
                targets=targets,
                ledger_path=ledger_path,
                ritual_dir=ritual_dir,
                stream_dir=stream_dir,
            )
        except ValueError as exc:
            task.fail(error=str(exc))
            raise typer.BadParameter(str(exc)) from exc

        executed = 0
        try:
            for record in orchestrator.run():
                executed += 1
                payload = {
                    "cycle": record.cycle,
                    "timestamp": record.timestamp,
                    "glyph": record.glyph_signature,
                    "artifacts": list(record.artifacts),
                    "ledger": str(record.ledger_entry),
                    "ritual": str(record.ritual_path),
                    "targets": list(record.targets),
                }
                if record.progress is not None and hasattr(record.progress, "proposal_id"):
                    payload["proposal_id"] = getattr(record.progress, "proposal_id")

                message = (
                    f"Cycle {record.cycle:05d} logged to {record.ledger_entry}. "
                    f"Ritual entry: {record.ritual_path}"
                )
                _echo(ctx, payload, message=message)
                task.progress(stage="cycle", cycle=record.cycle, glyph=record.glyph_signature)
        except KeyboardInterrupt:  # pragma: no cover - interactive usage
            console.print(f"Interrupted after {executed} cycle(s)")
            task.skip(interrupted=True, completed=executed)
            return

        task.succeed(payload={"executed": executed, "targets": targets})


@app.command()
def export(
    ctx: typer.Context,
    query: Optional[str] = typer.Option(
        None,
        "--query",
        help="pandas-compatible expression, e.g. family=='P2PKH' and ud_bound==True",
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        help="Destination path for the JSONL export (defaults to exports/puzzle_lab_<timestamp>.jsonl)",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Export filtered puzzle rows to a JSON Lines file."""
    with worker_hive.worker(
        "export",
        metadata={"query": query, "out": str(out) if out else None, "json": json_mode},
    ) as task:
        _set_json_mode(ctx, json_mode)
        records = load_records()
        frame = build_dataframe(records)

        query_frame = frame.copy()
        query_frame["puzzle"] = query_frame["Puzzle"]
        query_frame["family"] = query_frame["Family"]
        query_frame["ud_bound"] = query_frame["UD_Bound"]
        query_frame["ud_count"] = query_frame["UD_Count"]
        query_frame["address"] = query_frame["Address"]

        if query:
            try:
                filtered_frame = query_frame.query(query, engine="python")
            except Exception as exc:  # pragma: no cover - defensive
                task.fail(error=str(exc), query=query)
                raise typer.BadParameter(f"Invalid query: {exc}") from exc
        else:
            filtered_frame = query_frame

        puzzles = set(filtered_frame["puzzle"].tolist())
        selected = _filter_records(records, puzzles)

        if out is None:
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
            out = Path("exports") / f"puzzle_lab_{timestamp}.jsonl"

        destination = export_records(selected, out)
        payload = {"exported": len(selected), "path": str(destination)}
        _echo(ctx, payload, message=f"Exported {len(selected)} puzzles to {destination}")
        task.succeed(payload=payload)


def main() -> None:  # pragma: no cover - console entry point
    if TYPER_AVAILABLE:
        app()
        return

    parser = argparse.ArgumentParser(prog="echo_cli", description="Puzzle Lab utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    stats_parser = subparsers.add_parser("stats", help="Print summary statistics")
    stats_parser.add_argument("--build-charts", action="store_true", dest="build_charts")
    stats_parser.add_argument("--json", "-j", action="store_true", dest="json_mode")

    history_parser = subparsers.add_parser(
        "history", help="Display recent worker hive telemetry"
    )
    history_parser.add_argument("--limit", "-n", type=int, default=20, dest="limit")
    history_parser.add_argument("--since", dest="since")
    history_parser.add_argument(
        "--show-metadata", action="store_true", dest="show_metadata"
    )
    history_parser.add_argument(
        "--show-payload", action="store_true", dest="show_payload"
    )
    history_parser.add_argument("--json", "-j", action="store_true", dest="json_mode")

    verify_parser = subparsers.add_parser("verify", help="Verify puzzle addresses")
    verify_parser.add_argument("--puzzles", dest="puzzles")
    verify_parser.add_argument("--json", "-j", action="store_true", dest="json_mode")

    transcend_parser = subparsers.add_parser(
        "transcend", help="Automate recurring EchoInfinite rituals"
    )
    transcend_parser.add_argument("--infinite", action="store_true", dest="infinite")
    transcend_parser.add_argument("--cycles", "-c", type=int, default=1, dest="cycles")
    transcend_parser.add_argument(
        "--interval-minutes", "-i", type=float, default=0.0, dest="interval_minutes"
    )
    transcend_parser.add_argument("--at-midnight", action="store_true", dest="at_midnight")
    transcend_parser.add_argument("--target", action="append", dest="targets")
    transcend_parser.add_argument(
        "--ledger-path", default="ledger/transcend_log.jsonl", dest="ledger_path"
    )
    transcend_parser.add_argument(
        "--ritual-dir", default="ledger/rituals", dest="ritual_dir"
    )
    transcend_parser.add_argument(
        "--stream-dir", default="ledger/transcend_streams", dest="stream_dir"
    )
    transcend_parser.add_argument("--base-dir", default=".", dest="base_dir")
    transcend_parser.add_argument("--json", "-j", action="store_true", dest="json_mode")

    deploy_parser = subparsers.add_parser("deploy", help="Deployment automation")
    deploy_subparsers = deploy_parser.add_subparsers(dest="deploy_command", required=True)
    meta_parser = deploy_subparsers.add_parser(
        "meta-causal-engine", help="Plan or apply a meta-causal engine rollout"
    )
    meta_parser.add_argument("--status", choices=("enabled", "disabled"))
    meta_parser.add_argument("--channel")
    meta_parser.add_argument("--max-parallel", type=int, dest="max_parallel")
    meta_parser.add_argument("--apply", action="store_true")

    args = parser.parse_args()

    ctx = typer.Context()  # type: ignore[call-arg]

    if args.command == "stats":
        stats(ctx, build_charts_flag=args.build_charts, json_mode=args.json_mode)
    elif args.command == "history":
        history(
            ctx,
            limit=args.limit,
            since=args.since,
            show_metadata=args.show_metadata,
            show_payload=args.show_payload,
            json_mode=args.json_mode,
        )
    elif args.command == "verify":
        verify(ctx, puzzles=args.puzzles, json_mode=args.json_mode)
    elif args.command == "transcend":
        targets = args.targets if args.targets else None
        transcend(
            ctx,
            infinite=args.infinite,
            cycles=args.cycles,
            interval_minutes=args.interval_minutes,
            at_midnight=args.at_midnight,
            target=targets,
            ledger_path=Path(args.ledger_path),
            ritual_dir=Path(args.ritual_dir),
            stream_dir=Path(args.stream_dir),
            base_dir=Path(args.base_dir),
            json_mode=args.json_mode,
        )
    elif args.command == "deploy":
        if args.deploy_command == "meta-causal-engine":
            deploy_meta_causal_engine(
                ctx,
                status=args.status,
                channel=args.channel,
                max_parallel=args.max_parallel,
                apply=args.apply,
            )
        else:  # pragma: no cover - defensive
            parser.error(f"Unsupported deploy command: {args.deploy_command}")
    else:  # pragma: no cover - defensive
        parser.error(f"Unsupported command in fallback mode: {args.command}")
