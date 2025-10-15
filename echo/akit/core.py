"""Assistant Kit public API."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from . import config
from .config import ARTIFACT_DIR, DEFAULT_PLAN_FILE, load_config
from .models import (
    AKitReport,
    CycleRecord,
    ExecutionPlan,
    PlanStep,
    RunResult,
    RunState,
    utc_now,
)
from .persistence import (
    ensure_paths_allowed,
    load_report,
    load_state,
    manifest_path,
    prune_cycles,
    record_cycle,
    save_plan,
    save_report,
    save_state,
)


def _normalise_intention(intention: str) -> str:
    cleaned = " ".join(intention.strip().split())
    if not cleaned:
        raise ValueError("intention must not be empty")
    return cleaned


def _infer_targets(intention: str) -> List[str]:
    keyword_map = {
        "doc": "docs",
        "docs": "docs",
        "documentation": "docs",
        "guide": "docs",
        "readme": "docs",
        "test": "tests",
        "pytest": "tests",
        "cli": "echo",
        "module": "echo",
        "api": "echo",
        "code": "echo",
        "build": "echo",
        "implement": "echo",
        "refactor": "echo",
        "workflow": "modules",
        "action": "modules",
        "snapshot": "artifacts",
        "manifest": "artifacts",
    }
    lowered = intention.lower()
    targets: set[str] = set()
    for keyword, target in keyword_map.items():
        if keyword in lowered:
            targets.add(target)
    if not targets:
        targets.add("docs")
    return sorted(targets)


def _plan_steps(intention: str, targets: Sequence[str], constraints: Sequence[str]) -> List[PlanStep]:
    actions = [
        f"Summarise intention: {intention}",
        "List explicit constraints and success signals.",
    ]
    steps = [
        PlanStep(
            name="Clarify",
            goal="Align on the desired outcome and guardrails.",
            actions=actions,
            targets=["docs"],
        ),
        PlanStep(
            name="Decompose",
            goal="Break intention into deterministic work units.",
            actions=[
                "Enumerate plan steps in priority order.",
                "Map steps to responsible surfaces (code, docs, artifacts).",
            ],
            targets=list(targets),
        ),
    ]
    execution_actions = [
        "Apply the planned changes respecting safety guardrails.",
        "Capture artifacts or logs under artifacts/akit/ if applicable.",
    ]
    if constraints:
        execution_actions.append("Observe constraints: " + "; ".join(constraints))
    steps.append(
        PlanStep(
            name="Execute",
            goal="Carry out the concrete changes and record artifacts.",
            actions=execution_actions,
            targets=list(targets),
        )
    )
    steps.append(
        PlanStep(
            name="Validate",
            goal="Verify outcomes and prepare communication.",
            actions=[
                "Run pytest -q.",
                "Generate akit.report() digest and share risks/next steps.",
            ],
            targets=["tests", "artifacts", "docs"],
            risks=["Missing approvals or failing tests will block merge."],
        )
    )
    return steps


def _plan_id(payload: Dict[str, object]) -> str:
    serialised = json.dumps(payload, sort_keys=True)
    digest = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
    return digest[:16]


def plan(
    intention: str,
    *,
    constraints: Optional[Sequence[str]] = None,
) -> ExecutionPlan:
    """Turn a high-level intention into an execution plan."""

    cleaned = _normalise_intention(intention)
    constraint_list = [c for c in (constraints or []) if c]
    targets = _infer_targets(cleaned)
    steps = _plan_steps(cleaned, targets, constraint_list)
    payload = {
        "intent": cleaned,
        "steps": [step.to_dict() for step in steps],
        "constraints": constraint_list,
    }
    plan_id = _plan_id(payload)
    requires_codeowners = any(target != "docs" for target in targets)
    execution_plan = ExecutionPlan(
        plan_id=plan_id,
        intent=cleaned,
        created_at=utc_now(),
        steps=steps,
        constraints=constraint_list,
        requires_codeowners=requires_codeowners,
    )
    save_plan(execution_plan)
    save_plan(execution_plan, DEFAULT_PLAN_FILE)
    return execution_plan


def _clone_state(state: RunState) -> RunState:
    return RunState(
        plan=state.plan,
        completed_steps=list(state.completed_steps),
        cycles=list(state.cycles),
        last_cycle_at=state.last_cycle_at,
    )


def _determine_next_step(state: RunState) -> Optional[int]:
    total = len(state.plan.steps)
    for index in range(total):
        if index not in state.completed_steps:
            return index
    return None


def _cycle_path(index: int) -> Path:
    return ARTIFACT_DIR / f"cycle-{index:04d}.json"


def _build_report(state: RunState, *, blocked: bool) -> AKitReport:
    completed_names = [state.plan.steps[i].name for i in state.completed_steps if i < len(state.plan.steps)]
    pending_names = [
        state.plan.steps[i].name
        for i in range(len(state.plan.steps))
        if i not in state.completed_steps
    ]
    next_step = pending_names[0] if pending_names else None
    risks: List[str] = []
    if blocked:
        risks.append("CODEOWNERS approval required before execution.")
    for step in state.plan.steps:
        risks.extend(step.risks)
    return AKitReport(
        plan_id=state.plan.plan_id,
        generated_at=utc_now() if state.last_cycle_at is None else state.last_cycle_at,
        progress=state.progress,
        completed=completed_names,
        pending=pending_names,
        requires_codeowners=state.plan.requires_codeowners,
        next_step=next_step,
        risks=sorted(set(risks)),
    )


def run(
    plan_obj: ExecutionPlan,
    *,
    cycles: int = 1,
    dry_run: bool = False,
    resume: bool = True,
    limit_artifacts: Optional[int] = None,
) -> RunResult:
    """Execute a plan over multiple cycles."""

    if cycles <= 0:
        raise ValueError("cycles must be positive")
    cfg = load_config(artifact_limit=limit_artifacts)
    try:
        state = load_state() if resume else RunState(plan=plan_obj)
    except FileNotFoundError:
        state = RunState(plan=plan_obj)
    if state.plan.plan_id != plan_obj.plan_id:
        state = RunState(plan=plan_obj)
    active_state = _clone_state(state)
    artifacts: List[str] = []
    blocked = plan_obj.requires_codeowners and not cfg.approval_granted

    for _ in range(cycles):
        cycle_index = len(active_state.cycles) + 1
        timestamp = utc_now()
        next_step_index = _determine_next_step(active_state)
        if next_step_index is None:
            record = CycleRecord(
                cycle_index=cycle_index,
                step_name="complete",
                status="idle",
                notes="Plan already complete; nothing to execute.",
                timestamp=timestamp,
            )
        else:
            step = active_state.plan.steps[next_step_index]
            if blocked and not dry_run:
                record = CycleRecord(
                    cycle_index=cycle_index,
                    step_name=step.name,
                    status="blocked",
                    notes="Approval gate active; set AKIT_APPROVED to continue.",
                    timestamp=timestamp,
                )
            elif blocked and dry_run:
                record = CycleRecord(
                    cycle_index=cycle_index,
                    step_name=step.name,
                    status="preview",
                    notes="Approval gate active; dry-run only.",
                    timestamp=timestamp,
                )
            else:
                record = CycleRecord(
                    cycle_index=cycle_index,
                    step_name=step.name,
                    status="completed" if next_step_index not in active_state.completed_steps else "repeat",
                    notes="Step marked as complete for this cycle.",
                    timestamp=timestamp,
                )
                if next_step_index not in active_state.completed_steps:
                    active_state.completed_steps.append(next_step_index)
        active_state.cycles.append(record)
        active_state.last_cycle_at = record.timestamp
        if not dry_run:
            cycle_path = _cycle_path(record.cycle_index)
            record_cycle(cycle_path, record.to_dict())
            artifacts.append(str(cycle_path.relative_to(config.REPO_ROOT)))
        else:
            artifacts.append(f"dry-run:{record.step_name}:{record.status}")
    if blocked and not dry_run:
        raise PermissionError("CODEOWNERS approval required. Set AKIT_APPROVED=1 to proceed.")

    report = _build_report(active_state, blocked=blocked)
    if not dry_run:
        save_state(active_state)
        save_report(report.to_dict())
        prune_cycles(cfg.artifact_limit)
    return RunResult(state=active_state, report=report, artifacts=artifacts)


def report() -> AKitReport:
    """Return the most recent execution report."""

    data = load_report()
    if not data:
        raise FileNotFoundError("no report available")
    return AKitReport(
        plan_id=str(data.get("plan_id", "")),
        generated_at=str(data.get("generated_at", "")),
        progress=float(data.get("progress", 0.0)),
        completed=[str(item) for item in data.get("completed", [])],
        pending=[str(item) for item in data.get("pending", [])],
        requires_codeowners=bool(data.get("requires_codeowners", False)),
        next_step=(str(data["next_step"]) if data.get("next_step") is not None else None),
        risks=[str(item) for item in data.get("risks", [])],
    )


def snapshot(*, state: Optional[RunState] = None) -> Tuple[Path, Path]:
    """Persist a deterministic snapshot of the Assistant Kit state."""

    if state is None:
        state = load_state()
    report_data = _build_report(state, blocked=False).to_dict()
    manifest = {
        "version": "akit.snapshot.v1",
        "plan": state.plan.to_dict(),
        "state": state.to_dict(),
        "report": report_data,
        "generated_at": state.last_cycle_at or state.plan.created_at,
    }
    serialised = json.dumps(manifest, sort_keys=True)
    digest = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
    label = f"snapshot-{state.plan.plan_id}-{digest[:12]}.json"
    attest_label = f"snapshot-{state.plan.plan_id}-{digest[:12]}.attest.json"
    manifest_file = manifest_path(label)
    attestation_file = manifest_path(attest_label)
    ensure_paths_allowed([manifest_file, attestation_file])
    manifest_file.write_text(serialised + "\n", encoding="utf-8")
    attestation = {
        "type": "akit.snapshot.digest",
        "sha256": digest,
        "plan_id": state.plan.plan_id,
        "generated_at": manifest["generated_at"],
    }
    attestation_file.write_text(json.dumps(attestation, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest_file, attestation_file
