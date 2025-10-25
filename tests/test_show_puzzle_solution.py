from satoshi.show_puzzle_solution import _hash160_from_pkscript


def test_hash160_from_pkscript_extracts_payload_from_metadata_block() -> None:
    script = """Puzzle #21

14oFNXucf-7riuyXs4h
Pkscript
OP_DUP
OP_HASH160
29a78213caa9eea824acf08022ab9dfc83414f56
OP_EQUALVERIFY
OP_CHECKSIG
"""

    assert _hash160_from_pkscript(script) == "29a78213caa9eea824acf08022ab9dfc83414f56"
