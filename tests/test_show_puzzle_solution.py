import pytest

from satoshi.show_puzzle_solution import (
    SOLUTIONS_PATH,
    _hash160_to_p2pkh_address,
    _match_entry,
    _normalize_base58,
    _parse_p2pkh_hash160,
    _load_solutions,
)


PUZZLE_24_HASH160 = "0959e80121f36aea13b3bad361c15dac26189e2f"
PUZZLE_24_ADDRESS = "1rSnXMr63jdCuegJFuidJqWxUPV7AtUf7"


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


def test_normalize_base58_strips_separators():
    assert _normalize_base58(" 19EEC52kr-HT7Gp1TYT \n", allow_empty=False) == "19EEC52krHT7Gp1TYT"


def test_match_entry_allows_prefix_suffix_pattern():
    entries = _load_solutions(SOLUTIONS_PATH)
    entry = _match_entry(entries, address="19EEC52kr-HT7Gp1TYT")
    assert entry["address"] == "19EEC52krRUK1RkUAEZmQdjTyHT7Gp1TYT"
