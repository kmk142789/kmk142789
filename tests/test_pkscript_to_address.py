from __future__ import annotations

import os
import textwrap
import subprocess
import sys
from pathlib import Path

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


TAPROOT_PROGRAM = (
    "79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
)


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


def test_pkscript_allows_hyphenated_checksig_token() -> None:
    script = ["Pkscript", UNCOMPRESSED_PUBKEY, "OP-CHECKSIG"]

    address = pkscript_to_address(script)

    assert address == UNCOMPRESSED_ADDRESS


def test_pkscript_allows_hyphenated_split_checksig_tokens() -> None:
    script = ["Pkscript", UNCOMPRESSED_PUBKEY, "OP-CHECK", "S-IG"]

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


def test_p2tr_script_is_supported() -> None:
    script = ["Pkscript", "OP_1", TAPROOT_PROGRAM]

    address = pkscript_to_address(script)

    assert address == "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"


def test_p2tr_uses_correct_hrp_on_testnet() -> None:
    script = ["Pkscript", "OP_1", TAPROOT_PROGRAM]

    address = pkscript_to_address(script, network="testnet")

    assert address == "tb1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq47zagq"


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


def test_pkscript_handles_underscoreless_split_checksig_token() -> None:
    script = [
        "Pkscript",
        "OP_DUP",
        "OP_HASH160",
        "03b7892656a4c3df81b2f3e974f8e5ed2dc78dee",
        "OP_EQUALVERIFY",
        "OP",
        "CHECKSIG",
    ]

    address = pkscript_to_address(script)

    assert address == "1Lets1xxxx1use1xxxxxxxxxxxy2EaMkJ"


def test_pkscript_derives_address_for_uncompressed_pubkey() -> None:
    script = [
        "1LsfkvwMo-Tzs4qSZjz",
        "Pkscript",
        "04000d82179bdc0fdfd4c8f7b46e7bea3a84c35dbaacaee3f35193213728fb4afdac18a09151c36d7d16e8b72851e90e7ad4c247ac8ae734a3ce096cb354daf2c0",
        "OP_CHECK",
        "SIG",
    ]

    address = pkscript_to_address(script)

    assert address == "1LsfkvwMo6JBisYpGHkai18hyTzs4qSZjz"


def test_pkscript_accepts_split_pubkey_hash_tokens() -> None:
    script = [
        "1dot1xxxx-xxxwYqEEt",
        "Pkscript",
        "OP_DUP",
        "OP_HASH160",
        "06f61b94f0e562e41e71",
        "37a8b0aa78db61029257",
        "OP_EQUALVERIFY",
        "OP_CHECKSIG",
    ]

    address = pkscript_to_address(script)

    assert address == "1dot1xxxxx1sv1xxxxxxxxxxxxxwYqEEt"


def test_pkscript_accepts_split_script_hash_tokens() -> None:
    script = [
        "Pkscript",
        "OP_HASH160",
        "b2a3badd10273692",
        "5c846dc3270ae187",
        "3cb205d5",
        "OP_EQUAL",
    ]

    address = pkscript_to_address(script)

    assert address == "3HyaLqxcfDVfk4pqH6s2PRuA4umnCTgSE4"


def test_pkscript_handles_raw_witness_script_with_metadata() -> None:
    script = [
        "bc1qr2cr3-xu7txc2de",
        "Pkscript",
        "00141ab038be420532ef6419408002f21df7a79c9b9e",
        "Witness",
        "304402203acb6b2bbefd1475ab6c0922ed8ab3f02efa9605353f04832bb416350c2d3c2702204d7d4d394634636dac0ed107f7fe888876debba977d5116c4f6dcf441777e88701,03a57e8e4099ef1db00db7bfab566d159a3a6c94b53a03942f570a52733eb1",
        "fea9",
    ]

    address = pkscript_to_address(script)

    assert address == "bc1qr2cr30jzq5ew7eqegzqq9usa77neexu7txc2de"


def test_cli_handles_direct_script_invocation(tmp_path) -> None:
    script_path = Path(__file__).resolve().parents[1] / "tools" / "pkscript_to_address.py"
    example = "\n".join(EXAMPLE_SCRIPT) + "\n"

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    proc = subprocess.run(
        [sys.executable, str(script_path)],
        input=example,
        text=True,
        capture_output=True,
        check=True,
        env=env,
        cwd=script_path.parents[1],
    )

    assert proc.stdout.strip() == "1HvQwsgSXk5p2DfWRAbbqDrWSSppuLLdha"

