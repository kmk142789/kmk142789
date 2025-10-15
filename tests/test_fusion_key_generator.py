from __future__ import annotations

import json

import pytest

from code.fusion_key_generator import (
    FusionKey,
    generate_fusion_key,
    generate_fusion_key_batch,
    main,
)

SEED = "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"


def test_generate_fusion_key_deterministic() -> None:
    key = generate_fusion_key(SEED, index=2)
    assert isinstance(key, FusionKey)
    assert key.index == 2
    assert key.private_key_hex == (
        "09b145e21516091a8fe61a2182e012567b2ea68b96ac2ae7bbaa3c9a62b53a95"
    )
    assert key.signature_hex == (
        "7fdf0e4ad8c9c9f211c0be9e6a56dc41bd8b9ae7fbbf390ade79d0e4a2aace93"
        "35bb692ca6e8a446dc97b2c81265dbc32bef40b29602bed3e0d645b5924b5295"
    )
    assert "Fusion Key 2" in key.summary()


def test_generate_fusion_key_batch_sequence() -> None:
    keys = generate_fusion_key_batch(SEED, count=2, start_index=3)
    assert [key.index for key in keys] == [3, 4]
    assert len({key.private_key_hex for key in keys}) == 2


def test_cli_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([SEED, "-n", "2", "--start-index", "1", "--json"])
    assert exit_code == 0
    captured = capsys.readouterr().out
    payload = json.loads(captured)
    assert isinstance(payload, list)
    assert len(payload) == 2
    assert payload[0]["index"] == 1
    assert payload[1]["index"] == 2


def test_generate_fusion_key_batch_invalid_count() -> None:
    with pytest.raises(ValueError):
        generate_fusion_key_batch(SEED, count=0)
