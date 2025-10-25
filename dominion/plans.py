"""Planning primitives for Dominion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence
from uuid import uuid4


@dataclass
class ActionIntent:
    intent_id: str
    action_type: str
    target: str
    payload: dict
    metadata: dict

    def signature(self) -> str:
        blob = json.dumps(
            {
                "intent_id": self.intent_id,
                "action_type": self.action_type,
                "target": self.target,
                "payload": self.payload,
                "metadata": self.metadata,
            },
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()


@dataclass
class DominionPlan:
    plan_id: str
    source: str
    compiled_at: str
    intents: list[ActionIntent]
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "source": self.source,
            "compiled_at": self.compiled_at,
            "metadata": self.metadata,
            "intents": [asdict(intent) for intent in self.intents],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "DominionPlan":
        intents = [ActionIntent(**intent) for intent in payload.get("intents", [])]
        return cls(
            plan_id=str(payload["plan_id"]),
            source=str(payload.get("source", "")),
            compiled_at=str(payload.get("compiled_at", "")),
            intents=intents,
            metadata=dict(payload.get("metadata", {})),
        )

    def write(self, destination: Path | str) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return path

    @property
    def digest(self) -> str:
        sha = hashlib.sha256()
        for intent in self.intents:
            sha.update(intent.signature().encode("utf-8"))
        sha.update(self.source.encode("utf-8"))
        return sha.hexdigest()

    @classmethod
    def from_intents(cls, intents: Sequence[ActionIntent], source: str) -> "DominionPlan":
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        sorted_intents = sorted(intents, key=lambda i: i.intent_id)
        dummy = cls(plan_id="", source=source, compiled_at=timestamp, intents=list(sorted_intents))
        plan_id = dummy.digest[:16]
        dummy.plan_id = plan_id
        dummy.metadata = {"intent_count": len(intents)}
        return dummy


def intents_from_log(log_payload: Iterable[Mapping[str, object]]) -> List[ActionIntent]:
    intents: list[ActionIntent] = []
    for entry in log_payload:
        action_type = str(entry.get("type") or entry.get("action_type"))
        if not action_type:
            continue
        intent = ActionIntent(
            intent_id=str(entry.get("id") or uuid4()),
            action_type=action_type,
            target=str(entry.get("target", "")),
            payload=dict(entry.get("payload", {})),
            metadata=dict(entry.get("metadata", {})),
        )
        intents.append(intent)
    return intents


def load_log(path: Path | str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "events" in data:
        events = data["events"]
        if not isinstance(events, list):
            raise ValueError("Expected 'events' list in log file")
        return [dict(item) for item in events]
    if isinstance(data, list):
        return [dict(item) for item in data]
    raise ValueError("Unsupported log structure")

