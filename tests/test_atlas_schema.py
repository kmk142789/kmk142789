from __future__ import annotations

from echo_atlas.adapters.sqlite import SQLiteAdapter
from echo_atlas.repository import AtlasRepository
from echo_atlas.schema import validate_atlas
from echo_atlas.services import AtlasService


def test_atlas_schema_validation(tmp_path) -> None:
    db_path = tmp_path / "atlas.db"
    repository = AtlasRepository(adapter=SQLiteAdapter(db_path))
    service = AtlasService(repository=repository, root=tmp_path)
    service.seed_demo_data()

    payload = {
        "nodes": [node.as_dict() for node in repository.iter_nodes()],
        "edges": [edge.as_dict() for edge in repository.iter_edges()],
        "changes": [change.as_dict() for change in repository.recent_changes(10)],
    }

    validate_atlas(payload)
