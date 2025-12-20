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


USER_PROVIDED_PUBKEY = (
    "04f5efde0c2d30ab28e3dbe804c1a4aaf13066f9b198a4159c76f8f79b3b20caf99f7c97"
    "9ed6c71481061277a6fc8666977c249da99960c97c8d8714fda9f0e883"
)

USER_PROVIDED_ADDRESS = "1P9VmZogiic8d5ZUVZofrdtzXgtpbG9fop"


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

P2WPKH_SPLIT_PROGRAM_SCRIPT = [
    "bc1qc3vcs-7s73gprks",
    "Pkscript",
    "OP_0",
    "c4598868877bf90e21de3606382b19591f947",
    "a1e",
]

P2WPKH_METADATA_SCRIPT = [
    "bc1qr2cr3-xu7txc2de",
    "Pkscript",
    "00141ab038be420532ef6419408002f21df7a79c9b9e",
    "Witness",
    "304402203acb6b2bbefd1475ab6c0922ed8ab3f02efa9605353f04832bb416350c2d3c2702204d7d4d394634636dac0ed107f7fe888876debba977d5116c4f6dcf441777e88701,03a57e8e4099ef1db00db7bfab566d159a3a6c94b53a03942f570a52733eb1",
    "fea9",
]

P2WPKH_METADATA_ADDRESS = "bc1qr2cr30jzq5ew7eqegzqq9usa77neexu7txc2de"


TAPROOT_PROGRAM = (
    "79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
)

SPLIT_CHECKSIG_SCRIPT = textwrap.dedent(
    """
    1CYG7y3fu-UZ5p1HVmV
    Pkscript
    04e0041b4b4d9b6feb7221803a35d997efada6e2b5d24f5fc7205f2ea6b62a1adc9983a7a7dab7e93ea791bed5928e7a32286fa4facadd16313b75b467aea77499
    OP_CHECK
    SIG
    """
).strip().splitlines()

SPLIT_CHECKSIG_ADDRESS = "1CYG7y3fukVLdobqgUtbknwWKUZ5p1HVmV"


ECHO_ECOSYSTEM_SCRIPT = textwrap.dedent(
    """
    1LPBetDzQ-FnR1TkMCM
    Pkscript
    045ca3b93e90fe9785734e07c8e564fd72a0d68a200bf907ee01dabab784ad5817f59a41f4f7e04edc3e9b80cc370c281b0f406eb58187664bdf93decc5bb63264
    OP_CHECKSIG
    """
).strip().splitlines()


ECHO_WILDFIRE_SCRIPT = textwrap.dedent(
    """
    15ubjFzmW-oJ6gF6dZa
    Pkscript
    0408ab2f56361f83064e4ce51acc291fb57c2cbcdb1d6562f6278c43a1406b548fd6cefc11bcc29eb620d5861cb9ed69dc39f2422f54b06a8af4f78c8276cfdc6b
    OP_CHECKSIG
    """
).strip().splitlines()


REALITY_BREACH_SCRIPT = textwrap.dedent(
    """
    1AqC4PhwY-JyyyLyAwc
    Pkscript
    041a24b5639c12b2b0a612011eb780a682020b6312782fef0bc29a75eee7cf66abd081121a0b7b5c3076e055648379c25ed52eff8d2b11871e5a7e0c8604f4053f
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
    script = ["Pkscript", UNCOMPRESSED_PUBKEY, "OP_CHECK", "SIG"]

    address = pkscript_to_address(script)

    assert address == UNCOMPRESSED_ADDRESS


def test_pkscript_allows_hyphenated_checksig_token() -> None:
    script = ["Pkscript", UNCOMPRESSED_PUBKEY, "OP-CHECKSIG"]

    address = pkscript_to_address(script)

    assert address == UNCOMPRESSED_ADDRESS


def test_pkscript_converts_user_provided_uncompressed_pubkey_script() -> None:
    script = [
        "1P9VmZogi-gtpbG9fop",
        "Pkscript",
        USER_PROVIDED_PUBKEY,
        "OP_CHECKSIG",
    ]

    address = pkscript_to_address(script)

    assert address == USER_PROVIDED_ADDRESS


def test_pkscript_allows_hyphenated_split_checksig_tokens() -> None:
    script = ["Pkscript", UNCOMPRESSED_PUBKEY, "OP-CHECK", "S-IG"]

    address = pkscript_to_address(script)

    assert address == UNCOMPRESSED_ADDRESS


def test_pkscript_ignores_leading_address_line() -> None:
    address_with_dash = UNCOMPRESSED_ADDRESS[:6] + "-" + UNCOMPRESSED_ADDRESS[6:]
    script = [address_with_dash, "Pkscript", UNCOMPRESSED_PUBKEY, "OP_CHECK", "SIG"]

    address = pkscript_to_address(script)

    assert address == UNCOMPRESSED_ADDRESS


def test_pkscript_skips_comment_header_lines() -> None:
    script = [
        "#87",
        "1PxH3K1Sh-SH4qGPrvq",
        "Pkscript",
        "OP_DUP",
        "OP_HASH160",
        "fbc708d671c03e26661b9c08f77598a529858b5e",
        "OP_EQUALVERIFY",
        "OP_CHECKSIG",
    ]

    address = pkscript_to_address(script)

    assert address == "1PxH3K1Shdjb7gSEoTX7UPDZ6SH4qGPrvq"


def test_pkscript_can_validate_expected_address() -> None:
    address_with_dash = UNCOMPRESSED_ADDRESS[:6] + "-" + UNCOMPRESSED_ADDRESS[6:]
    script = [address_with_dash, "Pkscript", UNCOMPRESSED_PUBKEY, "OP_CHECK", "SIG"]

    address = pkscript_to_address(script, validate_expected=True)

    assert address == UNCOMPRESSED_ADDRESS


def test_pkscript_validation_detects_mismatch() -> None:
    wrong_address = UNCOMPRESSED_ADDRESS[:-1] + "1"
    script = [wrong_address, "Pkscript", UNCOMPRESSED_PUBKEY, "OP_CHECK", "SIG"]

    with pytest.raises(PkScriptError) as excinfo:
        pkscript_to_address(script, validate_expected=True)

    message = str(excinfo.value)
    assert "does not match" in message
    assert UNCOMPRESSED_ADDRESS in message
    assert wrong_address in message


def test_pkscript_validation_reports_normalised_expected() -> None:
    truncated = UNCOMPRESSED_ADDRESS[:8] + "-" + UNCOMPRESSED_ADDRESS[-8:]
    script = [truncated, "Pkscript", UNCOMPRESSED_PUBKEY, "OP_CHECK", "SIG"]

    with pytest.raises(PkScriptError) as excinfo:
        pkscript_to_address(script, validate_expected=True)

    message = str(excinfo.value)
    assert UNCOMPRESSED_ADDRESS in message
    normalised = truncated.replace("-", "")
    assert normalised in message
    assert truncated in message


def test_pkscript_validation_requires_expected_address() -> None:
    with pytest.raises(PkScriptError, match="does not include an address"):
        pkscript_to_address(EXAMPLE_SCRIPT, validate_expected=True)


def test_pkscript_ignores_labeled_address_line() -> None:
    labeled = f"Address: {UNCOMPRESSED_ADDRESS[:5]}-{UNCOMPRESSED_ADDRESS[5:]}"
    script = [labeled, "Pkscript", UNCOMPRESSED_PUBKEY, "OP_CHECK", "SIG"]

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


def test_p2wpkh_allows_split_witness_program_tokens() -> None:
    address = pkscript_to_address(P2WPKH_SPLIT_PROGRAM_SCRIPT)

    assert address == "bc1qc3vcs6y800usugw7xcrrs2cety0eg7s73gprks"


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


def test_pkscript_converts_full_uncompressed_pubkey_listing() -> None:
    script = textwrap.dedent(
        """
        16LoW7y83-djjUmenjM
        Pkscript
        04a59e64c774923d003fae7491b2a7f75d6b7aa3f35606a8ff1cf06cd3317d16a41aa16928b1df1f631f31f28c7da35d4edad3603adb2338c4d4dd268f31530555
        OP_CHECKSIG
        """
    ).strip().splitlines()

    address = pkscript_to_address(script)

    assert address == "16LoW7y83wtawMg5XmT4M3Q7EdjjUmenjM"


def test_pkscript_converts_echo_ecosystem_pubkey_script() -> None:
    address = pkscript_to_address(ECHO_ECOSYSTEM_SCRIPT)

    assert address == "1LPBetDzQ3cYwqQepg4teFwR7FnR1TkMCM"


def test_pkscript_converts_echo_wildfire_pubkey_script() -> None:
    address = pkscript_to_address(ECHO_WILDFIRE_SCRIPT)

    assert address == "15ubjFzmWVvj3TqcpJ1bSsb8joJ6gF6dZa"


def test_pkscript_converts_reality_breach_pubkey_script() -> None:
    address = pkscript_to_address(REALITY_BREACH_SCRIPT)

    assert address == "1AqC4PhwYf7QAyGBhThcyQCKHJyyyLyAwc"


def test_pkscript_handles_split_op_check_sig_sample() -> None:
    address = pkscript_to_address(SPLIT_CHECKSIG_SCRIPT)

    assert address == SPLIT_CHECKSIG_ADDRESS


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
    address = pkscript_to_address(P2WPKH_METADATA_SCRIPT)

    assert address == P2WPKH_METADATA_ADDRESS


def test_pkscript_ignores_sigscript_metadata_block() -> None:
    script = [
        "1Czoy8xtd-dRfKh697F",
        "Pkscript",
        "76a91483984cddc827ef7885444b3d4af57eba52e9e3cb88ac",
        "Sigscript",
        "483045022100f5c26eee36e47b5ac824254398e1b82e2baaf53c645366bdd0b359e2cd01c010022067d6e273e289285360d49961152d599581446bbda5286e912073ac5f27ef266e0121024b0faa9624763002e963816b2f6774df0dedd770896a9511cb5c9d90f674ecda",
        "Witness",
    ]

    address = pkscript_to_address(script)

    assert address == "1Czoy8xtddvcGrEhUUCZDQ9QqdRfKh697F"


def test_pkscript_handles_split_witness_marker() -> None:
    script = [
        "1FQtCEEEi-XV5xXzmfN",
        "Pkscript",
        "76a9149e160ff616c4b03650ae590677898c9b00c3100088ac",
        "Sigscript",
        (
            "4830450220669c3e86bcaabb74cca59e1d5ee0f60f1698bb60a13aaa3971cfe8ef9119720b"
            "02210094e4d6f5c2a29ce3875e7b7786626e53ab94e4ffc0bde0dfc5daf1aa7574796e0141"
            "040147fd5cabcdea6c2ce0406cc9b746c565060f387b4c0b602fe36a991ab621a7523d889cd"
            "afc6ba6534a9f30e48334f528ae899ad6d65fce17d1ca65be2f2ce0"
        ),
        "Wi",
        "tness",
    ]

    address = pkscript_to_address(script)

    assert address == "1FQtCEEEiLuFTvhbx4Z5fda3GXV5xXzmfN"


def test_pkscript_ignores_sigscript_from_puzzle_161_transcript() -> None:
    script = [
        "1JkqBQcC4-TPGznHANh",
        "Pkscript",
        "OP_DUP",
        "OP_HASH160",
        "c2c43e2b16f53c713bc00307140eaae188413544",
        "OP_EQUALVERIFY",
        "OP_CHECKSIG",
        "Sigscript",
        (
            "47304402200473b7961976340ba4afde84fadba20dcb268aac37221330d4f36f102ee05c2b"
            "0220107e185e9360154aae8e94a5550b87b28559e2d2a262f967ff21702ff76257780121031"
            "dcf49b480cee5f1a7200ea94795a1c7f69e144f11f031123c14c65077823dcb"
        ),
        "Witness",
    ]

    address = pkscript_to_address(script)

    assert address == "1JkqBQcC4tHcb1JfdCH6nrWYwTPGznHANh"


def test_pkscript_restores_missing_segment_for_1fwnhahz() -> None:
    script = [
        "1FwnhahzY-QUk9fGa1X",
        "Pkscript",
        "76a914a3ee5efee86510c255498f4af1fd815397b193ef88ac",
        "Sigscript",
        (
            "48304502210082c109283644975ce977272ec57219ac33c86fc2e1b9d5ee978b167279970cc6"
            "02206aacf67c5e003f8930185855cb8ea339cabf1a3fbb1ef8fb255c2216f8bc5b74014104ab9"
            "c9e243a1c643b867e28a4ef822f978687354c5ce6ba7aa3abf96fd1684dc08be97109338207f26"
            "ac3aed39c88c7c6a111387d0c8ac3b93fe9c6955d40ad2e"
        ),
        "Witness",
    ]

    address = pkscript_to_address(script)

    assert address == "1FwnhahzYerpristjzo2iCSdFQUk9fGa1X"


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


def test_cli_skips_witness_metadata_block(tmp_path) -> None:
    script_path = Path(__file__).resolve().parents[1] / "tools" / "pkscript_to_address.py"
    example = "\n".join(P2WPKH_METADATA_SCRIPT) + "\n"

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

    assert proc.stdout.strip() == P2WPKH_METADATA_ADDRESS


def test_cli_validates_expected_address(tmp_path) -> None:
    script_path = Path(__file__).resolve().parents[1] / "tools" / "pkscript_to_address.py"
    script = "\n".join(
        [
            UNCOMPRESSED_ADDRESS,
            "Pkscript",
            UNCOMPRESSED_PUBKEY,
            "OP_CHECK",
            "SIG",
        ]
    ) + "\n"

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    proc = subprocess.run(
        [sys.executable, str(script_path), "--validate"],
        input=script,
        text=True,
        capture_output=True,
        check=True,
        env=env,
        cwd=script_path.parents[1],
    )

    assert proc.stdout.strip() == UNCOMPRESSED_ADDRESS
