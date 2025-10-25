import pytest

from satoshi.show_puzzle_solution import (
    _address_matches_query,
    _hash160_to_p2pkh_address,
    _parse_p2pkh_hash160,
)


PUZZLE_24_HASH160 = "0959e80121f36aea13b3bad361c15dac26189e2f"
PUZZLE_24_ADDRESS = "1rSnXMr63jdCuegJFuidJqWxUPV7AtUf7"
PUZZLE_33_ADDRESS = "187swFMjz1G54ycVU56B7jZFHFTNVQFDiu"


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


def test_address_matches_query_exact():
    assert _address_matches_query(PUZZLE_24_ADDRESS, PUZZLE_24_ADDRESS)


def test_address_matches_query_with_wildcard():
    assert _address_matches_query(PUZZLE_24_ADDRESS, "1rSnXMr63j-AtUf7")
    assert _address_matches_query(PUZZLE_33_ADDRESS, "187swFMjz-FTNVQFDiu")
    assert not _address_matches_query(PUZZLE_24_ADDRESS, "187swFMjz-FTNVQFDiu")
