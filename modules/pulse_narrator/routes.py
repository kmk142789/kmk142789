"""FastAPI routes for Pulse Narrator."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query

from .narrator import PulseNarrator
from .schemas import NarrativeInputs

router = APIRouter(prefix="/pulse", tags=["pulse"])


@router.get("/narrator")
def get_narrative(
    style: str = Query("poem", pattern="^(poem|log)$"),
    seed: Optional[int] = None,
    snapshot_id: str = Query(...),
    commit_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    total_events: Optional[int] = None,
    channels: Optional[list[str]] = Query(None),
    top_prefixes: Optional[list[str]] = Query(None),
    index_count: Optional[int] = None,
    save: bool = False,
) -> dict[str, Optional[str]]:
    ts = datetime.fromisoformat(timestamp) if timestamp else None
    inputs = NarrativeInputs(
        snapshot_id=snapshot_id,
        commit_id=commit_id,
        timestamp=ts,
        total_events=total_events,
        channels=channels,
        top_prefixes=top_prefixes,
        index_count=index_count,
    )
    artifact = PulseNarrator().render(inputs, style=style, seed=seed)

    if save:
        output_dir = Path("docs/narratives")
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{inputs.snapshot_id[:8]}_{artifact.sha256[:8]}_{style}.md"
        path.write_text(artifact.body_md, encoding="utf-8")
        artifact.path = str(path)

    return {
        "style": artifact.style,
        "title": artifact.title,
        "sha256": artifact.sha256,
        "path": artifact.path,
        "body_md": artifact.body_md,
    }
