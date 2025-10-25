from satoshi import pkscript_decode


def test_cli_lookup_puzzle_entry(capsys):
    script = "OP_DUP\nOP_HASH160\nf6d8ce225ffbdecec170f8298c3fc28ae686df25\nOP_EQUALVERIFY\nOP_CHECKSIG"
    pkscript_decode.main([script, "--lookup"])
    captured = capsys.readouterr()
    assert "Hash160       : f6d8ce225ffbdecec170f8298c3fc28ae686df25" in captured.out
    assert "Legacy address: 1PWCx5fovoEaoBowAvF5k91m2Xat9bMgwb" in captured.out
    assert "Puzzle bits   : 35" in captured.out
    assert "Lookup        : matched puzzle entry" in captured.out
