"""Typer CLI providing access to the Puzzle Lab utilities."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterable, List, Mapping, Optional
from statistics import mean, median

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
from echo.resonance_complex import (
    load_resonance_blueprint,
    save_resonance_report,
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


def _parse_iso_timestamp(value: str | None) -> datetime | None:
    """Parse ISO 8601 timestamps returning timezone-aware datetimes when possible."""

    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_iso(timestamp: datetime | None) -> str | None:
    """Render timezone-aware datetimes as canonical ``YYYY-MM-DDTHH:MM:SSZ`` strings."""

    if timestamp is None:
        return None
    return timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_duration(seconds: float | None) -> str:
    """Render durations as ``H:MM:SS`` strings for console output."""

    if seconds is None:
        return "-"
    seconds = max(seconds, 0.0)
    whole_seconds = int(seconds)
    minutes, secs = divmod(whole_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _format_hours(hours: float | None) -> str:
    """Render fractional hours as a concise human readable string."""

    if hours is None:
        return "-"
    hours = max(hours, 0.0)
    total_minutes = int(round(hours * 60))
    if total_minutes == 0 and hours > 0:
        return "<1m"
    hours_part, minutes = divmod(total_minutes, 60)
    if hours_part and minutes:
        return f"{hours_part}h {minutes}m"
    if hours_part:
        return f"{hours_part}h"
    return f"{minutes}m"


def _percentile(values: List[float], fraction: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    fraction = min(max(fraction, 0.0), 1.0)
    index = int(math.ceil(fraction * (len(values) - 1)))
    return values[index]


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


def _aggregate_worker_events(
    events: Iterable[Mapping[str, Any]],
    *,
    command_filter: set[str] | None = None,
) -> dict[str, Any]:
    """Derive aggregate statistics from worker hive telemetry.

    Parameters
    ----------
    events:
        Worker hive telemetry records.
    command_filter:
        Optional whitelist limiting aggregation to the provided command names.
    """

    status_counts: Counter[str] = Counter()
    command_counts: Counter[str] = Counter()
    task_states: dict[str, str] = {}
    last_event_timestamp: str | None = None

    for event in events:
        status = str(event.get("status", "unknown"))
        name = str(event.get("name", "-"))
        if command_filter and name not in command_filter:
            continue
        status_counts[status] += 1
        command_counts[name] += 1

        task_id = event.get("task_id")
        if isinstance(task_id, str):
            if status in {"success", "failure", "skipped"}:
                task_states[task_id] = status
            elif status == "start":
                task_states.setdefault(task_id, "active")
            else:
                task_states.setdefault(task_id, "active")

        timestamp = event.get("timestamp")
        if isinstance(timestamp, str):
            if last_event_timestamp is None or timestamp > last_event_timestamp:
                last_event_timestamp = timestamp

    active_tasks = sum(1 for state in task_states.values() if state == "active")

    return {
        "total_events": sum(status_counts.values()),
        "status_counts": dict(status_counts),
        "command_activity": dict(command_counts),
        "unique_commands": len(command_counts),
        "active_tasks": active_tasks,
        "last_event": last_event_timestamp,
    }


def _derive_task_metrics(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Compute lifecycle analytics from worker hive telemetry."""

    tasks: dict[str, dict[str, Any]] = {}
    for event in events:
        task_id = event.get("task_id")
        if not isinstance(task_id, str):
            continue
        status = str(event.get("status", "")).lower()
        name = str(event.get("name", "-"))
        timestamp = _parse_iso_timestamp(event.get("timestamp"))
        task_state = tasks.setdefault(
            task_id,
            {
                "name": name,
                "start": None,
                "end": None,
                "status": None,
                "progress_updates": 0,
                "last_progress": None,
            },
        )
        task_state["name"] = name
        if status == "start" and timestamp:
            task_state["start"] = timestamp
        elif status in {"success", "failure", "skipped"}:
            if timestamp:
                task_state["end"] = timestamp
            task_state["status"] = status
        elif status == "progress":
            task_state["progress_updates"] += 1
            if timestamp:
                task_state["last_progress"] = timestamp

    completed: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    duration_values: list[float] = []
    now = datetime.now(timezone.utc)

    for task_id, state in tasks.items():
        start = state.get("start")
        if start is None:
            continue
        end = state.get("end")
        status = state.get("status") or "active"
        if end is not None:
            duration = max((end - start).total_seconds(), 0.0)
            duration_values.append(duration)
            completed.append(
                {
                    "task_id": task_id,
                    "name": state["name"],
                    "status": status,
                    "duration_seconds": duration,
                    "finished_at": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            )
        else:
            last_progress = state.get("last_progress") or start
            age = max((now - start).total_seconds(), 0.0)
            since_heartbeat = max((now - last_progress).total_seconds(), 0.0)
            active.append(
                {
                    "task_id": task_id,
                    "name": state["name"],
                    "age_seconds": age,
                    "last_heartbeat_seconds": since_heartbeat,
                    "progress_updates": state["progress_updates"],
                }
            )

    completed.sort(key=lambda item: item["duration_seconds"], reverse=True)
    active.sort(key=lambda item: item["age_seconds"], reverse=True)

    duration_values.sort()
    avg_duration = mean(duration_values) if duration_values else None
    p90_duration = _percentile(duration_values, 0.9)

    stats = {
        "completed_total": len(completed),
        "success_total": sum(1 for task in completed if task["status"] == "success"),
        "failure_total": sum(1 for task in completed if task["status"] == "failure"),
        "skipped_total": sum(1 for task in completed if task["status"] == "skipped"),
        "active_total": len(active),
        "average_duration_seconds": avg_duration,
        "p90_duration_seconds": p90_duration,
    }
    if stats["completed_total"]:
        stats["failure_rate"] = stats["failure_total"] / stats["completed_total"]
    else:
        stats["failure_rate"] = 0.0

    recent_failures = [task for task in completed if task["status"] == "failure"]
    recent_failures.sort(key=lambda item: item.get("finished_at", ""), reverse=True)

    return {
        "stats": stats,
        "slowest_tasks": completed[:5],
        "active_tasks": active[:5],
        "recent_failures": recent_failures[:5],
    }


def _compute_command_performance(
    events: Iterable[Mapping[str, Any]],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Summarise health signals per command from worker hive telemetry."""

    tasks: dict[str, dict[str, Any]] = {}
    for event in events:
        task_id = event.get("task_id")
        if not isinstance(task_id, str):
            continue
        status = str(event.get("status", "")).lower()
        name = str(event.get("name", "-"))
        timestamp = _parse_iso_timestamp(event.get("timestamp"))
        task_state = tasks.setdefault(
            task_id,
            {
                "name": name,
                "start": None,
                "end": None,
                "status": None,
                "last_progress": None,
            },
        )
        task_state["name"] = name
        if status == "start" and timestamp:
            task_state["start"] = timestamp
        elif status in {"success", "failure", "skipped"}:
            if timestamp:
                task_state["end"] = timestamp
            task_state["status"] = status
        elif status == "progress" and timestamp:
            task_state["last_progress"] = timestamp

    now = now or datetime.now(timezone.utc)
    command_buckets: dict[str, dict[str, Any]] = {}
    for state in tasks.values():
        name = state["name"]
        start = state.get("start")
        if start is None:
            continue
        bucket = command_buckets.setdefault(
            name,
            {
                "completed": 0,
                "success": 0,
                "failure": 0,
                "skipped": 0,
                "active": 0,
                "durations": [],
                "last_finished": None,
                "stale_heartbeats": [],
            },
        )
        end = state.get("end")
        status = state.get("status") or "active"
        if end is not None:
            duration = max((end - start).total_seconds(), 0.0)
            bucket["completed"] += 1
            bucket["durations"].append(duration)
            bucket[status] = bucket.get(status, 0) + 1
            last_finished = bucket["last_finished"]
            if last_finished is None or end > last_finished:
                bucket["last_finished"] = end
        else:
            bucket["active"] += 1
            last_progress = state.get("last_progress") or start
            stale = max((now - last_progress).total_seconds(), 0.0)
            bucket["stale_heartbeats"].append(stale)

    command_rows: list[dict[str, Any]] = []
    for name in sorted(command_buckets.keys()):
        bucket = command_buckets[name]
        durations = sorted(bucket["durations"])
        avg_duration = mean(durations) if durations else None
        p95_duration = _percentile(durations, 0.95)
        stale_max = max(bucket["stale_heartbeats"]) if bucket["stale_heartbeats"] else None
        last_finished = bucket["last_finished"]
        command_rows.append(
            {
                "command": name,
                "completed": bucket["completed"],
                "success": bucket.get("success", 0),
                "failure": bucket.get("failure", 0),
                "skipped": bucket.get("skipped", 0),
                "active": bucket["active"],
                "average_duration_seconds": avg_duration,
                "p95_duration_seconds": p95_duration,
                "slowest_duration_seconds": max(durations) if durations else None,
                "last_finished_at": last_finished.strftime("%Y-%m-%dT%H:%M:%SZ")
                if last_finished
                else None,
                "success_rate": (
                    bucket["success"] / bucket["completed"]
                    if bucket["completed"]
                    else 0.0
                ),
                "stale_heartbeats_seconds": stale_max,
            }
        )

    totals = {
        "commands_tracked": len(command_rows),
        "completed_tasks": sum(row["completed"] for row in command_rows),
        "active_tasks": sum(row["active"] for row in command_rows),
        "failures": sum(row["failure"] for row in command_rows),
    }
    if totals["completed_tasks"]:
        totals["overall_failure_rate"] = (
            totals["failures"] / totals["completed_tasks"]
        )
    else:
        totals["overall_failure_rate"] = 0.0

    return {"commands": command_rows, "totals": totals}


def _collect_task_states(
    events: Iterable[Mapping[str, Any]], *, command_filter: str | None = None
) -> dict[str, dict[str, Any]]:
    """Normalise worker telemetry into a task-centric timeline."""

    states: dict[str, dict[str, Any]] = {}
    for event in events:
        task_id = event.get("task_id")
        if not isinstance(task_id, str):
            continue
        name = str(event.get("name", "-"))
        if command_filter and name != command_filter:
            continue
        status = str(event.get("status", "")).lower()
        timestamp = _parse_iso_timestamp(event.get("timestamp"))
        state = states.setdefault(
            task_id,
            {
                "task_id": task_id,
                "name": name,
                "start": None,
                "end": None,
                "status": None,
                "last_progress": None,
                "first_seen": None,
                "last_seen": None,
            },
        )
        state["name"] = name
        if timestamp:
            state["last_seen"] = timestamp
            if state["first_seen"] is None:
                state["first_seen"] = timestamp
        if status == "start" and timestamp:
            state["start"] = timestamp
        elif status in {"success", "failure", "skipped"}:
            if timestamp:
                state["end"] = timestamp
            state["status"] = status
        elif status == "progress" and timestamp:
            state["last_progress"] = timestamp

    return states


def _compute_peak_concurrency(
    task_states: Mapping[str, Mapping[str, Any]], *, now: datetime
) -> dict[str, Any]:
    """Calculate the moment when the most worker tasks overlapped."""

    timeline: list[tuple[datetime, int]] = []
    for state in task_states.values():
        start = state.get("start")
        if not isinstance(start, datetime):
            continue
        timeline.append((start, 1))
        end = state.get("end")
        if not isinstance(end, datetime):
            end = state.get("last_progress") or now
        timeline.append((end, -1))

    if not timeline:
        return {"peak": 0, "timestamp": None}

    timeline.sort(key=lambda item: item[0])
    active = 0
    peak = 0
    peak_at: datetime | None = None
    for timestamp, delta in timeline:
        active += delta
        if active > peak:
            peak = active
            peak_at = timestamp

    return {"peak": peak, "timestamp": _format_iso(peak_at)}


def _compute_timeline_insights(
    events: Iterable[Mapping[str, Any]],
    *,
    command_filter: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Derive tempo, throughput, and concurrency analytics from telemetry."""

    now = now or datetime.now(timezone.utc)
    event_list = list(events)
    states = _collect_task_states(event_list, command_filter=command_filter)
    completed: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    durations: list[float] = []
    hourly_buckets: dict[datetime, Counter[str]] = {}
    completions: list[datetime] = []
    success_total = failure_total = skipped_total = 0

    for state in states.values():
        start = state.get("start")
        if not isinstance(start, datetime):
            continue
        entry = {
            "task_id": state["task_id"],
            "name": state["name"],
            "start": start,
            "last_progress": state.get("last_progress"),
        }
        end = state.get("end")
        status = state.get("status")
        if isinstance(end, datetime):
            duration = max((end - start).total_seconds(), 0.0)
            durations.append(duration)
            completions.append(end)
            resolved_status = status or "success"
            if resolved_status == "success":
                success_total += 1
            elif resolved_status == "failure":
                failure_total += 1
            elif resolved_status == "skipped":
                skipped_total += 1
            entry.update({
                "end": end,
                "status": resolved_status,
                "duration_seconds": duration,
            })
            completed.append(entry)
            bucket = end.replace(minute=0, second=0, microsecond=0)
            bucket_counts = hourly_buckets.setdefault(bucket, Counter())
            bucket_counts["total"] += 1
            bucket_counts[resolved_status] += 1
        else:
            heartbeat = state.get("last_progress") or start
            entry.update({
                "status": status or "active",
                "last_progress": heartbeat,
            })
            active.append(entry)

    durations.sort()
    avg_duration = mean(durations) if durations else None
    median_duration = median(durations) if durations else None
    p95_duration = _percentile(durations, 0.95)

    raw_window_start = (
        _parse_iso_timestamp(event_list[0].get("timestamp")) if event_list else None
    )
    raw_window_end = (
        _parse_iso_timestamp(event_list[-1].get("timestamp")) if event_list else None
    )
    window_start = _format_iso(raw_window_start)
    window_end = _format_iso(raw_window_end)
    span_seconds = None
    if raw_window_start and raw_window_end:
        span_seconds = max((raw_window_end - raw_window_start).total_seconds(), 0.0)

    summary = {
        "tasks_tracked": len(states),
        "completed_tasks": len(completed),
        "active_tasks": len(active),
        "success": success_total,
        "failure": failure_total,
        "skipped": skipped_total,
        "success_rate": success_total / len(completed) if completed else 0.0,
        "average_duration_seconds": avg_duration,
        "median_duration_seconds": median_duration,
        "p95_duration_seconds": p95_duration,
        "window_start": window_start,
        "window_end": window_end,
        "window_span_seconds": span_seconds,
        "command_filter": command_filter,
    }

    hourly = [
        {
            "hour": _format_iso(bucket),
            "completed": counts.get("total", 0),
            "success": counts.get("success", 0),
            "failure": counts.get("failure", 0),
            "skipped": counts.get("skipped", 0),
        }
        for bucket, counts in sorted(hourly_buckets.items())
    ]

    idle_windows: list[dict[str, Any]] = []
    completions.sort()
    for prev, curr in zip(completions, completions[1:]):
        gap = max((curr - prev).total_seconds(), 0.0)
        if gap <= 0:
            continue
        idle_windows.append(
            {
                "start": _format_iso(prev),
                "end": _format_iso(curr),
                "duration_seconds": gap,
            }
        )
    idle_windows.sort(key=lambda item: item["duration_seconds"], reverse=True)
    idle_windows = idle_windows[:5]

    def _summarise_streak(target: str) -> dict[str, Any]:
        best = {"length": 0, "ended_at": None}
        current = 0
        for entry in sorted(completed, key=lambda item: item.get("end")):
            if entry.get("status") == target:
                current += 1
                if current > best["length"]:
                    best = {"length": current, "ended_at": _format_iso(entry.get("end"))}
            else:
                current = 0
        return best

    streaks = {
        "success": _summarise_streak("success"),
        "failure": _summarise_streak("failure"),
    }

    active_focus = []
    for entry in active:
        start = entry["start"]
        last_progress = entry.get("last_progress") or start
        active_focus.append(
            {
                "task_id": entry["task_id"],
                "name": entry["name"],
                "age_seconds": max((now - start).total_seconds(), 0.0),
                "last_heartbeat_seconds": max((now - last_progress).total_seconds(), 0.0),
            }
        )
    active_focus.sort(key=lambda item: item["age_seconds"], reverse=True)
    active_focus = active_focus[:5]

    recent = []
    for entry in sorted(completed, key=lambda item: item.get("end"), reverse=True)[:5]:
        recent.append(
            {
                "task_id": entry["task_id"],
                "name": entry["name"],
                "status": entry["status"],
                "duration_seconds": entry["duration_seconds"],
                "finished_at": _format_iso(entry.get("end")),
            }
        )

    concurrency = _compute_peak_concurrency(states, now=now)

    return {
        "summary": summary,
        "hourly_throughput": hourly,
        "idle_windows": idle_windows,
        "streaks": streaks,
        "active_focus": active_focus,
        "recent_completions": recent,
        "concurrency": concurrency,
        "tasks_tracked": len(states),
    }


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
def resonance(
    ctx: typer.Context,
    blueprint: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to a resonance complex blueprint JSON file.",
    ),
    cycles: int = typer.Option(8, "--cycles", "-c", help="Number of simulation cycles to execute."),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        help="Seed for the pseudo-random components (defaults to system entropy).",
    ),
    save_report: Optional[Path] = typer.Option(
        None,
        "--save-report",
        help="Persist the full resonance report as JSON.",
    ),
    json_mode: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Emit JSON instead of a formatted text summary.",
    ),
) -> None:
    """Run a high-order resonance complex simulation."""

    _ensure_ctx(ctx)
    metadata = {
        "blueprint": str(blueprint),
        "cycles": cycles,
        "seed": seed,
        "json": json_mode,
    }

    with worker_hive.worker("resonance.simulation", metadata=metadata) as task:
        if cycles <= 0:
            task.fail(error="invalid_cycles", cycles=cycles)
            raise typer.BadParameter("--cycles must be a positive integer")

        try:
            complex_model = load_resonance_blueprint(blueprint)
        except FileNotFoundError:
            task.fail(error="missing_blueprint", path=str(blueprint))
            raise typer.BadParameter(f"blueprint not found: {blueprint}") from None
        except ValueError as exc:
            task.fail(error="invalid_blueprint", path=str(blueprint), message=str(exc))
            raise typer.BadParameter(str(exc)) from exc

        report = complex_model.simulate(cycles=cycles, seed=seed)
        if save_report is not None:
            save_resonance_report(report, save_report)

        payload = report.to_dict()
        payload["blueprint"] = str(blueprint)
        if save_report is not None:
            payload["report_path"] = str(save_report)

        _set_json_mode(ctx, json_mode)
        _echo(ctx, payload, message=report.render_summary())
        task.succeed(payload=payload)


@app.command()
def history(
    ctx: typer.Context,
    limit: int = typer.Option(20, "--limit", "-n", help="Number of events to display"),
    since: Optional[str] = typer.Option(
        None,
        "--since",
        help="Only include events at or after the provided ISO timestamp",
    ),
    commands: List[str] = typer.Option(
        [],
        "--command",
        "-c",
        help="Only include events emitted by the specified command (repeatable).",
    ),
    statuses: List[str] = typer.Option(
        [],
        "--status",
        "-s",
        help="Only include events whose status matches the provided values.",
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
        "commands": commands,
        "statuses": statuses,
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

        command_filter = sorted({name.strip() for name in commands if name.strip()})
        command_set = set(command_filter) if command_filter else None
        status_filter = sorted({status.strip().lower() for status in statuses if status.strip()})
        status_set = set(status_filter) if status_filter else None

        events = worker_hive.tail_events(limit=limit, since=since_marker)
        current_task_id = getattr(task, "task_id", None)
        ordered_events = [
            event
            for event in reversed(events)
            if event.get("task_id") != current_task_id
            and (command_set is None or str(event.get("name", "")) in command_set)
            and (
                status_set is None
                or str(event.get("status", ""))
                .strip()
                .lower()
                in status_set
            )
        ]

        payload: dict[str, object] = {
            "events": ordered_events,
            "log_path": str(worker_hive.log_path),
            "count": len(ordered_events),
            "commands": command_filter,
            "statuses": status_filter,
        }

        if ctx.obj.get("json", False):
            _echo(ctx, payload)
        else:
            if not ordered_events:
                if command_filter:
                    console.print(
                        "No worker activity recorded for the selected command filter yet."
                    )
                else:
                    console.print(
                        "No worker activity recorded yet. Instrumented commands will appear here once executed."
                    )
            else:
                scope_parts: list[str] = []
                if command_filter:
                    scope_parts.append(", ".join(command_filter))
                if status_filter:
                    scope_parts.append(
                        "status in (" + ", ".join(status_filter) + ")"
                    )
                scope = " & ".join(scope_parts) if scope_parts else "all instrumented commands"
                if FALLBACK_TABLE:
                    console.print(
                        f"Recent worker events ({len(ordered_events)}) from {worker_hive.log_path} (scope: {scope}):"
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
                    table = Table(title=f"Recent worker activity ({scope})")
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
def status(
    ctx: typer.Context,
    since: Optional[str] = typer.Option(
        None,
        "--since",
        help="Only include events at or after the provided ISO timestamp",
    ),
    commands: List[str] = typer.Option(
        [],
        "--command",
        "-c",
        help="Only include events emitted by the specified command (repeatable).",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Summarise worker hive activity across all instrumented commands."""

    metadata = {"since": since, "json": json_mode, "commands": commands}

    with worker_hive.worker("status", metadata=metadata) as task:
        _set_json_mode(ctx, json_mode)

        since_marker: Optional[str] = None
        if since is not None:
            try:
                since_marker = _normalise_iso_timestamp(since)
            except ValueError as exc:
                task.fail(error="invalid_since", since=since)
                raise typer.BadParameter(f"Invalid ISO timestamp: {since}") from exc

        command_filter = sorted({name.strip() for name in commands if name.strip()})
        command_set = set(command_filter) if command_filter else None

        events = worker_hive.tail_events(limit=None, since=since_marker)
        aggregates = _aggregate_worker_events(events, command_filter=command_set)
        aggregates["log_path"] = str(worker_hive.log_path)
        aggregates["since"] = since_marker
        aggregates["commands"] = command_filter

        if ctx.obj.get("json", False):
            _echo(ctx, aggregates)
        else:
            total = aggregates["total_events"]
            unique = aggregates["unique_commands"]
            active = aggregates["active_tasks"]
            last_event = aggregates.get("last_event")
            scope = ", ".join(command_filter) if command_filter else "all commands"

            console.print(
                f"Worker hive summary for {scope}: {total} events across {unique} commands (active tasks: {active})"
            )
            if last_event:
                console.print(f"Most recent event recorded at {last_event}")
            console.print(f"Log file: {aggregates['log_path']}")
            if since_marker:
                console.print(f"Filtered from: {since_marker}")

            status_counts = aggregates["status_counts"]
            command_activity = aggregates["command_activity"]

            if status_counts:
                if FALLBACK_TABLE:
                    console.print("Status counts:")
                    for status, count in sorted(status_counts.items()):
                        console.print(f"  {status}: {count}")
                else:
                    status_table = Table(title="Event statuses")
                    status_table.add_column("Status", style="green")
                    status_table.add_column("Count", justify="right")
                    for status, count in sorted(status_counts.items()):
                        status_table.add_row(str(status), str(count))
                    console.print(status_table)

            if command_activity:
                sorted_activity = sorted(
                    command_activity.items(), key=lambda item: (-item[1], item[0])
                )
                if FALLBACK_TABLE:
                    console.print("Command activity:")
                    for name, count in sorted_activity:
                        console.print(f"  {name}: {count}")
                else:
                    command_table = Table(title="Command activity")
                    command_table.add_column("Command", style="magenta")
                    command_table.add_column("Events", justify="right")
                    for name, count in sorted_activity:
                        command_table.add_row(str(name), str(count))
                    console.print(command_table)

        task.succeed(payload=aggregates)


@app.command()
def digest(
    ctx: typer.Context,
    limit: int = typer.Option(
        800,
        "--window",
        "-w",
        help="Number of recent worker events inspected for the digest.",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Summarise the busiest commands, statuses, and time windows."""

    metadata = {"window": limit, "json": json_mode}

    with worker_hive.worker("digest", metadata=metadata) as task:
        if limit <= 0:
            task.fail(error="invalid_window", window=limit)
            raise typer.BadParameter("--window must be a positive integer")

        _set_json_mode(ctx, json_mode)
        events = worker_hive.tail_events(limit=limit)
        now = datetime.now(timezone.utc)
        status_counts: Counter[str] = Counter()
        command_counts: Counter[str] = Counter()
        hourly_counts: Counter[str] = Counter()
        first_dt: datetime | None = None
        last_dt: datetime | None = None

        for event in events:
            status = str(event.get("status", "unknown")) or "unknown"
            command = str(event.get("name", "-")) or "-"
            status_counts[status] += 1
            command_counts[command] += 1
            timestamp = _parse_iso_timestamp(event.get("timestamp"))
            if not timestamp:
                continue
            if first_dt is None or timestamp < first_dt:
                first_dt = timestamp
            if last_dt is None or timestamp > last_dt:
                last_dt = timestamp
            bucket = timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_counts[_format_iso(bucket) or "-"] += 1

        span_seconds = None
        if first_dt and last_dt:
            span_seconds = max((last_dt - first_dt).total_seconds(), 0.0)
        freshness_seconds = None
        if last_dt:
            freshness_seconds = max((now - last_dt).total_seconds(), 0.0)

        events_per_hour = None
        if span_seconds and span_seconds > 0:
            hours = span_seconds / 3600
            if hours > 0:
                events_per_hour = len(events) / hours

        try:
            file_size = worker_hive.log_path.stat().st_size
        except OSError:
            file_size = None

        busiest_hours = [
            {"hour": hour, "events": count}
            for hour, count in sorted(
                hourly_counts.items(), key=lambda item: item[1], reverse=True
            )[:5]
        ]

        payload = {
            "log_path": str(worker_hive.log_path),
            "event_limit": limit,
            "event_count": len(events),
            "status_counts": dict(status_counts),
            "command_counts": dict(command_counts),
            "hourly_activity": busiest_hours,
            "window_start": _format_iso(first_dt),
            "window_end": _format_iso(last_dt),
            "window_span_seconds": span_seconds,
            "freshness_seconds": freshness_seconds,
            "events_per_hour": events_per_hour,
            "file_size_bytes": file_size,
        }

        if ctx.obj.get("json", False):
            _echo(ctx, payload)
        else:
            console.print(
                f"Digest of {payload['event_count']} events (limit {limit}) "
                f"from {payload['log_path']}"
            )
            if payload["window_start"] and payload["window_end"]:
                span_text = _format_duration(payload["window_span_seconds"])
                console.print(
                    f"Window: {payload['window_start']} → {payload['window_end']} "
                    f"({span_text})"
                )
            if payload["freshness_seconds"] is not None:
                console.print(
                    "Last event "
                    f"{_format_duration(payload['freshness_seconds'])} ago."
                )
            if file_size is not None:
                console.print(f"Log size: {file_size/1024:.1f} KiB")
            if events_per_hour is not None:
                console.print(f"Average activity: {events_per_hour:.2f} events/hour")

            if status_counts:
                if FALLBACK_TABLE:
                    console.print("Statuses:")
                    for status, count in sorted(status_counts.items()):
                        console.print(f"  {status}: {count}")
                else:
                    status_table = Table(title="Status distribution")
                    status_table.add_column("Status", style="green")
                    status_table.add_column("Events", justify="right")
                    for status, count in sorted(status_counts.items()):
                        status_table.add_row(str(status), str(count))
                    console.print(status_table)

            if command_counts:
                top_commands = sorted(
                    command_counts.items(), key=lambda item: (-item[1], item[0])
                )[:10]
                if FALLBACK_TABLE:
                    console.print("Top commands:")
                    for name, count in top_commands:
                        console.print(f"  {name}: {count}")
                else:
                    command_table = Table(title="Most active commands")
                    command_table.add_column("Command", style="magenta")
                    command_table.add_column("Events", justify="right")
                    for name, count in top_commands:
                        command_table.add_row(str(name), str(count))
                    console.print(command_table)

            if busiest_hours:
                if FALLBACK_TABLE:
                    console.print("Busiest hours (UTC):")
                    for row in busiest_hours:
                        console.print(f"  {row['hour']}: {row['events']} events")
                else:
                    hour_table = Table(title="Busiest hours (UTC)")
                    hour_table.add_column("Hour", style="cyan")
                    hour_table.add_column("Events", justify="right")
                    for row in busiest_hours:
                        hour_table.add_row(row["hour"], str(row["events"]))
                    console.print(hour_table)

        task.succeed(payload=payload)


@app.command()
def reliability(
    ctx: typer.Context,
    window: int = typer.Option(
        400,
        "--window",
        "-w",
        help="Number of recent worker events inspected for reliability analytics.",
    ),
    show_active: bool = typer.Option(
        True,
        "--show-active/--hide-active",
        help="Display tasks that started but never completed in the inspected window.",
    ),
    show_failures: bool = typer.Option(
        True,
        "--show-failures/--hide-failures",
        help="Display the most recent failed tasks in the inspected window.",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Surface slow, failing, and stuck workers to build delivery trust."""

    metadata = {
        "window": window,
        "show_active": show_active,
        "show_failures": show_failures,
        "json": json_mode,
    }
    with worker_hive.worker("reliability", metadata=metadata) as task:
        if window <= 0:
            task.fail(error="invalid_window", window=window)
            raise typer.BadParameter("window must be a positive integer")

        _set_json_mode(ctx, json_mode)
        events = worker_hive.tail_events(limit=window)
        metrics = _derive_task_metrics(events)
        payload: dict[str, Any] = {
            **metrics,
            "log_path": str(worker_hive.log_path),
            "event_count": len(events),
            "window": window,
        }

        if ctx.obj.get("json", False):
            _echo(ctx, payload)
        else:
            stats = metrics["stats"]
            console.print(
                f"Reliability scan over {payload['event_count']} events (log: {payload['log_path']})."
            )
            console.print(
                "Completed tasks: "
                f"{stats['completed_total']} (success {stats['success_total']}, "
                f"failures {stats['failure_total']}, skipped {stats['skipped_total']})."
            )
            console.print(
                f"Failure rate: {stats['failure_rate']:.1%} | Active tasks: {stats['active_total']}"
            )
            avg = _format_duration(stats["average_duration_seconds"])
            p90 = _format_duration(stats["p90_duration_seconds"])
            console.print(f"Average duration: {avg} | p90 duration: {p90}")

            slowest = metrics["slowest_tasks"]
            if slowest:
                if FALLBACK_TABLE:
                    console.print("Slowest completed tasks:")
                    for task_info in slowest:
                        console.print(
                            f"{task_info['name']} ({task_info['status']}) - "
                            f"{_format_duration(task_info['duration_seconds'])}"
                        )
                else:
                    table = Table(title="Slowest completed tasks")
                    table.add_column("Command", style="magenta")
                    table.add_column("Status", style="green")
                    table.add_column("Duration", justify="right")
                    table.add_column("Finished at", style="cyan")
                    for task_info in slowest:
                        table.add_row(
                            task_info["name"],
                            task_info["status"],
                            _format_duration(task_info["duration_seconds"]),
                            task_info.get("finished_at", "-"),
                        )
                    console.print(table)
            else:
                console.print("No completed tasks recorded in the selected window yet.")

            if show_active and metrics["active_tasks"]:
                if FALLBACK_TABLE:
                    console.print("Active tasks:")
                    for task_info in metrics["active_tasks"]:
                        console.print(
                            f"{task_info['name']} age={_format_duration(task_info['age_seconds'])} "
                            f"heartbeat={_format_duration(task_info['last_heartbeat_seconds'])}"
                        )
                else:
                    table = Table(title="Active / incomplete tasks")
                    table.add_column("Command", style="yellow")
                    table.add_column("Age", justify="right")
                    table.add_column("Since heartbeat", justify="right")
                    table.add_column("Progress updates", justify="right")
                    for task_info in metrics["active_tasks"]:
                        table.add_row(
                            task_info["name"],
                            _format_duration(task_info["age_seconds"]),
                            _format_duration(task_info["last_heartbeat_seconds"]),
                            str(task_info["progress_updates"]),
                        )
                    console.print(table)
            elif show_active:
                console.print("No active worker tasks detected in the selected window.")

            if show_failures and metrics["recent_failures"]:
                if FALLBACK_TABLE:
                    console.print("Recent failures:")
                    for task_info in metrics["recent_failures"]:
                        console.print(
                            f"{task_info['name']} failed after "
                            f"{_format_duration(task_info['duration_seconds'])}"
                        )
                else:
                    table = Table(title="Recent failures")
                    table.add_column("Command", style="red")
                    table.add_column("Duration", justify="right")
                    table.add_column("Finished at", style="cyan")
                    for task_info in metrics["recent_failures"]:
                        table.add_row(
                            task_info["name"],
                            _format_duration(task_info["duration_seconds"]),
                            task_info.get("finished_at", "-"),
                        )
                    console.print(table)
            elif show_failures:
                console.print("No failed tasks detected in the selected window.")

        task.succeed(payload=payload)


@app.command("command-health")
def command_health(
    ctx: typer.Context,
    window: int = typer.Option(
        600,
        "--window",
        "-w",
        help="Number of recent worker events inspected for command analytics.",
    ),
    limit: int = typer.Option(
        8,
        "--limit",
        "-n",
        help="Number of commands to display in the console view.",
    ),
    sort_by: str = typer.Option(
        "failures",
        "--sort-by",
        help="Rank commands by failures, duration, runs, or stale heartbeats.",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Highlight per-command health signals to build delivery trust."""

    metadata = {"window": window, "limit": limit, "sort_by": sort_by, "json": json_mode}
    with worker_hive.worker("command_health", metadata=metadata) as task:
        if window <= 0:
            task.fail(error="invalid_window", window=window)
            raise typer.BadParameter("window must be a positive integer")
        if limit <= 0:
            task.fail(error="invalid_limit", limit=limit)
            raise typer.BadParameter("limit must be a positive integer")

        sort_key = sort_by.strip().lower()
        sort_map: dict[str, Callable[[Mapping[str, Any]], float]] = {
            "failures": lambda row: float(row["failure"]),
            "duration": lambda row: float(row.get("average_duration_seconds") or 0.0),
            "runs": lambda row: float(row["completed"]),
            "stale": lambda row: float(row.get("stale_heartbeats_seconds") or 0.0),
        }
        if sort_key not in sort_map:
            task.fail(error="invalid_sort", sort_by=sort_by)
            allowed = ", ".join(sorted(sort_map.keys()))
            raise typer.BadParameter(f"--sort-by must be one of: {allowed}")

        _set_json_mode(ctx, json_mode)
        events = worker_hive.tail_events(limit=window)
        metrics = _compute_command_performance(events)
        commands = metrics["commands"]
        sorted_commands = sorted(commands, key=sort_map[sort_key], reverse=True)
        top_commands = sorted_commands[:limit]
        payload = {
            "totals": metrics["totals"],
            "commands": commands,
            "top_commands": top_commands,
            "window": window,
            "sort_by": sort_key,
            "event_count": len(events),
        }

        if ctx.obj.get("json", False):
            _echo(ctx, payload)
        else:
            console.print(
                "Command health scan across "
                f"{payload['event_count']} events (log: {worker_hive.log_path})."
            )
            totals = payload["totals"]
            console.print(
                "Tracked commands: "
                f"{totals['commands_tracked']} | Completed tasks: {totals['completed_tasks']} "
                f"| Active tasks: {totals['active_tasks']} | Failure rate: {totals['overall_failure_rate']:.1%}"
            )
            if not top_commands:
                console.print("No instrumented commands have completed runs yet.")
            else:
                title = (
                    f"Top {len(top_commands)} commands (sorted by {sort_key})"
                )
                if FALLBACK_TABLE:
                    console.print(title)
                    for row in top_commands:
                        console.print(
                            f"{row['command']}: completed {row['completed']} | "
                            f"failures {row['failure']} | active {row['active']} | "
                            f"success-rate {row['success_rate']:.1%} | "
                            f"avg {_format_duration(row.get('average_duration_seconds'))}"
                        )
                else:
                    table = Table(title=title)
                    table.add_column("Command", style="magenta")
                    table.add_column("Completed", justify="right")
                    table.add_column("Failures", justify="right")
                    table.add_column("Active", justify="right")
                    table.add_column("Success rate", justify="right")
                    table.add_column("Avg", justify="right")
                    table.add_column("P95", justify="right")
                    table.add_column("Last finished", style="cyan")
                    table.add_column("Stale heartbeat", justify="right")
                    for row in top_commands:
                        table.add_row(
                            row["command"],
                            str(row["completed"]),
                            str(row["failure"]),
                            str(row["active"]),
                            f"{row['success_rate']:.1%}",
                            _format_duration(row.get("average_duration_seconds")),
                            _format_duration(row.get("p95_duration_seconds")),
                            row.get("last_finished_at") or "-",
                            _format_duration(row.get("stale_heartbeats_seconds")),
                        )
                    console.print(table)

        task.succeed(payload=payload)


@app.command()
def insights(
    ctx: typer.Context,
    window: int = typer.Option(
        600,
        "--window",
        "-w",
        help="Number of recent worker events to analyze for operational insights.",
    ),
    command_name: Optional[str] = typer.Option(
        None,
        "--command",
        "-c",
        help="Only include telemetry emitted by the specified command name.",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Generate throughput, concurrency, and reliability insights."""

    metadata = {
        "window": window,
        "command": command_name,
        "json": json_mode,
    }

    with worker_hive.worker("insights", metadata=metadata) as task:
        if window <= 0:
            task.fail(error="invalid_window", window=window)
            raise typer.BadParameter("window must be a positive integer")

        _set_json_mode(ctx, json_mode)
        events = worker_hive.tail_events(limit=window)
        insights_payload = _compute_timeline_insights(
            events, command_filter=command_name
        )
        payload = {
            "insights": insights_payload,
            "event_count": len(events),
            "window": window,
            "log_path": str(worker_hive.log_path),
            "command": command_name,
        }

        if ctx.obj.get("json", False):
            _echo(ctx, payload)
        else:
            summary = insights_payload["summary"]
            target = command_name or "all commands"
            console.print(
                f"Operational insights for {target} using {payload['event_count']} events"
                f" (log: {payload['log_path']})."
            )
            if summary["window_start"] and summary["window_end"]:
                console.print(
                    f"Window: {summary['window_start']} to {summary['window_end']}"
                )

            avg = _format_duration(summary["average_duration_seconds"])
            med = _format_duration(summary["median_duration_seconds"])
            p95 = _format_duration(summary["p95_duration_seconds"])
            concurrency = insights_payload["concurrency"]
            peak = concurrency.get("peak", 0)
            peak_at = concurrency.get("timestamp") or "-"
            streaks = insights_payload["streaks"]

            if FALLBACK_TABLE:
                console.print(
                    f"Completed: {summary['completed_tasks']} | Active: {summary['active_tasks']}"
                )
                console.print(
                    f"Success {summary['success']} • Failure {summary['failure']} • Skipped {summary['skipped']}"
                )
                console.print(
                    f"Success rate: {summary['success_rate']:.1%} | "
                    f"avg {avg} | median {med} | p95 {p95}"
                )
                console.print(
                    f"Peak concurrency: {peak} workers @ {peak_at}"
                )
                console.print(
                    f"Success streak: {streaks['success']['length']} • Failure streak: {streaks['failure']['length']}"
                )
            else:
                summary_table = Table(title="Operational summary")
                summary_table.add_column("Metric", style="cyan")
                summary_table.add_column("Value", justify="right")
                summary_table.add_row("Completed", str(summary["completed_tasks"]))
                summary_table.add_row("Active", str(summary["active_tasks"]))
                summary_table.add_row("Success", str(summary["success"]))
                summary_table.add_row("Failure", str(summary["failure"]))
                summary_table.add_row("Skipped", str(summary["skipped"]))
                summary_table.add_row("Success rate", f"{summary['success_rate']:.1%}")
                summary_table.add_row("Average", avg)
                summary_table.add_row("Median", med)
                summary_table.add_row("p95", p95)
                summary_table.add_row("Peak concurrency", str(peak))
                summary_table.add_row("Peak at", peak_at)
                summary_table.add_row(
                    "Success streak",
                    str(streaks["success"]["length"]),
                )
                summary_table.add_row(
                    "Failure streak",
                    str(streaks["failure"]["length"]),
                )
                console.print(summary_table)

            hourly_rows = insights_payload["hourly_throughput"][-12:]
            if hourly_rows:
                if FALLBACK_TABLE:
                    console.print("Hourly throughput (most recent):")
                    for row in hourly_rows:
                        console.print(
                            f"  {row['hour']}: total {row['completed']}"
                            f" (success {row['success']}, failure {row['failure']})"
                        )
                else:
                    throughput_table = Table(title="Hourly throughput (UTC)")
                    throughput_table.add_column("Hour", style="magenta")
                    throughput_table.add_column("Completed", justify="right")
                    throughput_table.add_column("Success", justify="right")
                    throughput_table.add_column("Failure", justify="right")
                    throughput_table.add_column("Skipped", justify="right")
                    for row in hourly_rows:
                        throughput_table.add_row(
                            row["hour"],
                            str(row["completed"]),
                            str(row["success"]),
                            str(row["failure"]),
                            str(row["skipped"]),
                        )
                    console.print(throughput_table)

            idle_windows = insights_payload["idle_windows"]
            if idle_windows:
                if FALLBACK_TABLE:
                    console.print("Longest idle windows:")
                    for window_entry in idle_windows:
                        console.print(
                            f"  {window_entry['start']} → {window_entry['end']}"
                            f" ({_format_duration(window_entry['duration_seconds'])})"
                        )
                else:
                    idle_table = Table(title="Longest idle windows")
                    idle_table.add_column("Start", style="red")
                    idle_table.add_column("End", style="green")
                    idle_table.add_column("Duration", justify="right")
                    for window_entry in idle_windows:
                        idle_table.add_row(
                            window_entry["start"],
                            window_entry["end"],
                            _format_duration(window_entry["duration_seconds"]),
                        )
                    console.print(idle_table)

            if insights_payload["active_focus"]:
                if FALLBACK_TABLE:
                    console.print("Oldest active workers:")
                    for entry in insights_payload["active_focus"]:
                        console.print(
                            f"  {entry['name']} age={_format_duration(entry['age_seconds'])}"
                            f" heartbeat={_format_duration(entry['last_heartbeat_seconds'])}"
                        )
                else:
                    active_table = Table(title="Oldest active workers")
                    active_table.add_column("Command", style="yellow")
                    active_table.add_column("Age", justify="right")
                    active_table.add_column("Since heartbeat", justify="right")
                    for entry in insights_payload["active_focus"]:
                        active_table.add_row(
                            entry["name"],
                            _format_duration(entry["age_seconds"]),
                            _format_duration(entry["last_heartbeat_seconds"]),
                        )
                    console.print(active_table)

            if insights_payload["recent_completions"]:
                if FALLBACK_TABLE:
                    console.print("Recent completions:")
                    for entry in insights_payload["recent_completions"]:
                        console.print(
                            f"  {entry['finished_at']} {entry['name']}"
                            f" ({entry['status']}) {_format_duration(entry['duration_seconds'])}"
                        )
                else:
                    recent_table = Table(title="Recent completions")
                    recent_table.add_column("Finished", style="cyan")
                    recent_table.add_column("Command", style="green")
                    recent_table.add_column("Status", style="magenta")
                    recent_table.add_column("Duration", justify="right")
                    for entry in insights_payload["recent_completions"]:
                        recent_table.add_row(
                            entry["finished_at"] or "-",
                            entry["name"],
                            entry["status"],
                            _format_duration(entry["duration_seconds"]),
                        )
                    console.print(recent_table)

        task.succeed(payload=payload)


@app.command()
def timeline(
    ctx: typer.Context,
    window: int = typer.Option(
        600,
        "--window",
        "-w",
        help="Number of recent worker events considered for the timeline.",
    ),
    command_name: Optional[str] = typer.Option(
        None,
        "--command",
        "-c",
        help="Only include telemetry emitted by the specified command name.",
    ),
    display_hours: int = typer.Option(
        12,
        "--display-hours",
        "-d",
        help="Number of hourly buckets to render in the textual output.",
    ),
    export_csv: Optional[Path] = typer.Option(
        None,
        "--export-csv",
        help="Optional path used to export the hourly throughput as CSV.",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Visualise hourly throughput trends for worker activity."""

    metadata = {
        "window": window,
        "command": command_name,
        "display_hours": display_hours,
        "export_csv": str(export_csv) if export_csv else None,
        "json": json_mode,
    }

    with worker_hive.worker("timeline", metadata=metadata) as task:
        if window <= 0:
            task.fail(error="invalid_window", window=window)
            raise typer.BadParameter("window must be a positive integer")
        if display_hours <= 0:
            task.fail(error="invalid_display_hours", display_hours=display_hours)
            raise typer.BadParameter("--display-hours must be a positive integer")

        _set_json_mode(ctx, json_mode)
        events = worker_hive.tail_events(limit=window)
        insights_payload = _compute_timeline_insights(
            events, command_filter=command_name
        )
        hourly = insights_payload["hourly_throughput"]

        export_path: str | None = None
        if export_csv is not None:
            export_csv.parent.mkdir(parents=True, exist_ok=True)
            with export_csv.open("w", encoding="utf-8") as handle:
                handle.write("hour,completed,success,failure,skipped\n")
                for row in hourly:
                    handle.write(
                        f"{row['hour']},{row['completed']},{row['success']},{row['failure']},{row['skipped']}\n"
                    )
            export_path = str(export_csv)

        payload = {
            "insights": insights_payload,
            "hourly_throughput": hourly,
            "event_count": len(events),
            "window": window,
            "command": command_name,
            "display_hours": display_hours,
            "export_path": export_path,
            "log_path": str(worker_hive.log_path),
        }

        if ctx.obj.get("json", False):
            _echo(ctx, payload)
        else:
            target = command_name or "all commands"
            console.print(
                f"Hourly timeline for {target} built from {payload['event_count']} events"
                f" (log: {payload['log_path']})."
            )
            if not hourly:
                console.print("No completed tasks found in the inspected window yet.")
            else:
                display_rows = hourly[-display_hours:]
                max_completed = max((row["completed"] for row in display_rows), default=0)
                scale = max(max_completed, 1)
                if FALLBACK_TABLE:
                    console.print("Hourly throughput (UTC):")
                    for row in display_rows:
                        bar_units = max(1, int(round((row["completed"] / scale) * 20)))
                        bar = "█" * bar_units if row["completed"] else "·"
                        hour_text = row.get("hour") or "-"
                        console.print(
                            f"{hour_text} | {bar} ({row['completed']}) "
                            f"success={row['success']} failure={row['failure']}"
                        )
                else:
                    table = Table(
                        title=f"Hourly throughput (last {len(display_rows)} buckets)",
                    )
                    table.add_column("Hour", style="cyan")
                    table.add_column("Completed", justify="right")
                    table.add_column("Success", justify="right")
                    table.add_column("Failure", justify="right")
                    table.add_column("Skipped", justify="right")
                    table.add_column("Relative load", style="green")
                    for row in display_rows:
                        bar_units = max(1, int(round((row["completed"] / scale) * 20)))
                        bar = "█" * bar_units if row["completed"] else "·"
                        hour_text = row.get("hour") or "-"
                        table.add_row(
                            hour_text,
                            str(row["completed"]),
                            str(row["success"]),
                            str(row["failure"]),
                            str(row["skipped"]),
                            bar,
                        )
                    console.print(table)

            idle_windows = insights_payload["idle_windows"]
            if idle_windows:
                longest = idle_windows[0]
                console.print(
                    "Longest idle gap: "
                    f"{_format_duration(longest['duration_seconds'])} between {longest['start']} and {longest['end']}"
                )
            else:
                console.print("No idle gaps detected between observed completions.")

        if export_path:
            console.print(f"Hourly throughput exported to {export_path}.")

        task.succeed(payload=payload)


@app.command()
def capacity_plan(
    ctx: typer.Context,
    backlog: int = typer.Option(
        50,
        "--backlog",
        "-b",
        help="Number of outstanding tasks waiting to be processed.",
    ),
    window: int = typer.Option(
        800,
        "--window",
        "-w",
        help="Number of recent worker events to use when forecasting throughput.",
    ),
    parallelism: int = typer.Option(
        1,
        "--parallelism",
        "-p",
        help="Assumed number of workers processing the backlog concurrently.",
    ),
    confidence: float = typer.Option(
        0.8,
        "--confidence",
        help="Confidence level (0-1) for the minimum throughput floor.",
    ),
    command_name: Optional[str] = typer.Option(
        None,
        "--command",
        "-c",
        help="Only use telemetry emitted by the specified command name.",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text"
    ),
) -> None:
    """Forecast how long it will take to clear the current backlog."""

    metadata = {
        "backlog": backlog,
        "window": window,
        "parallelism": parallelism,
        "confidence": confidence,
        "command": command_name,
        "json": json_mode,
    }

    with worker_hive.worker("capacity_plan", metadata=metadata) as task:
        if backlog < 0:
            task.fail(error="invalid_backlog", backlog=backlog)
            raise typer.BadParameter("--backlog must be zero or a positive integer")
        if window <= 0:
            task.fail(error="invalid_window", window=window)
            raise typer.BadParameter("--window must be a positive integer")
        if parallelism <= 0:
            task.fail(error="invalid_parallelism", parallelism=parallelism)
            raise typer.BadParameter("--parallelism must be at least 1")
        if not (0.0 < confidence < 1.0):
            task.fail(error="invalid_confidence", confidence=confidence)
            raise typer.BadParameter("--confidence must be between 0 and 1")

        _set_json_mode(ctx, json_mode)
        events = worker_hive.tail_events(limit=window)
        insights_payload = _compute_timeline_insights(
            events, command_filter=command_name
        )
        summary = insights_payload["summary"]
        hourly_rows = insights_payload["hourly_throughput"]
        hourly_success_values = [
            row["success"]
            for row in hourly_rows
            if isinstance(row.get("success"), int)
        ]

        avg_success_per_hour = (
            mean(hourly_success_values) if hourly_success_values else None
        )
        span_seconds = summary.get("window_span_seconds") or 0
        if (avg_success_per_hour is None or avg_success_per_hour == 0) and span_seconds > 0:
            span_hours = span_seconds / 3600
            if span_hours > 0:
                avg_success_per_hour = (
                    summary.get("success", 0) / span_hours if summary.get("success") else None
                )

        confident_rate = None
        if hourly_success_values:
            confident_fraction = max(0.0, min(1.0, 1.0 - confidence))
            confident_rate = _percentile(
                sorted(hourly_success_values), confident_fraction
            )
        peak_rate = max(hourly_success_values) if hourly_success_values else None
        planning_rate = confident_rate or avg_success_per_hour
        if planning_rate is not None and planning_rate <= 0:
            planning_rate = None

        eta_hours = None
        eta_timestamp = None
        if backlog == 0:
            eta_hours = 0.0
            eta_timestamp = _format_iso(datetime.now(timezone.utc))
        elif planning_rate:
            eta_hours = backlog / (planning_rate * parallelism)
            eta_timestamp = _format_iso(
                datetime.now(timezone.utc) + timedelta(hours=eta_hours)
            )

        completed_total = summary.get("completed_tasks", 0) or 0
        failure_rate = (
            summary.get("failure", 0) / completed_total if completed_total else 0.0
        )
        recommended_buffer = math.ceil(backlog * failure_rate) if backlog else 0

        payload = {
            "event_count": len(events),
            "window": window,
            "log_path": str(worker_hive.log_path),
            "command": command_name,
            "backlog": backlog,
            "parallelism": parallelism,
            "confidence": confidence,
            "rates": {
                "hourly_average": avg_success_per_hour,
                "hourly_confident": confident_rate,
                "hourly_peak": peak_rate,
            },
            "planning_rate": planning_rate,
            "eta_hours": eta_hours,
            "eta_timestamp": eta_timestamp,
            "failure_rate": failure_rate,
            "recommended_buffer": recommended_buffer,
            "insights": insights_payload,
        }

        if ctx.obj.get("json", False):
            _echo(ctx, payload)
        else:
            target = command_name or "all commands"
            console.print(
                f"Capacity plan for {target}: backlog={backlog} tasks using {payload['event_count']} events"
                f" (log: {payload['log_path']})."
            )
            planning_text = (
                f"{planning_rate:.2f} tasks/hr" if planning_rate is not None else "-"
            )
            console.print(
                f"Parallelism: {parallelism} | Confidence: {confidence:.0%} "
                f"| Planning rate: {planning_text}"
            )

            if eta_hours is not None:
                console.print(
                    f"Estimated completion: {_format_hours(eta_hours)} (ETA {eta_timestamp or '-'})"
                )
            else:
                console.print(
                    "Not enough throughput telemetry to estimate completion yet."
                )

            console.print(
                f"Failure rate: {failure_rate:.1%} | Recommended buffer: {recommended_buffer} tasks"
            )

            if not FALLBACK_TABLE:
                rate_table = Table(title="Hourly throughput scenarios")
                rate_table.add_column("Scenario", style="cyan")
                rate_table.add_column("Throughput", justify="right")
                for label, value in [
                    ("Average", avg_success_per_hour),
                    (f"{confidence:.0%} floor", confident_rate),
                    ("Peak hour", peak_rate),
                ]:
                    rate_text = f"{value:.2f} tasks/hr" if value is not None else "-"
                    rate_table.add_row(label, rate_text)
                console.print(rate_table)
            else:
                console.print("Throughput scenarios:")
                for label, value in [
                    ("Average", avg_success_per_hour),
                    (f"{confidence:.0%} floor", confident_rate),
                    ("Peak hour", peak_rate),
                ]:
                    rate_text = f"{value:.2f} tasks/hr" if value is not None else "-"
                    console.print(f"  {label}: {rate_text}")

        task.succeed(payload=payload)


@app.command("prune-log")
def prune_worker_log(
    ctx: typer.Context,
    max_events: Optional[int] = typer.Option(
        None,
        "--max-events",
        help="Keep at most this many recent events when pruning the worker log.",
    ),
    max_age_hours: Optional[float] = typer.Option(
        None,
        "--max-age-hours",
        help="Drop events older than the provided number of hours.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the pruning effect without modifying the log file.",
    ),
    json_mode: bool = typer.Option(
        False, "--json", "-j", help="Emit JSON payloads instead of rich text",
    ),
) -> None:
    """Trim worker telemetry files to avoid unbounded growth."""

    metadata = {
        "max_events": max_events,
        "max_age_hours": max_age_hours,
        "dry_run": dry_run,
        "json": json_mode,
    }

    with worker_hive.worker("prune_log", metadata=metadata) as task:
        if max_events is None and max_age_hours is None:
            task.fail(error="missing_filters")
            raise typer.BadParameter("Provide --max-events, --max-age-hours, or both")
        if max_events is not None and max_events <= 0:
            task.fail(error="invalid_max_events", max_events=max_events)
            raise typer.BadParameter("--max-events must be a positive integer")
        if max_age_hours is not None and max_age_hours <= 0:
            task.fail(error="invalid_max_age", max_age_hours=max_age_hours)
            raise typer.BadParameter("--max-age-hours must be greater than zero")

        _set_json_mode(ctx, json_mode)
        effective_dry_run = dry_run or ctx.obj.get("json", False)
        result = worker_hive.prune_events(
            max_events=max_events,
            max_age_hours=max_age_hours,
            dry_run=effective_dry_run,
        )

        payload = {"prune_result": result}
        if ctx.obj.get("json", False):
            _echo(ctx, payload)
        else:
            if result["deleted"]:
                action = "dry-run" if result["dry_run"] else "applied"
                console.print(
                    f"{action.title()} prune removed {result['deleted']} events; "
                    f"{result['after_count']} remain (log: {result['log_path']})."
                )
            else:
                console.print(
                    "Worker log already satisfies the requested limits "
                    f"(log: {result['log_path']})."
                )
            if result["filters"]:
                filters_text = ", ".join(
                    f"{key}={value}" for key, value in sorted(result["filters"].items())
                )
                console.print(f"Applied filters: {filters_text}")
            if result["dry_run"] and not dry_run:
                console.print(
                    "Note: pruning was performed in dry-run mode because --json was requested."
                )

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

    reliability_parser = subparsers.add_parser(
        "reliability", help="Surface slow, failing, and stuck worker tasks"
    )
    reliability_parser.add_argument("--window", "-w", type=int, default=400, dest="window")
    reliability_parser.add_argument(
        "--hide-active", action="store_true", dest="hide_active"
    )
    reliability_parser.add_argument(
        "--hide-failures", action="store_true", dest="hide_failures"
    )
    reliability_parser.add_argument("--json", "-j", action="store_true", dest="json_mode")

    insights_parser = subparsers.add_parser(
        "insights",
        help="Generate throughput, concurrency, and reliability insights",
    )
    insights_parser.add_argument("--window", "-w", type=int, default=600, dest="window")
    insights_parser.add_argument("--command", "-c", dest="filter_command")
    insights_parser.add_argument("--json", "-j", action="store_true", dest="json_mode")

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
    elif args.command == "reliability":
        reliability(
            ctx,
            window=args.window,
            show_active=not args.hide_active,
            show_failures=not args.hide_failures,
            json_mode=args.json_mode,
        )
    elif args.command == "insights":
        insights(
            ctx,
            window=args.window,
            command_name=args.filter_command,
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
