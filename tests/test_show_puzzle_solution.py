import pytest

from satoshi import show_puzzle_solution
from satoshi.show_puzzle_solution import (
    _hash160_to_p2pkh_address,
    _parse_p2pkh_hash160,
)


PUZZLE_24_HASH160 = "0959e80121f36aea13b3bad361c15dac26189e2f"
PUZZLE_24_ADDRESS = "1rSnXMr63jdCuegJFuidJqWxUPV7AtUf7"
PUZZLE_65_HASH160 = "52e763a7ddc1aa4fa811578c491c1bc7fd570137"
PUZZLE_65_ADDRESS = "18ZMbwUFLMHoZBbfpCjUJQTCMCbktshgpe"


def test_parse_pkscript_human_readable():
    script = """OP_DUP\nOP_HASH160\n0959e80121f36aea13b3bad361c15dac26189e2f\nOP_EQUALVERIFY\nOP_CHECKSIG"""
    assert _parse_p2pkh_hash160(script) == PUZZLE_24_HASH160


def test_parse_pkscript_hexadecimal():
    script = "76a9140959e80121f36aea13b3bad361c15dac26189e2f88ac"
    assert _parse_p2pkh_hash160(script) == PUZZLE_24_HASH160


def test_hash160_to_p2pkh_address():
    assert _hash160_to_p2pkh_address(PUZZLE_24_HASH160) == PUZZLE_24_ADDRESS


def test_parse_pkscript_invalid_tokens():
    with pytest.raises(ValueError):
        _parse_p2pkh_hash160("OP_HASH160 0959e80121f36aea13b3bad361c15dac26189e2f")


def test_hash160_to_p2pkh_address_puzzle_65():
    assert _hash160_to_p2pkh_address(PUZZLE_65_HASH160) == PUZZLE_65_ADDRESS


def test_cli_can_display_canonical_script(capsys):
    show_puzzle_solution.main(["26", "--show-script"])
    captured = capsys.readouterr()
    assert "Canonical P2PKH script:" in captured.out
    assert (
        "ASM : OP_DUP OP_HASH160 bfebb73562d4541b32a02ba664d140b5a574792f"
        " OP_EQUALVERIFY OP_CHECKSIG"
    ) in captured.out
    assert "HEX : 76a914bfebb73562d4541b32a02ba664d140b5a574792f88ac" in captured.out


def test_parse_pkscript_with_metadata_lines():
    script = """Puzzle #47\n1Pd8VvT49-mXCZ6ay7Z\nPkscript\nOP_DUP\nOP_HASH160\nf828005d41b0f4fed4c8dca3b06011072cfb07d4\nOP_EQUALVERIFY\nOP_CHECKSIG"""
    assert _parse_p2pkh_hash160(script) == "f828005d41b0f4fed4c8dca3b06011072cfb07d4"


def test_parse_pkscript_with_puzzle_65_metadata():
    script = """Puzzle #65\n18ZMbwUFL-Cbktshgpe\nPkscript\nOP_DUP\nOP_HASH160\n52e763a7ddc1aa4fa811578c491c1bc7fd570137\nOP_EQUALVERIFY\nOP_CHECKSIG"""
    assert _parse_p2pkh_hash160(script) == PUZZLE_65_HASH160
