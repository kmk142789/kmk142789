"""Tests for the ``tools.bitcoin_genesis_block`` helpers."""

from tools import bitcoin_genesis_block as genesis


def test_genesis_header_hash_matches_canonical_value() -> None:
    header = genesis.build_genesis_header()
    assert header.hash().hex() == (
        "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
    )


def test_genesis_merkle_root_matches_supplied_value() -> None:
    header = genesis.build_genesis_header()
    assert header.merkle_root.hex() == (
        "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"
    )


def test_genesis_difficulty_is_one() -> None:
    header = genesis.build_genesis_header()
    target = genesis.bits_to_target(header.bits)
    assert genesis.difficulty_from_target(target) == 1
