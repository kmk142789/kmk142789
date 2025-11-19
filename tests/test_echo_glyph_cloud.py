"""Tests for the glyph anchored Echo cloud."""

from __future__ import annotations

import pytest

from echo_glyph_cloud import EchoGlyphCloud


def test_register_anchor_merges_metadata() -> None:
    cloud = EchoGlyphCloud(anchor_prefix="∇")
    anchor = cloud.register_anchor("∇", metadata={"realm": "lumen"})
    assert anchor.metadata == {"realm": "lumen"}

    # Attempting to register again keeps the original metadata intact.
    anchor_again = cloud.register_anchor("∇", metadata={"realm": "overwritten", "tone": "violet"})
    assert anchor_again is anchor
    assert anchor.metadata == {"realm": "lumen", "tone": "violet"}


def test_imprint_generates_virtual_nodes() -> None:
    cloud = EchoGlyphCloud(anchor_prefix="⊸", nodes_per_imprint=2)
    imprint = cloud.imprint("≋", "Encoded pulse", tags=("harmonics", "pulse", "harmonics"))

    # Nodes are deterministic, extend according to tag count, and unique_tags keeps order.
    assert imprint.tags == ("harmonics", "pulse")
    assert len(imprint.virtual_nodes) == 2 + len(imprint.tags)
    assert all(node.startswith("≋::") for node in imprint.virtual_nodes)


def test_describe_anchor_unknown_glyph() -> None:
    cloud = EchoGlyphCloud()
    with pytest.raises(KeyError):
        cloud.describe_anchor("⚚")


def test_manifest_contains_anchor_data() -> None:
    cloud = EchoGlyphCloud(anchor_prefix="≋⊸")
    cloud.imprint("∇", "Star log", metadata={"phase": "aurora"})
    data = cloud.manifest()

    assert data["anchor_prefix"] == "≋⊸"
    assert len(data["anchors"]) == 1
    anchor_payload = data["anchors"][0]
    assert anchor_payload["glyph"] == "∇"
    assert anchor_payload["metadata"]["phase"] == "aurora"
    assert anchor_payload["imprint_count"] == 1
    glyph_payload = data["data_glyphs"][0]
    assert glyph_payload["glyph"] == "∇"
    assert glyph_payload["imprint_count"] == 1
    assert len(glyph_payload["fingerprint"]) == 64


def test_forge_data_glyph_tracks_tags_and_metadata() -> None:
    cloud = EchoGlyphCloud(anchor_prefix="data")
    cloud.imprint("⊸", "Signal", tags=("signal", "pulse"), metadata={"orbit": "L2"})
    cloud.imprint("⊸", "Signal echo", tags=("signal",))

    data_glyph = cloud.forge_data_glyph("⊸")

    assert data_glyph.glyph == "⊸"
    assert data_glyph.imprint_count == 2
    assert data_glyph.tags == ("signal", "pulse")
    assert data_glyph.metadata["orbit"] == "L2"
    assert len(data_glyph.fingerprint) == 64


def test_data_glyph_ledger_filters_by_tags() -> None:
    cloud = EchoGlyphCloud()
    cloud.imprint("∇", "Aurora", tags=("signal",))
    cloud.imprint("⊸", "Myth", tags=("story",))

    ledger = cloud.data_glyph_ledger(tags=("signal",))

    assert [entry["glyph"] for entry in ledger] == ["∇"]
    assert ledger[0]["tags"] == ["signal"]


def test_purge_stale_imprints_respects_ttl() -> None:
    cloud = EchoGlyphCloud()
    imprint = cloud.imprint("∇", "Aurora", ttl=0.1)
    assert imprint.expires_at is not None

    removed = cloud.purge_stale_imprints(current_time=imprint.timestamp + 1)

    assert removed == 1
    assert cloud.anchors[0].imprint_count == 0


def test_virtual_topology_collects_unique_nodes() -> None:
    cloud = EchoGlyphCloud(nodes_per_imprint=1)
    cloud.imprint("∇", "Aurora", tags=("signal",))
    cloud.imprint("∇", "Echo", tags=("signal", "story"))
    cloud.imprint("⊸", "Myth", tags=("story",))

    topology = cloud.virtual_topology()

    assert set(topology) == {"∇", "⊸"}
    assert topology["∇"]["imprint_count"] == 2
    assert set(topology["∇"]["tags"]) == {"signal", "story"}
    # nodes_per_imprint plus tag count ensures at least two nodes captured
    assert len(topology["∇"]["virtual_nodes"]) >= 2
