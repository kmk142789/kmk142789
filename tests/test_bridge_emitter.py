from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.bridge_emitter import (
    BridgeConfig,
    BridgeEmitter,
    BridgeState,
    MerkleBatch,
    eth_calldata_for_root,
    opreturn_for_root,
    _sha256,
)


def test_merkle_batch_roundtrip() -> None:
    items = [{"seq": 1, "value": "a"}, {"seq": 2, "value": "b"}, {"seq": 3, "value": "c"}]
    batch = MerkleBatch.from_items(items)
    root, levels = batch.build_tree()

    # Each proof should recompute the root when verified manually.
    for index, item in enumerate(items):
        proof = MerkleBatch.proof_for_index(levels, index)
        leaf = json.dumps(item, sort_keys=True, separators=(",", ":")).encode()
        leaf_hash = _sha256(leaf)
        computed = leaf_hash
        position = index
        for sibling_hex in proof:
            sibling = bytes.fromhex(sibling_hex)
            if position % 2 == 0:
                computed = _sha256(computed + sibling)
            else:
                computed = _sha256(sibling + computed)
            position //= 2
        assert computed == root


def test_anchor_roundtrip(tmp_path: Path) -> None:
    stream = tmp_path / "stream.jsonl"
    with stream.open("w", encoding="utf-8") as handle:
        for seq in range(1, 5):
            handle.write(json.dumps({"seq": seq, "payload": seq}) + "\n")

    config = BridgeConfig(
        stream_path=stream,
        anchor_dir=tmp_path / "anchors",
        state_path=tmp_path / "state.json",
        batch_size=2,
    )
    emitter = BridgeEmitter(config)

    out_dir = emitter.process_once()
    assert out_dir is not None
    assert out_dir.exists()

    manifest = json.loads((out_dir / "batch_manifest.json").read_text())
    assert manifest["seq_start"] == 1
    assert manifest["seq_end"] == 2
    assert manifest["count"] == 2

    state = BridgeState.load(config.state_path)
    assert state.last_seq == 2

    op_hex = emitter.last_opreturn()
    assert isinstance(op_hex, str) and op_hex.startswith("6a20")

    eth_payload = json.loads(emitter.last_eth_calldata())
    assert eth_payload["fn"] == "anchor(bytes32)"

    # Running again should pick up remaining items.
    second_dir = emitter.process_once()
    assert second_dir is not None
    state = BridgeState.load(config.state_path)
    assert state.last_seq == 4

    # No more items -> returns None.
    assert emitter.process_once() is None


def test_helpers_validate_root_length() -> None:
    with pytest.raises(ValueError):
        opreturn_for_root("00")

    result = eth_calldata_for_root("beef")
    assert result["arg_root"].endswith("beef")
