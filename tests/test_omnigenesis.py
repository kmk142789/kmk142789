import pytest

from omnigenesis import (
    Paradigm,
    create_paradigm_p1,
    create_paradigm_p2,
    create_paradigm_p3,
    derive_genesis_key,
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


def test_genesis_key_is_stable_and_condensed():
    noisy_phrase = (
        "Genesis historic mysterious cryptic0000000000000000000000000000000000000000000001"
        "one key to rule them all"
    )
    cleaned_variant = noisy_phrase.replace("cryptic", "CRyPTiC--")

    base_key = derive_genesis_key(noisy_phrase)
    variant_key = derive_genesis_key(cleaned_variant)

    assert base_key.startswith("genesis-")
    assert len(base_key.split("-", 1)[1]) == 32
    assert base_key == variant_key


def test_genesis_key_collapses_zero_padding_noise():
    assert derive_genesis_key("genesis 000001 00001") == derive_genesis_key("genesis 1")
