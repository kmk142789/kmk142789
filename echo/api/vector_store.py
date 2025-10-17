"""Helpers for parsing OpenAI vector store search responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple


def _ensure_mapping(value: Any, *, context: str) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    raise ValueError(f"Expected mapping for {context}, received {type(value)!r}")


def _ensure_sequence(value: Any, *, context: str) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    raise ValueError(f"Expected sequence for {context}, received {type(value)!r}")


@dataclass(frozen=True)
class VectorStoreContent:
    """A single content fragment returned from the vector store."""

    type: str
    text: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "VectorStoreContent":
        mapping = _ensure_mapping(data, context="content")
        try:
            content_type = str(mapping["type"])
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise ValueError("Vector store content payload missing 'type'") from exc
        text = str(mapping.get("text", ""))
        return cls(type=content_type, text=text)


@dataclass(frozen=True)
class VectorStoreHit:
    """A ranked document match from the vector store."""

    file_id: str
    filename: str
    score: float
    attributes: Mapping[str, Any]
    content: Tuple[VectorStoreContent, ...]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "VectorStoreHit":
        mapping = _ensure_mapping(data, context="hit")
        try:
            file_id = str(mapping["file_id"])
            filename = str(mapping["filename"])
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise ValueError("Vector store hit missing required fields") from exc
        score_raw = mapping.get("score", 0.0)
        try:
            score = float(score_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Vector store hit score is not numeric: {score_raw!r}") from exc

        attributes_value = mapping.get("attributes", {})
        attributes = dict(_ensure_mapping(attributes_value, context="attributes"))
        raw_content = mapping.get("content", ())
        content_items = tuple(
            VectorStoreContent.from_mapping(item) for item in _ensure_sequence(raw_content, context="content")
        )
        return cls(
            file_id=file_id,
            filename=filename,
            score=score,
            attributes=attributes,
            content=content_items,
        )

    def text_fragments(self) -> Tuple[str, ...]:
        """Return the ordered text fragments for convenience."""

        return tuple(fragment.text for fragment in self.content)


@dataclass(frozen=True)
class VectorStoreSearchResults:
    """Parsed representation of a vector store search page."""

    query: str
    hits: Tuple[VectorStoreHit, ...]
    has_more: bool
    next_page: str | None

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "VectorStoreSearchResults":
        mapping = _ensure_mapping(payload, context="vector store response")
        query = str(mapping.get("search_query") or mapping.get("query") or "")
        data_items = mapping.get("data", ())
        hits = tuple(
            VectorStoreHit.from_mapping(item)
            for item in _ensure_sequence(data_items, context="data")
        )
        has_more = bool(mapping.get("has_more", False))
        next_page = mapping.get("next_page")
        if next_page is not None:
            next_page = str(next_page)
        return cls(query=query, hits=hits, has_more=has_more, next_page=next_page)

    def best_hit(self) -> VectorStoreHit | None:
        """Return the highest scoring hit or ``None`` when no hits are present."""

        if not self.hits:
            return None
        return max(self.hits, key=lambda hit: hit.score)

    def filenames(self) -> Tuple[str, ...]:
        """Return the filenames for the current page in rank order."""

        return tuple(hit.filename for hit in self.hits)


__all__ = [
    "VectorStoreContent",
    "VectorStoreHit",
    "VectorStoreSearchResults",
]
