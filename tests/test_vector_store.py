"""Tests for the vector store parsing helpers."""

from __future__ import annotations

import pytest

from echo.api.vector_store import VectorStoreContent, VectorStoreSearchResults


@pytest.fixture
def sample_payload() -> dict[str, object]:
    return {
        "object": "vector_store.search_results.page",
        "search_query": "What is the return policy?",
        "data": [
            {
                "file_id": "file_123",
                "filename": "document.pdf",
                "score": 0.95,
                "attributes": {"author": "John Doe", "date": "2023-01-01"},
                "content": [{"type": "text", "text": "Relevant chunk"}],
            },
            {
                "file_id": "file_456",
                "filename": "notes.txt",
                "score": 0.89,
                "attributes": {"author": "Jane Smith", "date": "2023-01-02"},
                "content": [
                    {"type": "text", "text": "Sample text content from the vector store."}
                ],
            },
        ],
        "has_more": False,
        "next_page": None,
    }


def test_vector_store_search_results_parses_payload(sample_payload: dict[str, object]) -> None:
    results = VectorStoreSearchResults.from_json(sample_payload)

    assert results.query == "What is the return policy?"
    assert results.has_more is False
    assert results.next_page is None
    assert len(results.hits) == 2
    assert results.filenames() == ("document.pdf", "notes.txt")

    best_hit = results.best_hit()
    assert best_hit is not None
    assert best_hit.file_id == "file_123"
    assert best_hit.score == pytest.approx(0.95)
    assert best_hit.text_fragments() == ("Relevant chunk",)


def test_vector_store_hit_rejects_non_numeric_score(sample_payload: dict[str, object]) -> None:
    bad_hit = dict(sample_payload["data"][0])
    bad_hit["score"] = "not-a-number"
    bad_payload = {**sample_payload, "data": [bad_hit]}

    with pytest.raises(ValueError):
        VectorStoreSearchResults.from_json(bad_payload)


def test_vector_store_content_requires_type() -> None:
    with pytest.raises(ValueError):
        VectorStoreContent.from_mapping({"text": "missing type"})
