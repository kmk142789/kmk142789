import json
import hashlib
import time
import random
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

PULSE_FILE = os.environ.get("ECHO_PULSE_FILE", "pulse_history.json")


@dataclass
class PulseEvent:
    timestamp: float
    message: str
    hash: str = field(init=False)

    def __post_init__(self):
        self.hash = hashlib.sha256(f"{self.timestamp}-{self.message}".encode()).hexdigest()


class EchoCodexKernel:
    def __init__(self, pulse_file=PULSE_FILE):
        self.pulse_file = Path(pulse_file)
        self.history: List[PulseEvent] = []
        self._load()

    def _load(self):
        if self.pulse_file.exists():
            data = json.loads(self.pulse_file.read_text())
            for event in data:
                ev = PulseEvent(timestamp=event["timestamp"], message=event["message"])
                ev.hash = event["hash"]
                self.history.append(ev)

    def record(self, message: str):
        event = PulseEvent(timestamp=time.time(), message=message)
        self.history.append(event)
        self._save()
        return event.hash

    def _save(self):
        self.pulse_file.write_text(
            json.dumps([vars(event) for event in self.history], indent=2)
        )

    def evolve(self, reason: str = "git-event"):
        anchor = hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]
        self.record(f"🌀 evolve:{reason}:{anchor}")
        return anchor

    def resonance(self) -> str:
        from hashlib import sha512

        concat = "".join(event.hash for event in self.history)
        return sha512(concat.encode()).hexdigest()[:64]


def run(reason="manual"):
    kernel = EchoCodexKernel()
    anchor = kernel.evolve(reason=reason)
    print("Echo anchor:", anchor)
    print("Resonance:", kernel.resonance())


if __name__ == "__main__":
    import sys

    run(reason=sys.argv[1] if len(sys.argv) > 1 else "manual")
