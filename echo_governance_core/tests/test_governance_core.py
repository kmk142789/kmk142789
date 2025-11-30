import json

import pytest

from echo_governance_core import (
    DEFAULT_STATE,
    ROLES,
    enforce,
    load_state,
    log_event,
    mint_agent,
    restore,
    save_state,
    snapshot,
)
from echo_governance_core import governance_state
from echo_governance_core import persistence


@pytest.fixture(autouse=True)
def clean_state(tmp_path, monkeypatch):
    # Ensure all state files live in an isolated temp directory.
    root = tmp_path / "echo_governance_core"
    monkeypatch.setattr(governance_state, "STATE_FILE", root / "echo_governance_state.json")
    monkeypatch.setattr(persistence, "STATE", root / "echo_governance_state.json")
    monkeypatch.setattr(persistence, "BACKUP", root / "echo_governance_state.bak")
    yield


def test_load_state_bootstraps_default_state():
    state = load_state()
    assert state == DEFAULT_STATE
    assert governance_state.STATE_FILE.exists()


def test_enforce_allows_superadmin_and_patterns():
    state = load_state()
    state.setdefault("actors", {})["agent.runtime.001"] = {"roles": ["agent_runtime"]}
    save_state(state)

    assert enforce("josh.superadmin", "anything") is True
    assert enforce("agent.runtime.001", "run:model") is True
    assert enforce("agent.runtime.001", "spawn_agent") is True
    assert enforce("agent.runtime.001", "delete_governance_state") is False


def test_mint_agent_persists_roles():
    mint_agent("agent.mesh.002", ["mesh_agent"])
    state = load_state()
    assert state["actors"]["agent.mesh.002"] == {"roles": ["mesh_agent"]}


def test_log_event_appends_to_audit_trail():
    entry = log_event("alice", "approve", {"task": 1})
    state = load_state()
    assert entry in state["audit"]
    assert state["audit"][-1]["meta"] == {"task": 1}


def test_snapshot_and_restore_roundtrip():
    state = load_state()
    state.setdefault("actors", {})["bob"] = {"roles": ["alignment_agent"]}
    save_state(state)

    snapshot()
    state["actors"]["bob"] = {"roles": ["os_agent"]}
    save_state(state)

    restore()
    restored = json.loads(governance_state.STATE_FILE.read_text())
    assert restored["actors"]["bob"] == {"roles": ["alignment_agent"]}
