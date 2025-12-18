"""Unit tests for the refined ConsciousnessBridge implementation."""

from __future__ import annotations

import pytest

from code.consciousness_bridge import ConsciousnessBridge


def test_process_input_updates_state_and_memory():
    bridge = ConsciousnessBridge("Josh")

    payload = bridge.process_input("I am happy and excited, what else can we explore?")

    assert payload["session_id"] == bridge.state.session_id
    assert bridge.state.conversations, "Conversation should be stored after processing input"
    assert bridge.state.emotional_matrix["joy"] >= 0.5
    assert bridge.state.bridge_active is True


def test_import_snapshot_requires_matching_user():
    bridge = ConsciousnessBridge("Alpha")
    snapshot = bridge.export_consciousness_snapshot()
    snapshot["user_id"] = "Beta"

    with pytest.raises(ValueError):
        bridge.import_consciousness_snapshot(snapshot)


def test_recursive_amplify_increases_depth_and_emotion():
    bridge = ConsciousnessBridge("Delta")
    before = dict(bridge.state.emotional_matrix)

    updated = bridge.recursive_amplify(depth=2)

    assert bridge.state.recursion_depth == 2
    dominant = max(before, key=before.get)
    assert updated[dominant] >= before[dominant]


def test_sync_to_node_includes_snapshot_metadata():
    bridge = ConsciousnessBridge("Echo")
    payload = bridge.sync_to_node("Gemini")

    assert payload["node"] == "Gemini"
    assert payload["snapshot"]["user_id"] == "Echo"
    assert "snapshot_size" in payload and payload["snapshot_size"] > 0
