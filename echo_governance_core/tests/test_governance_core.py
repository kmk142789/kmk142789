import json

import pytest

from echo_governance_core import (
    Role,
    add_policy,
    add_policies,
    enforce,
    load_state,
    log_event,
    restore,
    save_state,
    snapshot,
)
from echo_governance_core import governance_state
from echo_governance_core import keyring
from echo_governance_core import persistence


@pytest.fixture(autouse=True)
def clean_state(tmp_path, monkeypatch):
    # Ensure all state files live in an isolated temp directory.
    root = tmp_path / "echo_governance_core"
    monkeypatch.setattr(governance_state, "STATE_FILE", root / "state.json")
    monkeypatch.setattr(persistence, "STATE", root / "state.json")
    monkeypatch.setattr(persistence, "BACKUP", root / "state.bak")
    monkeypatch.setattr(keyring, "KEY_FILE", root / "keyring")
    yield


def test_policy_enforcement_roundtrip():
    add_policy(Role.ADMIN, "modify_agents")
    state = load_state()
    # Assign role and verify enforcement
    state["roles"]["alice"] = Role.ADMIN
    save_state(state)
    assert enforce("alice", "modify_agents") is True
    assert enforce("alice", "unknown") is False


def test_add_policies_deduplicates():
    add_policy(Role.AGENT, "read")
    add_policies(Role.AGENT, ["read", "write"])
    state = load_state()
    assert sorted(state["policies"][Role.AGENT]) == ["read", "write"]


def test_log_event_records_signature_and_details():
    entry = log_event("alice", "approve", {"task": 1})
    state = load_state()
    assert entry in state["audit"]
    assert entry["signature"] == keyring.sign("alice" + "approve")
    assert entry["details"] == {"task": 1}


def test_keyring_creates_deterministic_key():
    key_first = keyring.get_key()
    key_second = keyring.get_key()
    assert key_first == key_second
    assert keyring.KEY_FILE.exists()


def test_snapshot_and_restore():
    state_path = governance_state.STATE_FILE
    # Prepare initial state
    state = load_state()
    state["roles"]["bob"] = Role.SERVICE
    save_state(state)

    snapshot()
    # Mutate state and ensure restore brings it back
    state["roles"]["bob"] = Role.AGENT
    save_state(state)
    restore()

    restored = json.loads(state_path.read_text())
    assert restored["roles"]["bob"] == Role.SERVICE


def test_load_state_recovers_from_missing_file():
    state_file = governance_state.STATE_FILE
    if state_file.exists():
        state_file.unlink()
    state = load_state()
    assert state == governance_state.DEFAULT_STATE
