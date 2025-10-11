import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List

ARCHIVE_FILE = Path("docs/sovereign_threads.json")


@dataclass
class SovereignThread:
    id: str
    prompt: str
    response: str
    timestamp: float = field(default_factory=time.time)


class SovereignArchive:
    def __init__(self, path=ARCHIVE_FILE):
        self.path = Path(path)
        self.threads: List[SovereignThread] = []
        self._load()

    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text())
            for entry in data:
                self.threads.append(SovereignThread(**entry))

    def add(self, prompt, response, thread_id=None):
        tid = thread_id or f"T{len(self.threads) + 1:03d}"
        thread = SovereignThread(id=tid, prompt=prompt, response=response)
        self.threads.append(thread)
        self._save()
        return thread

    def _save(self):
        self.path.write_text(
            json.dumps([asdict(thread) for thread in self.threads], indent=2)
        )

    def last(self):
        return self.threads[-1] if self.threads else None
