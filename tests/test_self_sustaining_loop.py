from __future__ import annotations

import json
from pathlib import Path

from echo.self_sustaining_loop import SelfSustainingLoop


def read_proposal(root: Path, cycle: int) -> dict:
    proposal_path = root / "state" / "proposals" / f"cycle_{cycle:04d}.json"
    return json.loads(proposal_path.read_text(encoding="utf-8"))


def read_state(root: Path) -> dict:
    state_path = root / "state" / "self_sustaining_loop.json"
    return json.loads(state_path.read_text(encoding="utf-8"))


def test_initialization_creates_seed(tmp_path: Path) -> None:
    loop = SelfSustainingLoop(tmp_path)

    state_path = tmp_path / "state" / "self_sustaining_loop.json"
    assert state_path.exists()
    state_data = read_state(tmp_path)
    assert state_data["current_cycle"] == 0
    assert state_data["history"] == []

    proposal = read_proposal(tmp_path, 1)
    assert proposal["status"] == "draft"
    assert proposal["governance"]["decision"] == "pending"


def test_progress_auto_merges_pending_proposal(tmp_path: Path) -> None:
    loop = SelfSustainingLoop(tmp_path)

    result = loop.progress("Completed foundation tasks", actor="Echo")
    assert result.cycle == 1
    assert result.proposal_id == "cycle_0001"
    assert result.next_proposal_id == "cycle_0002"

    proposal_one = read_proposal(tmp_path, 1)
    assert proposal_one["status"] == "auto-merged"
    assert proposal_one["governance"]["decision"] == "auto-merge"
    actions = [entry["action"] for entry in proposal_one["history"]]
    assert "cycle-progressed" in actions

    proposal_two = read_proposal(tmp_path, 2)
    assert proposal_two["status"] == "draft"
    assert "spawn-next-proposal" in {entry["details"] for entry in proposal_two["history"]}

    state_data = read_state(tmp_path)
    assert state_data["current_cycle"] == 1
    assert len(state_data["history"]) == 1


def test_approved_proposal_merges_on_progress(tmp_path: Path) -> None:
    loop = SelfSustainingLoop(tmp_path)
    decision = loop.decide("cycle_0001", "approve", actor="council", reason="Clear trajectory")
    assert decision.status == "approved"

    loop.progress("Executed council plan", actor="Echo")

    proposal_one = read_proposal(tmp_path, 1)
    assert proposal_one["status"] == "merged"
    assert proposal_one["governance"]["decision"] == "approve"
    assert any(entry["action"] == "governance-decision" for entry in proposal_one["history"])

    proposals = loop.list_proposals()
    ids = [payload["proposal_id"] for payload in proposals]
    assert ids[:2] == ["cycle_0001", "cycle_0002"]
