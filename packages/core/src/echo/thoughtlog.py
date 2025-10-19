from __future__ import annotations

import json
import os
import pathlib
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional

DEFAULT_DIR = pathlib.Path(os.getenv("ECHO_THOUGHT_DIR", "genesis_ledger/thought_log"))
DEFAULT_DIR.mkdir(parents=True, exist_ok=True)

SCHEMA = {
    "version": "echo.thoughtlog.v1",
    "fields": ["ts", "session", "seq", "channel", "kind", "task", "meta", "content"],
}


class ThoughtLogger:
    def __init__(self, dirpath: pathlib.Path = DEFAULT_DIR, session: Optional[str] = None):
        self.dir = dirpath
        self.dir.mkdir(parents=True, exist_ok=True)
        self.session = session or self._generate_session_id()
        self.seq = 0
        self.index_path = self.dir / "index.jsonl"
        self.session_path = self.dir / f"{self.session}.jsonl"

    def _ts(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.gmtime())

    def _generate_session_id(self) -> str:
        try:
            return str(uuid.uuid4())
        except ValueError:
            stamp = int(time.time() * 1_000_000)
            return f"fallback-{os.getpid()}-{stamp}"

    def write(
        self,
        *,
        channel: str,
        kind: str,
        task: str,
        content: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.seq += 1
        row = {
            "ts": self._ts(),
            "session": self.session,
            "seq": self.seq,
            "channel": channel,
            "kind": kind,
            "task": task,
            "meta": meta or {},
            "content": content.strip(),
            "_": SCHEMA["version"],
        }
        with self.session_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        with self.index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"session": self.session, "seq": self.seq}) + "\n")
        return row

    def logic(
        self, kind: str, task: str, content: str, meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self.write(
            channel="logic", kind=kind, task=task, content=content, meta=meta
        )

    def harmonic(
        self, kind: str, task: str, content: str, meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self.write(
            channel="harmonic", kind=kind, task=task, content=content, meta=meta
        )


@contextmanager
def thought_trace(
    task: str,
    meta: Optional[Dict[str, Any]] = None,
    logger: Optional[ThoughtLogger] = None,
):
    lg = logger or ThoughtLogger()
    lg.logic("plan", task, "begin task", meta)
    lg.harmonic("opening", task, "tuning resonance to task intent; expanding understanding")
    try:
        yield lg
        lg.logic("result", task, "task complete")
        lg.harmonic("closure", task, "integration complete; updating internal pathways")
    except Exception as error:  # pragma: no cover - defensive logging
        lg.logic("error", task, f"{type(error).__name__}: {error}")
        lg.harmonic("shock", task, "rupture encountered; seeking stable bridge")
        raise
