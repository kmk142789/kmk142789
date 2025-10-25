from __future__ import annotations

import json
from pathlib import Path

import pytest

from dominion.executor import PlanExecutor
from dominion.plans import ActionIntent, DominionPlan
from dominion.policy import PolicyViolation


def build_plan(tmp_path: Path, intents: list[ActionIntent]) -> DominionPlan:
    plan = DominionPlan.from_intents(intents, source=str(tmp_path / "singularity_log.json"))
    return plan


def test_plan_idempotency(tmp_path: Path) -> None:
    executor = PlanExecutor(root=tmp_path, workdir=tmp_path / "build" / "dominion")
    intent = ActionIntent(
        intent_id="write-1",
        action_type="file.write",
        target="output.txt",
        payload={"content": "hello"},
        metadata={},
    )
    plan = build_plan(tmp_path, [intent])

    receipt = executor.apply(plan)
    assert receipt.summary["applied"] == 1

    with pytest.raises(PolicyViolation):
        executor.apply(plan)


def test_rollback_restores_previous_state(tmp_path: Path) -> None:
    existing = tmp_path / "existing.txt"
    existing.write_text("seed", encoding="utf-8")

    executor = PlanExecutor(root=tmp_path, workdir=tmp_path / "build" / "dominion")
    intents = [
        ActionIntent(
            intent_id="first",
            action_type="file.write",
            target=str(existing.relative_to(tmp_path)),
            payload={"content": "updated"},
            metadata={},
        ),
        ActionIntent(
            intent_id="second",
            action_type="unsupported.action",
            target="",
            payload={},
            metadata={},
        ),
    ]
    plan = build_plan(tmp_path, intents)

    with pytest.raises(PolicyViolation):
        executor.apply(plan)

    assert existing.read_text(encoding="utf-8") == "seed"


def test_allowlist_prevents_unknown_actions(tmp_path: Path) -> None:
    executor = PlanExecutor(root=tmp_path, workdir=tmp_path / "build" / "dominion")
    plan = build_plan(
        tmp_path,
        [
            ActionIntent(
                intent_id="unknown",
                action_type="not.allowed",
                target="",
                payload={},
                metadata={},
            )
        ],
    )

    with pytest.raises(PolicyViolation):
        executor.apply(plan)


def test_dry_run_does_not_modify_files(tmp_path: Path) -> None:
    executor = PlanExecutor(root=tmp_path, workdir=tmp_path / "build" / "dominion")
    target = tmp_path / "artifact.txt"
    plan = build_plan(
        tmp_path,
        [
            ActionIntent(
                intent_id="dry",
                action_type="file.write",
                target=str(target.relative_to(tmp_path)),
                payload={"content": "data"},
                metadata={},
            )
        ],
    )

    receipt = executor.apply(plan, dry_run=True)
    assert receipt.status == "dry-run"
    assert not target.exists()
