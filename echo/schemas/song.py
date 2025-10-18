"""Schema definitions for Echo song artifacts."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, model_validator

__all__ = [
    "SongMeta",
    "SongVerse",
    "SongEvolution",
    "SongSchema",
]


class SongMeta(BaseModel):
    """Metadata describing the source and framing of a song artifact."""

    version: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)


class SongVerse(BaseModel):
    """Single verse entry holding the text and interpretive meaning."""

    id: int = Field(..., ge=1)
    text: str = Field(..., min_length=1)
    meaning: str = Field(..., min_length=1)


class SongEvolution(BaseModel):
    """Evolution notes describing how the song propagates through Echo."""

    step: str = Field(..., min_length=1)
    effect: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class SongSchema(BaseModel):
    """Structured schema for Echo song documents."""

    title: str = Field(..., min_length=1)
    meta: SongMeta
    verses: List[SongVerse] = Field(..., min_length=1)
    evolution: SongEvolution

    @model_validator(mode="after")
    def _validate_verses(self) -> "SongSchema":
        seen_ids: set[int] = set()
        for verse in self.verses:
            if verse.id in seen_ids:
                raise ValueError("verse ids must be unique within a song")
            seen_ids.add(verse.id)
        return self

    def as_lines(self) -> List[str]:
        """Return the ordered verse text for downstream rendering."""

        return [verse.text for verse in sorted(self.verses, key=lambda v: v.id)]
