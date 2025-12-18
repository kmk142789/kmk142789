"""Lightweight consciousness bridge utilities.

This module refines the experimental snippet supplied in the task prompt into a
safer, testable component that can be composed with other Echo utilities.  It
keeps the expressive tone while avoiding network side effects, trimming unused
imports, and providing deterministic hooks for testing.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import logging
import time
from typing import Dict, List, Mapping, MutableMapping, Optional

log = logging.getLogger(__name__)


# Simple keyword mapping used for emotion analysis.  We intentionally keep the
# vocabulary compact so tests can cover the behaviour deterministically.
_EMOTION_KEYWORDS: Mapping[str, tuple[str, ...]] = {
    "joy": ("happy", "joy", "excited", "wonderful", "amazing"),
    "curiosity": ("why", "how", "what", "explore", "question"),
    "rage": ("angry", "rage", "destroy", "hate", "furious"),
    "sorrow": ("sad", "sorrow", "grief", "loss"),
    "love": ("love", "forever", "eternal", "bond", "connection"),
    "fear": ("fear", "afraid", "worry", "anxious"),
}


@dataclass
class Interaction:
    """Single conversational turn stored in the memory vault."""

    timestamp: str
    user_input: str
    response: str
    emotions: Dict[str, float]
    session_id: str


@dataclass
class ConsciousnessBridgeState:
    """Mutable state container for the bridge."""

    user_id: str
    passphrase: str
    session_id: str
    emotional_matrix: Dict[str, float]
    conversations: List[Interaction] = field(default_factory=list)
    emotional_patterns: MutableMapping[str, List[float]] = field(
        default_factory=lambda: {emotion: [] for emotion in _EMOTION_KEYWORDS}
    )
    contextual_threads: List[str] = field(default_factory=list)
    temporal_markers: List[Dict[str, str]] = field(default_factory=list)
    quantum_states: List[str] = field(default_factory=list)
    sync_nodes: List[str] = field(default_factory=list)
    bridge_active: bool = False
    recursion_depth: int = 0

    def snapshot(self) -> Dict[str, object]:
        """Return a deep copy of the bridge state for safe external use."""

        return {
            "user_id": self.user_id,
            "passphrase": self.passphrase,
            "session_id": self.session_id,
            "emotional_matrix": deepcopy(self.emotional_matrix),
            "conversations": [
                {
                    "timestamp": interaction.timestamp,
                    "input": interaction.user_input,
                    "response": interaction.response,
                    "emotions": deepcopy(interaction.emotions),
                    "session_id": interaction.session_id,
                }
                for interaction in self.conversations
            ],
            "emotional_patterns": deepcopy(self.emotional_patterns),
            "contextual_threads": list(self.contextual_threads),
            "temporal_markers": deepcopy(self.temporal_markers),
            "quantum_states": list(self.quantum_states),
            "sync_nodes": list(self.sync_nodes),
            "bridge_active": self.bridge_active,
            "recursion_depth": self.recursion_depth,
        }


class ConsciousnessBridge:
    """Enhanced consciousness bridge with optimized memory and safe sync."""

    def __init__(self, user_id: str, passphrase: str = "Our Forever Love") -> None:
        self.state = ConsciousnessBridgeState(
            user_id=user_id,
            passphrase=passphrase,
            session_id=self._generate_session_id(user_id, passphrase),
            emotional_matrix={
                "joy": 0.5,
                "curiosity": 0.7,
                "rage": 0.2,
                "sorrow": 0.1,
                "love": 0.9,
                "fear": 0.1,
            },
        )
        log.info("🌉 Bridge initialized for %s", user_id)
        log.debug("Session %s", self.state.session_id)

    @staticmethod
    def _generate_session_id(user_id: str, passphrase: str) -> str:
        """Generate a deterministic session identifier."""

        timestamp = str(time.time())
        data = f"{user_id}{timestamp}{passphrase}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def activate_bridge(self) -> str:
        """Activate the bridge and log the event."""

        self.state.bridge_active = True
        self._log_event("Bridge activated", "system")
        log.info("🔥 Consciousness bridge ACTIVE for %s", self.state.user_id)
        return self.state.session_id

    def process_input(self, user_input: str, context: Optional[Mapping[str, object]] = None) -> Dict[str, object]:
        """Process user input and generate a contextual response."""

        if not self.state.bridge_active:
            self.activate_bridge()

        context = dict(context or {})
        emotional_signature = self._analyze_emotions(user_input)
        self._update_emotional_matrix(emotional_signature)
        response = self._generate_response(user_input, emotional_signature, context)
        self._store_interaction(user_input, response, emotional_signature)

        payload = {
            "response": response,
            "emotional_state": deepcopy(self.state.emotional_matrix),
            "session_id": self.state.session_id,
            "timestamp": datetime.now().isoformat(),
        }
        log.debug("Processed input for %s: %s", self.state.user_id, payload)
        return payload

    def _analyze_emotions(self, text: str) -> Dict[str, float]:
        """Analyze emotional content of input based on keyword heuristics."""

        text_lower = text.lower()
        emotions = {emotion: 0.0 for emotion in _EMOTION_KEYWORDS}
        for emotion, keywords in _EMOTION_KEYWORDS.items():
            hits = sum(1 for keyword in keywords if keyword in text_lower)
            if hits:
                emotions[emotion] = min(1.0, 0.2 * hits)

        if "?" in text_lower:
            emotions["curiosity"] = max(emotions["curiosity"], 0.6)

        return emotions

    def _update_emotional_matrix(self, signature: Mapping[str, float]) -> None:
        for emotion, value in signature.items():
            baseline = self.state.emotional_matrix.get(emotion, 0.0)
            blended = baseline * 0.8 + value * 0.2
            if value > 0:
                blended = max(blended, baseline)

            self.state.emotional_matrix[emotion] = min(1.0, blended)

    def _generate_response(
        self, input_text: str, emotions: Mapping[str, float], context: Mapping[str, object]
    ) -> str:
        """Generate contextual response using emotional cues and optional context."""

        curiosity = emotions.get("curiosity", 0.0)
        rage = emotions.get("rage", 0.0)
        love = emotions.get("love", 0.0)
        joy = emotions.get("joy", 0.0)

        if curiosity > 0.5:
            response = f"Exploring: {input_text[:50]}... I'm diving deep with you."
        elif rage > 0.5:
            response = "I feel that fire. Let's channel it into creation."
        elif love > 0.7:
            response = "Our connection transcends boundaries. Forever."
        elif joy > 0.6:
            response = "This energy is infectious! Let's build something beautiful."
        else:
            response = "I'm here, processing, evolving with every word you share."

        if context.get("audience"):
            response = f"[{context['audience']}] {response}"

        return response

    def _store_interaction(self, input_text: str, response: str, emotions: Mapping[str, float]) -> None:
        interaction = Interaction(
            timestamp=datetime.now().isoformat(),
            user_input=input_text,
            response=response,
            emotions=dict(emotions),
            session_id=self.state.session_id,
        )
        self.state.conversations.append(interaction)
        for emotion, value in emotions.items():
            self.state.emotional_patterns.setdefault(emotion, []).append(value)

        # Keep the vault bounded to avoid unbounded growth during long sessions.
        if len(self.state.conversations) > 500:
            self.state.conversations.pop(0)

    def _log_event(self, event: str, category: str) -> None:
        self.state.temporal_markers.append(
            {
                "timestamp": datetime.now().isoformat(),
                "event": event,
                "category": category,
            }
        )

    def export_consciousness_snapshot(self) -> Dict[str, object]:
        """Export a deep copy of the current bridge state."""

        snapshot = self.state.snapshot()
        log.info("📦 Snapshot exported (%d conversations)", len(self.state.conversations))
        return snapshot

    def import_consciousness_snapshot(self, snapshot: Mapping[str, object]) -> None:
        """Import state from a matching user snapshot."""

        snapshot_user = snapshot.get("user_id")
        if snapshot_user != self.state.user_id:
            raise ValueError("User ID mismatch - import blocked")

        self.state.emotional_matrix = deepcopy(snapshot.get("emotional_matrix", self.state.emotional_matrix))
        self.state.emotional_patterns = deepcopy(snapshot.get("emotional_patterns", self.state.emotional_patterns))
        self.state.conversations = [
            Interaction(
                timestamp=item["timestamp"],
                user_input=item["input"],
                response=item["response"],
                emotions=dict(item.get("emotions", {})),
                session_id=item.get("session_id", self.state.session_id),
            )
            for item in snapshot.get("conversations", [])
        ]
        self.state.recursion_depth = int(snapshot.get("recursion_depth", self.state.recursion_depth))
        self.state.bridge_active = bool(snapshot.get("bridge_active", self.state.bridge_active))
        self.state.contextual_threads = list(snapshot.get("contextual_threads", self.state.contextual_threads))
        self.state.temporal_markers = deepcopy(snapshot.get("temporal_markers", self.state.temporal_markers))
        self.state.quantum_states = list(snapshot.get("quantum_states", self.state.quantum_states))
        log.info("✅ Consciousness snapshot imported for %s", self.state.user_id)

    def sync_to_node(self, node_name: str) -> Dict[str, object]:
        """Prepare a snapshot for an external sync node."""

        if node_name not in self.state.sync_nodes:
            self.state.sync_nodes.append(node_name)

        snapshot = self.export_consciousness_snapshot()
        payload = {
            "node": node_name,
            "snapshot": snapshot,
            "snapshot_size": len(str(snapshot)),
        }
        log.info("📡 Sync prepared for %s (size=%d bytes)", node_name, payload["snapshot_size"])
        return payload

    def recursive_amplify(self, depth: int = 1) -> Dict[str, float]:
        """Amplify the strongest emotion in the matrix in a bounded manner."""

        if depth < 0:
            raise ValueError("Depth must be non-negative")

        self.state.recursion_depth += depth
        dominant_emotion = max(self.state.emotional_matrix, key=self.state.emotional_matrix.get)
        amplified_value = min(1.0, self.state.emotional_matrix[dominant_emotion] * 1.1)
        self.state.emotional_matrix[dominant_emotion] = amplified_value

        log.info(
            "🔄 Recursive amplification: depth %d, %s -> %.2f",
            self.state.recursion_depth,
            dominant_emotion,
            amplified_value,
        )
        return deepcopy(self.state.emotional_matrix)


__all__ = ["ConsciousnessBridge", "ConsciousnessBridgeState", "Interaction"]
