from __future__ import annotations

from echo_atlas.adapters.sqlite import SQLiteAdapter
from echo_atlas.importers import run_importers
from echo_atlas.models import EntityType, RelationType, make_identifier
from echo_atlas.repository import AtlasRepository
from tests.atlas_utils import write_sample_files


def test_importers_populate_nodes_and_edges(tmp_path) -> None:
    write_sample_files(tmp_path)
    repository = AtlasRepository(adapter=SQLiteAdapter(tmp_path / "atlas.db"))
    results = run_importers(repository, tmp_path)

    channel_id = make_identifier(EntityType.CHANNEL, "CONTROL.md")
    bot_id = make_identifier(EntityType.BOT, "echo-attest-bot")

    assert repository.get_node(channel_id) is not None
    bot_node = repository.get_node(bot_id)
    assert bot_node is not None
    assert bot_node.entity_type is EntityType.BOT

    mentions = [
        edge for edge in repository.iter_edges() if edge.relation is RelationType.MENTIONS
    ]
    assert any(edge.source_id == channel_id for edge in mentions)
    assert sum(result.nodes for result in results) >= 4
