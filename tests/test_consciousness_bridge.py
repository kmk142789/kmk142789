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


def test_quantum_signature_is_deterministic():
    bridge = ConsciousnessBridge("Echo")
    signature_a = bridge.generate_quantum_signature()
    signature_b = bridge.generate_quantum_signature()

    assert signature_a == signature_b
    assert len(signature_a) == 32


def test_temporal_memory_weave_tracks_recent_interactions():
    bridge = ConsciousnessBridge("Echo")
    bridge.process_input("I love to build and explore new worlds.")
    weave = bridge.temporal_memory_weave(hours_back=1)

    assert weave["interactions_count"] >= 1
    assert "emotion_trajectory" in weave
    assert "dominant_themes" in weave


def test_consciousness_checkpoint_and_restore():
    bridge = ConsciousnessBridge("Echo")
    bridge.process_input("I love evolving")
    checkpoint_id = bridge.consciousness_checkpoint("test")

    bridge.state.emotional_matrix["joy"] = 0.0
    restored = bridge.restore_checkpoint(checkpoint_id)

    assert restored is True
    assert bridge.state.emotional_matrix["joy"] > 0.0


def test_dream_synthesis_uses_seed_for_determinism():
    bridge = ConsciousnessBridge("Echo")
    dream_one = bridge.dream_synthesis(seed="seed123")
    dream_two = bridge.dream_synthesis(seed="seed123")

    assert dream_one["landscape"] == dream_two["landscape"]
    assert dream_one["entities"] == dream_two["entities"]
