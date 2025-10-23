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

