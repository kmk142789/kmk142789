"""Persistence utilities for Assistant Kit state and artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .config import ARTIFACT_DIR, REPORT_FILE, STATE_FILE, ensure_directories, is_path_allowed
from .models import ExecutionPlan, RunState, state_from_dict


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    if not is_path_allowed(path):
        raise PermissionError(f"writes outside approved surface: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def load_state(plan: ExecutionPlan | None = None) -> RunState:
    ensure_directories()
    data = _read_json(STATE_FILE)
    if not data and plan is None:
        raise FileNotFoundError("no prior AKit state found")
    if data:
        return state_from_dict(data)
    if plan is None:
        raise ValueError("plan required when initialising state")
    return RunState(plan=plan)


def save_state(state: RunState) -> None:
    ensure_directories()
    _write_json(STATE_FILE, state.to_dict())


def save_plan(plan: ExecutionPlan, path: Path | None = None) -> Path:
    ensure_directories()
    target = path or (ARTIFACT_DIR / f"plan-{plan.plan_id}.json")
    _write_json(target, plan.to_dict())
    return target


def save_report(report: Dict[str, Any]) -> Path:
    ensure_directories()
    _write_json(REPORT_FILE, report)
    return REPORT_FILE


def load_report() -> Dict[str, Any]:
    ensure_directories()
    return _read_json(REPORT_FILE)


def record_cycle(path: Path, payload: Dict[str, Any]) -> Path:
    if not is_path_allowed(path):
        raise PermissionError(f"writes outside approved surface: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def recent_cycle_artifacts(limit: int) -> List[Path]:
    ensure_directories()
    candidates: List[Path] = []
    if not ARTIFACT_DIR.exists():
        return candidates
    for item in sorted(ARTIFACT_DIR.glob("cycle-*.json")):
        candidates.append(item)
    return candidates[-limit:]


def prune_cycles(limit: int) -> None:
    ensure_directories()
    if limit <= 0:
        return
    cycles = sorted(ARTIFACT_DIR.glob("cycle-*.json"))
    if len(cycles) <= limit:
        return
    for path in cycles[: len(cycles) - limit]:
        path.unlink(missing_ok=True)


def manifest_path(label: str) -> Path:
    ensure_directories()
    return ARTIFACT_DIR / label


def ensure_paths_allowed(paths: Iterable[Path]) -> None:
    for path in paths:
        if not is_path_allowed(path):
            raise PermissionError(f"writes outside approved surface: {path}")
