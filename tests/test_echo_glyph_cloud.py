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
