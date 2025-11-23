import pytest

from src.entangled_resonance_cartographer import (
    AtlasResult,
    EntangledResonanceCartographer,
    ParallaxNode,
)


@pytest.fixture()
def sample_nodes():
    return (
        ParallaxNode(
            name="aurora",
            timeline=[0.1, 0.4, 0.9],
            emotion_map={"joy": 0.7, "focus": 0.3},
        ),
        ParallaxNode(
            name="tidal",
            timeline=[0.2, 0.5, 0.5, 0.8],
            emotion_map={"joy": 0.6, "focus": 0.5},
        ),
        ParallaxNode(
            name="spire",
            timeline=[0.0, 0.2, 0.4, 0.6],
            emotion_map={"joy": 0.4, "focus": 0.4, "awe": 0.8},
        ),
    )


def test_craft_atlas_builds_world_first_tensor(sample_nodes):
    cartographer = EntangledResonanceCartographer()
    atlas = cartographer.craft_atlas(sample_nodes, horizon=2, jitter=0.01)

    assert isinstance(atlas, AtlasResult)
    assert atlas.entanglement_tensor[0][1] == pytest.approx(0.8507, abs=1e-3)
    assert atlas.entanglement_tensor[1][2] == pytest.approx(0.7899, abs=1e-3)
    assert atlas.entanglement_tensor[2][0] == pytest.approx(0.7298, abs=1e-3)

    # Tensor should stay symmetric and diagonals should be perfect resonance.
    for i, row in enumerate(atlas.entanglement_tensor):
        assert row[i] == 1.0
        for j, value in enumerate(row):
            assert value == pytest.approx(atlas.entanglement_tensor[j][i])
            assert 0.0 <= value <= 1.0

    assert atlas.braid_indices["aurora"] == pytest.approx(0.527, abs=1e-3)
    assert atlas.braid_indices["tidal"] == pytest.approx(0.588, abs=1e-3)
    assert atlas.braid_indices["spire"] == pytest.approx(0.544, abs=1e-3)
    assert atlas.coherence == pytest.approx(0.790, abs=1e-3)
    assert atlas.vocabulary == ("awe", "focus", "joy")


def test_wavefront_projection_is_damped(sample_nodes):
    cartographer = EntangledResonanceCartographer()
    atlas = cartographer.craft_atlas(sample_nodes, horizon=2, jitter=0.01)

    wavefront = cartographer.project_wavefront(atlas, steps=3, damping=0.8)

    assert len(wavefront) == 3
    first_step = list(wavefront[0].values())
    third_step = list(wavefront[2].values())

    # Each node should settle toward the atlas coherence under damping.
    assert all(third <= first for first, third in zip(first_step, third_step))
    assert all(atlas.coherence - 0.05 <= value <= atlas.coherence + 0.05 for value in third_step)

    rendered = cartographer.render_wavefront(atlas, steps=2)
    assert "Wavefront projections" in rendered
    assert "t+1" in rendered and "t+2" in rendered


def test_manifest_contains_world_first_stamp(sample_nodes):
    cartographer = EntangledResonanceCartographer(world_first_stamp="parallax-braid:v9")
    atlas = cartographer.craft_atlas(sample_nodes, horizon=5)
    text = atlas.manifest()

    assert "parallax-braid:v9" in text
    assert "Braid indices" in text
    assert "Entanglement tensor" in text
    assert str(atlas.coherence)[:4] in text
