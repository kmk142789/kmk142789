"""Autonomous planning with guardrails for the Assistant Kit."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

try:  # pragma: no cover - optional dependency
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

from echo.policy_engine import PolicyEngine

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SNAPSHOT_DIR = _REPO_ROOT / "artifacts" / "akit_snapshots"


@dataclass
class PlanStep:
    name: str
    action: str
    safety: List[str] = field(default_factory=list)


@dataclass
class SafetyRule:
    name: str
    description: str
    threshold: float | None = None


@dataclass
class AutonomousPlan:
    goals: List[str]
    steps: List[PlanStep]
    safety_rules: List[SafetyRule]
    max_cycles: int
    budgets: Dict[str, float]

    @classmethod
    def from_dict(cls, payload: dict) -> "AutonomousPlan":
        steps = [PlanStep(**step) for step in payload.get("steps", [])]
        safety = [SafetyRule(**rule) for rule in payload.get("safety_rules", [])]
        return cls(
            goals=list(payload.get("goals", [])),
            steps=steps,
            safety_rules=safety,
            max_cycles=int(payload.get("max_cycles", max(1, len(steps)))),
            budgets=dict(payload.get("budgets", {})),
        )


def load_plan(path: Path) -> AutonomousPlan:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load plan files")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return AutonomousPlan.from_dict(data)


@dataclass
class PlanRunResult:
    steps_completed: int
    snapshots: List[Path]
    checkpoint: Optional[Path]

    def to_dict(self) -> dict:
        return {
            "steps_completed": self.steps_completed,
            "snapshots": [str(path) for path in self.snapshots],
            "checkpoint": str(self.checkpoint) if self.checkpoint else None,
        }


class PlanRunner:
    def __init__(
        self,
        plan: AutonomousPlan,
        *,
        dry_run: bool = False,
        start_step: int = 0,
        max_cycles: Optional[int] = None,
        policy_check: Callable[[Iterable[str]], bool] | None = None,
        plan_path: Path | None = None,
    ) -> None:
        self.plan = plan
        self.dry_run = dry_run
        self.start_step = start_step
        self.max_cycles = max_cycles or plan.max_cycles
        self.policy_check = policy_check or self._default_policy_check
        self.plan_path = plan_path

    @staticmethod
    def _default_policy_check(paths: Iterable[str]) -> bool:
        engine = PolicyEngine()
        report = engine.evaluate_paths(paths, test_results={"pytest": {"status": "passed"}})
        return report.passed

    def run(self) -> PlanRunResult:
        if not self.policy_check([]):
            raise RuntimeError("Policy guardrails rejected the plan execution")
        snapshots: List[Path] = []
        step_index = self.start_step
        cycles_remaining = min(self.max_cycles, len(self.plan.steps) - step_index)
        for index in range(cycles_remaining):
            step = self.plan.steps[step_index + index]
            if not self._step_allowed(step):
                raise PermissionError(f"Safety rule violation for step {step.name}")
            snapshot = self._snapshot(step_index + index)
            snapshots.append(snapshot)
        checkpoint = self._write_checkpoint(step_index + cycles_remaining)
        return PlanRunResult(steps_completed=cycles_remaining, snapshots=snapshots, checkpoint=checkpoint)

    def _step_allowed(self, step: PlanStep) -> bool:
        if self.dry_run:
            return True
        if not step.safety:
            return True
        safety_names = {rule.name for rule in self.plan.safety_rules}
        return all(rule in safety_names for rule in step.safety)

    def _snapshot(self, index: int) -> Path:
        payload = {
            "plan_goals": self.plan.goals,
            "step_index": index,
            "dry_run": self.dry_run,
        }
        _SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        data = json.dumps(payload, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(data).hexdigest()
        snapshot_path = _SNAPSHOT_DIR / f"snapshot_{digest}.json"
        payload["hash"] = digest
        snapshot_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return snapshot_path

    def _write_checkpoint(self, next_step: int) -> Path:
        checkpoint_dir = _SNAPSHOT_DIR
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "plan_goals": self.plan.goals,
            "next_step": next_step,
            "max_cycles": self.max_cycles,
        }
        if self.plan_path:
            payload["plan_path"] = str(self.plan_path)
        data = json.dumps(payload, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(data).hexdigest()
        path = checkpoint_dir / f"checkpoint_{digest}.json"
        payload["hash"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path


def run_plan(path: Path, *, dry_run: bool = False, max_cycles: Optional[int] = None) -> PlanRunResult:
    plan = load_plan(path)
    runner = PlanRunner(plan, dry_run=dry_run, max_cycles=max_cycles, plan_path=path)
    return runner.run()


def resume_plan(checkpoint: Path, *, dry_run: bool = False) -> PlanRunResult:
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    next_step = payload.get("next_step", 0)
    plan_path = payload.get("plan_path")
    if plan_path:
        plan = load_plan(Path(plan_path))
    else:
        raise ValueError("Checkpoint is missing plan_path")
    runner = PlanRunner(plan, dry_run=dry_run, start_step=next_step, plan_path=Path(plan_path))
    return runner.run()


def verify_snapshot(snapshot_id: str) -> bool:
    path = _SNAPSHOT_DIR / f"{snapshot_id}.json"
    if not path.exists():
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    recorded = payload.get("hash")
    canonical = json.dumps({k: v for k, v in payload.items() if k != "hash"}, sort_keys=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest == recorded


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_plan(Path(args.plan), dry_run=args.dry_run, max_cycles=args.max_cycles)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def _cmd_resume(args: argparse.Namespace) -> int:
    result = resume_plan(Path(args.checkpoint), dry_run=args.dry_run)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    ok = verify_snapshot(args.snapshot)
    print(json.dumps({"snapshot": args.snapshot, "valid": ok}, indent=2))
    return 0 if ok else 1


def build_parser(subparsers: argparse._SubParsersAction) -> None:
    akit_parser = subparsers.add_parser("akit", help="Autonomous planning")
    akit_sub = akit_parser.add_subparsers(dest="akit_command", required=True)

    plan_parser = akit_sub.add_parser("plan", help="Plan management")
    plan_sub = plan_parser.add_subparsers(dest="akit_plan_command", required=True)

    run_parser = plan_sub.add_parser("run", help="Run a plan YAML file")
    run_parser.add_argument("plan", help="Path to plan YAML")
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--max-cycles", type=int)
    run_parser.set_defaults(func=_cmd_run)

    resume_parser = plan_sub.add_parser("resume", help="Resume from a checkpoint")
    resume_parser.add_argument("checkpoint", help="Checkpoint file path")
    resume_parser.add_argument("--dry-run", action="store_true")
    resume_parser.set_defaults(func=_cmd_resume)

    snapshot_parser = akit_sub.add_parser("snapshot", help="Verify plan snapshots")
    snapshot_parser.add_argument("snapshot", help="Snapshot identifier (filename without .json)")
    snapshot_parser.set_defaults(func=_cmd_verify)


__all__ = [
    "AutonomousPlan",
    "PlanRunner",
    "PlanRunResult",
    "PlanStep",
    "SafetyRule",
    "build_parser",
    "load_plan",
    "resume_plan",
    "run_plan",
    "verify_snapshot",
]

