from __future__ import annotations

import textwrap

import pytest

from tools.pkscript_to_address import PkScriptError, pkscript_to_address


EXAMPLE_SCRIPT = textwrap.dedent(
    """
    Pkscript
    OP_DUP
    OP_HASH160
    b99c0c36e80c3409e730bfed297a85359489043d
    OP_EQUALVERIFY
    OP_CHECKSIG
    """
).strip().splitlines()


def test_pkscript_to_address_mainnet() -> None:
    address = pkscript_to_address(EXAMPLE_SCRIPT)
    assert address == "1HvQwsgSXk5p2DfWRAbbqDrWSSppuLLdha"


def test_pkscript_requires_valid_structure() -> None:
    broken_script = [
        "OP_DUP",
        "OP_HASH160",
        "not-a-hash",
        "OP_EQUALVERIFY",
    ]

    with pytest.raises(PkScriptError):
        pkscript_to_address(broken_script)


def test_unknown_network_is_rejected() -> None:
    with pytest.raises(ValueError):
        pkscript_to_address(EXAMPLE_SCRIPT, network="venusnet")


def test_pkscript_allows_pubkey_plus_checksig() -> None:
    pubkey = (
        "040005929d4eb70647483f96782be615f7b72f89f02996621b0d792fd3edd20"
        "dc229a99dfe63582d5471b55bcbb1d96c6e770ea406ce03bc798dc714bab36d5740"
    )
    script = ["Pkscript", pubkey, "OP_CHECK", "SIG"]

    address = pkscript_to_address(script)

    assert address == "1JtCBgQucKnV4j9nUYgVvrfYDGH4X3KHsu"


def test_pkscript_accepts_witness_program_hex() -> None:
    script = ["Pkscript", "0014751e76e8199196d454941c45d1b3a323f1433bd6"]

    address = pkscript_to_address(script)

    assert address == "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"


def test_pkscript_witness_program_respects_network() -> None:
    script = ["Pkscript", "0014751e76e8199196d454941c45d1b3a323f1433bd6"]

    address = pkscript_to_address(script, network="testnet")

    assert address == "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"

