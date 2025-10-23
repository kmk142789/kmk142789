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

UNCOMPRESSED_PUBKEY = (
    "040005929d4eb70647483f96782be615f7b72f89f02996621b0d792fd3edd20"
    "dc229a99dfe63582d5471b55bcbb1d96c6e770ea406ce03bc798dc714bab36d5740"
)

UNCOMPRESSED_ADDRESS = "1JtCBgQucKnV4j9nUYgVvrfYDGH4X3KHsu"


P2SH_SCRIPT = textwrap.dedent(
    """
    Pkscript
    OP_HASH160
    b2a3badd102736925c846dc3270ae1873cb205d5
    OP_EQUAL
    """
).strip().splitlines()


P2WPKH_SCRIPT = [
    "Pkscript",
    "OP_0",
    "985658becff8c12af60a1039cfd4049e834b6",
    "fd2",
]


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
    script = ["Pkscript", UNCOMPRESSED_PUBKEY, "OP_CHECK", "SIG"]

    address = pkscript_to_address(script)

    assert address == UNCOMPRESSED_ADDRESS


def test_pkscript_ignores_leading_address_line() -> None:
    address_with_dash = UNCOMPRESSED_ADDRESS[:6] + "-" + UNCOMPRESSED_ADDRESS[6:]
    script = [address_with_dash, "Pkscript", UNCOMPRESSED_PUBKEY, "OP_CHECK", "SIG"]

    address = pkscript_to_address(script)

    assert address == UNCOMPRESSED_ADDRESS


def test_p2sh_script_is_supported() -> None:
    address = pkscript_to_address(P2SH_SCRIPT)

    assert address == "3HyaLqxcfDVfk4pqH6s2PRuA4umnCTgSE4"


def test_p2sh_uses_correct_testnet_prefix() -> None:
    address = pkscript_to_address(P2SH_SCRIPT, network="testnet")

    assert address == "2N9XnQateGg11wrTNxEUu1NtRHFywvnptxe"


def test_p2wpkh_script_is_supported() -> None:
    address = pkscript_to_address(P2WPKH_SCRIPT)

    assert address == "bc1qnpt930k0lrqj4as2zquul4qyn6p5km7jjf4d4r"


def test_p2wpkh_uses_correct_hrp_on_testnet() -> None:
    address = pkscript_to_address(P2WPKH_SCRIPT, network="testnet")

    assert address == "tb1qnpt930k0lrqj4as2zquul4qyn6p5km7jc0w7ws"


def test_pkscript_handles_split_checksig_token() -> None:
    script = [
        "1Lets1xxx-xxy2EaMkJ",
        "Pkscript",
        "OP_DUP",
        "OP_HASH160",
        "03b7892656a4c3df81b2f3e974f8e5ed2dc78dee",
        "OP_EQUALVERIFY",
        "OP_CH",
        "ECKSIG",
    ]

    address = pkscript_to_address(script)

    assert address == "1Lets1xxxx1use1xxxxxxxxxxxy2EaMkJ"

