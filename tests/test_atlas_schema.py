from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo_atlas.domain import EntityType, Node, RelationType
from echo_atlas.schema import ValidationError, validate_graph


def test_validate_graph_accepts_valid_payload(tmp_path: Path) -> None:
    payload = {
        "generated_at": "2024-01-01T00:00:00Z",
        "nodes": [
            {"id": "node-1", "name": "Test", "entity_type": EntityType.PERSON.value},
        ],
        "edges": [
            {
                "id": "edge-1",
                "source": "node-1",
                "target": "node-1",
                "relation": RelationType.OWNS.value,
            }
        ],
        "change_log": [],
    }
    validate_graph(payload)


def test_validate_graph_rejects_invalid_payload() -> None:
    with pytest.raises(ValidationError):
        validate_graph({"nodes": []})
