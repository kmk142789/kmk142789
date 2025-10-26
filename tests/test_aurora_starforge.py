import re

from tools.aurora_starforge import AuroraCanvas, generate_aurora, surprise


def test_generate_aurora_dimensions_and_seed():
    canvas = generate_aurora(width=16, height=6, seed=12345)
    assert isinstance(canvas, AuroraCanvas)
    assert canvas.width == 16
    assert canvas.height == 6
    rows = canvas.art.splitlines()
    assert len(rows) == 6
    assert all(len(row) == 16 for row in rows)
    assert canvas.seed == 12345


def test_generate_aurora_poem_structure():
    canvas = generate_aurora(seed=4242)
    assert len(canvas.poem) == 3
    assert canvas.poem[0]
    assert "seed" in canvas.poem[-1]


def test_surprise_block_contains_banner_and_seed():
    block = surprise(seed=7)
    assert "Aurora Starforge" in block
    assert re.search(r"seed 000000007", block)
    assert block.count("\n") > 3
