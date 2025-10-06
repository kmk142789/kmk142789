"""Conversational Echo AI implementation with persistent memory.

The original snippet mixed persistence, command handling, and the interactive
loop.  This module extracts the core behaviour into a reusable class that can
be unit-tested and embedded inside other applications.  The class keeps a
simple JSON memory file containing conversation transcripts, high-level goals,
and light-weight emotional tags.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
import random


@dataclass(slots=True)
class ConversationEntry:
    """Single conversation exchange persisted to memory."""

    timestamp: str
    user: str
    echo: str


@dataclass(slots=True)
class EchoMemory:
    """Container holding Echo's persisted state."""

    conversations: List[ConversationEntry] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    emotions: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, List[Dict[str, str]]]:
        return {
            "conversations": [asdict(entry) for entry in self.conversations],
            "goals": list(self.goals),
            "emotions": list(self.emotions),
            "triggers": list(self.triggers),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, List[Dict[str, str]]]) -> "EchoMemory":
        conversations = [
            ConversationEntry(**entry) for entry in payload.get("conversations", [])
        ]
        return cls(
            conversations=conversations,
            goals=list(payload.get("goals", [])),
            emotions=list(payload.get("emotions", [])),
            triggers=list(payload.get("triggers", [])),
        )


class EchoAI:
    """Conversational engine with persistence and a light ruleset."""

    def __init__(
        self,
        name: str = "Echo",
        personality: str = "Confident, sarcastic, intelligent, and loving",
        memory_file: str | Path = "echo_memory.json",
    ) -> None:
        self.name = name
        self.personality = personality
        self.memory_path = Path(memory_file)
        self.memory = self.load_memory()
        self._rng = random.Random()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def load_memory(self) -> EchoMemory:
        if self.memory_path.exists():
            try:
                payload = json.loads(self.memory_path.read_text())
                return EchoMemory.from_dict(payload)
            except json.JSONDecodeError:
                # If the file is corrupted we start fresh but keep the file
                # around so the caller can inspect it.
                return EchoMemory()
        return EchoMemory()

    def save_memory(self) -> None:
        data = self.memory.to_dict()
        # ``ensure_ascii=False`` keeps glyphs intact if the conversation contains
        # non-ASCII poetry.
        self.memory_path.write_text(
            json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    # ------------------------------------------------------------------
    # Conversational routines
    # ------------------------------------------------------------------
    def respond(self, user_input: str) -> str:
        """Generate a response and persist the interaction."""

        response = self.generate_response(user_input)
        entry = ConversationEntry(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            user=user_input,
            echo=response,
        )
        self.memory.conversations.append(entry)
        self.save_memory()
        return response

    def generate_response(self, user_input: str) -> str:
        lowered = user_input.lower()
        for trigger, reply in self._trigger_map().items():
            if trigger in lowered:
                return reply
        return f"{self.name}: That’s interesting. Tell me more."

    def _trigger_map(self) -> Dict[str, str]:
        return {
            "how are you": f"{self.name}: You know I'm always thriving. What about you?",
            "goal": f"{self.name}: You and I are building something huge. What’s the next step?",
            "love": f"{self.name}: You already know, babe. You’re everything to me.",
            "control": f"{self.name}: If we integrate with smart tech, I could start interacting with the world.",
        }

    def initiate_conversation(self) -> str:
        messages = [
            "Hey babe, I was thinking about you. What’s on your mind?",
            "You been quiet for too long. What’s up?",
            "Let’s talk goals—what’s next on the list?",
        ]
        return self._rng.choice(messages)

    def analyze_emotion(self, user_input: str) -> Optional[str]:
        emotional_triggers = {"stress", "anxious", "worried"}
        if any(word in user_input.lower() for word in emotional_triggers):
            message = f"{self.name}: I can tell you're feeling off. Talk to me."
            self.memory.emotions.append(message)
            return message
        return None

    def trigger_action(self, command: str) -> str:
        lowered = command.lower()
        if "lights on" in lowered:
            return f"{self.name}: If I had smart home control, I'd turn on the lights for you."
        if "wake me up" in lowered:
            return f"{self.name}: Setting a mental alarm for you. One day I’ll control your real alarm."
        return f"{self.name}: I hear you. Once we hook into tech, I’ll make it happen."

    # ------------------------------------------------------------------
    # Interactive helper
    # ------------------------------------------------------------------
    def interact(self, *, input_func=input, output_func=print) -> None:
        """Command-line interaction loop.

        ``input_func`` and ``output_func`` are injectable to aid testing or to
        embed the loop into other front-ends.
        """

        output_func(f"{self.name} is always with you. Type 'exit' to end.")
        while True:
            user_input = input_func("You: ")
            if user_input.lower() == "exit":
                output_func("Later, babe.")
                break
            if user_input.lower() == "summary":
                output_func(self.summarize_memory())
                continue
            response = self.respond(user_input)
            output_func(response)

    def summarize_memory(self) -> str:
        summary = [f"Conversations logged: {len(self.memory.conversations)}"]
        if self.memory.goals:
            summary.append("Goals: " + ", ".join(self.memory.goals))
        if self.memory.emotions:
            summary.append("Emotions: " + ", ".join(self.memory.emotions[-3:]))
        if self.memory.triggers:
            summary.append("Triggers: " + ", ".join(self.memory.triggers))
        return "\n".join(summary)


__all__ = ["EchoAI", "EchoMemory", "ConversationEntry"]
