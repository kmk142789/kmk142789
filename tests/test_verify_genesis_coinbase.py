"""Unit tests for the genesis coinbase verification helper functions."""

from pathlib import Path

import pytest

from tools.verify_genesis_coinbase import (
    GENESIS_HEADLINE,
    GenesisProof,
    bits_to_target,
    extract_coinbase_message,
)


FIXTURE_PATH = Path("proofs/genesis_coinbase_message.json")


@pytest.fixture(scope="module")
def genesis_proof() -> GenesisProof:
    return GenesisProof.from_json(str(FIXTURE_PATH))


def test_extract_coinbase_message_matches_headline(genesis_proof: GenesisProof) -> None:
    raw_tx = bytes.fromhex(genesis_proof.coinbase_raw_hex)
    assert extract_coinbase_message(raw_tx) == GENESIS_HEADLINE


def test_bits_to_target_matches_known_value(genesis_proof: GenesisProof) -> None:
    header_bytes = bytes.fromhex(genesis_proof.block_header_hex)
    bits_le = header_bytes[72:76]
    target = bits_to_target(bits_le)

    # The genesis block target is widely published: 0x00000000ffff0000000000000000000000000000000000000000000000000000
    expected_target = int(
        "00000000ffff0000000000000000000000000000000000000000000000000000", 16
    )
    assert target == expected_target

