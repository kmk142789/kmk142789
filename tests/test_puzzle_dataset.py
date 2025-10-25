from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from satoshi.puzzle_dataset import (
    find_solution_by_address,
    get_puzzle_metadata,
    get_solution_by_bits,
    iter_puzzle_solutions,
    load_puzzle_solutions,
)
from tools.decode_pkscript import decode_p2pkh_script
from tools.verify_satoshi_34k_dataset import pubkey_to_p2pkh_address

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUZZLE_PROOF_DIR = PROJECT_ROOT / "satoshi" / "puzzle-proofs"


def test_dataset_is_sorted_and_complete():
    entries = load_puzzle_solutions()
    assert len(entries) == 82
    bits_values = [entry.bits for entry in entries]
    assert bits_values == sorted(bits_values)
    assert bits_values[0] == 1
    assert bits_values[69] == 70
    assert bits_values[-1] == 130


def test_public_key_round_trip_and_hash160():
    for entry in iter_puzzle_solutions():
        derived_address = pubkey_to_p2pkh_address(entry.public_key)
        assert derived_address == entry.address

        sha = hashlib.sha256(bytes.fromhex(entry.public_key)).digest()
        derived_hash160 = hashlib.new("ripemd160", sha).hexdigest()
        assert derived_hash160 == entry.hash160_compressed


def test_dataset_addresses_match_puzzle_proofs():
    proof_addresses: dict[str, dict] = {}
    for path in PUZZLE_PROOF_DIR.glob("puzzle*.json"):
        payload = json.loads(path.read_text())
        proof_addresses[payload["address"]] = payload

    for entry in iter_puzzle_solutions():
        proof = proof_addresses.get(entry.address)
        if proof is not None:
            assert proof["address"] == entry.address


def test_find_solution_by_address_handles_unknown():
    assert find_solution_by_address("1NonexistentAddress") is None
    sample = next(iter_puzzle_solutions())
    assert find_solution_by_address(sample.address) == sample
    with pytest.raises(KeyError):
        get_solution_by_bits(999)


def test_puzzle_metadata_exposes_locking_script():
    entry = get_puzzle_metadata(74)
    assert entry.address == "1FWGcVDK3JGzCC3WtkYetULPszMaK2Jksv"
    script = entry.p2pkh_script(separator="\n")
    assert script == (
        "OP_DUP\n"
        "OP_HASH160\n"
        "9f1adb20baeacc38b3f49f3df6906a0e48f2df3d\n"
        "OP_EQUALVERIFY\n"
        "OP_CHECKSIG"
    )

    decoded = decode_p2pkh_script(script)
    assert decoded.address == entry.address
    assert decoded.pubkey_hash == entry.hash160_compressed

    hex_script = entry.p2pkh_script_hex()
    assert hex_script == "76a9149f1adb20baeacc38b3f49f3df6906a0e48f2df3d88ac"
    decoded_hex = decode_p2pkh_script(hex_script)
    assert decoded_hex.address == entry.address
    assert decoded_hex.pubkey_hash == entry.hash160_compressed
