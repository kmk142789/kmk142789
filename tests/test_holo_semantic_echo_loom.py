import pytest

from src.holo_semantic_echo_loom import HoloSemanticEchoLoom, Spark


def test_loom_generates_consistent_signature_and_diagram():
    loom = HoloSemanticEchoLoom(seed_phrase="test-seed")
    sparks = [
        Spark(label="catalyst", intensity=0.72, vector=(1.0, 0.5)),
        Spark(label="echo", intensity=0.33, vector=(0.1,)),
        Spark(label="aurora", intensity=0.91, vector=(0.2, 0.3, 0.4)),
    ]
    loom.register_sparks(sparks)

    fabric = loom.loom()

    assert fabric["chronicle"]["sparks"] == 3
    assert fabric["signature"] == "9dd3057e4e7a993bad4a539430b08752a5e14dce494de537"
    assert "diagram" in fabric and fabric["diagram"].count("|") == 12

    # Deterministic glyph clusters for test inputs
    assert fabric["glyph_fabric"] == ["✺✹✦✧", "✺✹", "∇⊸≋✶"]


def test_requires_sparks_before_weaving():
    loom = HoloSemanticEchoLoom()
    with pytest.raises(ValueError):
        loom.loom()
