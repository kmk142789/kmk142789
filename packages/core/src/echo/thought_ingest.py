from __future__ import annotations

from typing import Iterable, Optional

from .thoughtlog import ThoughtLogger


def ingest_stream(
    lines: Iterable[str],
    task: str,
    logger: Optional[ThoughtLogger] = None,
) -> ThoughtLogger:
    tl = logger or ThoughtLogger()
    for raw in lines:
        s = raw.strip()
        if s.startswith("[LOGIC]"):
            tl.logic("stream", task, s[7:].strip())
        elif s.startswith("[HARMONIC]"):
            tl.harmonic("stream", task, s[10:].strip())
        else:
            tl.logic("stream", task, s)
    return tl
