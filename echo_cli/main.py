"""Typer CLI providing access to the Puzzle Lab utilities."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import typer
from rich.console import Console
from rich.table import Table

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
from echo_puzzle_lab.charts import save_charts

app = typer.Typer(help="Puzzle Lab utilities", no_args_is_help=True)
console = Console()


def _ensure_ctx(ctx: typer.Context) -> None:
    if ctx.obj is None:
        ctx.obj = {"json": False}


def _set_json_mode(ctx: typer.Context, enabled: bool) -> None:
    _ensure_ctx(ctx)
    if enabled:
        ctx.obj["json"] = True


def _echo(ctx: typer.Context, payload: dict[str, object], *, message: str | None = None) -> None:
    _ensure_ctx(ctx)
    if ctx.obj.get("json", False):
        console.print(json.dumps(payload))
    elif message:
        console.print(message)


@app.callback()
def cli_root(ctx: typer.Context) -> None:
    _ensure_ctx(ctx)


@app.command()
def refresh(
    ctx: typer.Context,
    force: bool = typer.Option(
        False, "--force", "-f", help="Force regeneration even if the map exists"
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """(Re)build ``echo_map.json`` using the project orchestrator."""

    _set_json_mode(ctx, json_mode)
    target = ensure_map_exists(force=force)
    payload = {"map_path": str(target)}
    _echo(ctx, payload, message=f"Puzzle map available at {target}")


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
        raise typer.Exit(code=0)
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

    if build_charts_flag:
        frame = build_dataframe(records)
        outputs = save_charts(frame, Path("reports") / "figures")
        if not ctx.obj.get("json", False):
            for key, paths in outputs.items():
                console.print(f"[blue]{key}[/blue]: {', '.join(str(p) for p in paths)}")


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

    _set_json_mode(ctx, json_mode)
    if not has_ud_credentials():
        payload = {"updated": 0, "status": "missing_credentials"}
        _echo(ctx, payload, message="UD credentials not configured; skipping enrichment.")
        return

    records = load_records()
    frame = build_dataframe(records)
    pending = frame[~frame["UD_Bound"]]["Address"].tolist()
    if owners is not None:
        pending = pending[:owners]

    if not pending:
        payload = {"updated": 0, "status": "nothing_to_update"}
        _echo(ctx, payload, message="All visible puzzles already have UD metadata.")
        return

    metadata = fetch_ud_metadata(pending, refresh=refresh_cache)
    updated_records = update_ud_records(records, metadata)
    save_records(updated_records)

    payload = {"updated": len(metadata), "addresses": list(metadata.keys())}
    _echo(ctx, payload, message=f"Updated UD metadata for {len(metadata)} puzzles.")


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


def main() -> None:  # pragma: no cover - console entry point
    app()
