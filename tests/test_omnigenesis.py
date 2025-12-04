import pytest

from omnigenesis import (
    Paradigm,
    create_paradigm_p1,
    create_paradigm_p2,
    create_paradigm_p3,
    generate_paradigm_lineage,
)


def test_lineage_unique_paradigms():
    lineage = generate_paradigm_lineage()
    names = {p.name for p in lineage}
    assert len(names) == 3
    substrates = {p.substrate.name for p in lineage}
    assert len(substrates) == 3


def test_paradigm_step_updates_state():
    paradigm: Paradigm = create_paradigm_p1()
    before = dict(paradigm.substrate.state)
    result = paradigm.step(0.6)
    assert result["coherence"] >= before["coherence"]
    assert result["flux"] >= before["flux"]


def test_law_enforcement_blocks_violation():
    paradigm = create_paradigm_p2()
    # Force slack beyond boundary to trigger law violation after step
    paradigm.substrate.state["slack"] = 0.95
    with pytest.raises(ValueError):
        paradigm.step(0.4)


def test_human_uplift_layer_present():
    paradigm = create_paradigm_p3()
    uplift = paradigm.human_uplift
    assert "consent" in uplift.ethics.lower()
    assert "wellbeing" not in uplift.ethics.lower() or uplift.wellbeing_architecture
