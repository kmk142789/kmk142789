from cognitive_harmonics.hyperprism_braid import generate_hyperprism_braid


def test_hyperprism_braid_fingerprint_is_stable():
    braid = generate_hyperprism_braid(cycles=5, seed="unit-test-seed")
    assert braid.fingerprint == "a382ce39636e9ff298002e6acbdd21550206c24ca7d5d2613e7b75e0b1fce757"


def test_hyperprism_braid_shape():
    braid = generate_hyperprism_braid(cycles=4, seed="shape-seed")
    assert len(braid.strands) == 3
    assert all(len(strand.steps) == 4 for strand in braid.strands)
    assert {strand.glyph for strand in braid.strands} == {"⌘", "✹", "∇"}
