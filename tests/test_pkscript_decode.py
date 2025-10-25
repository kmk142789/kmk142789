from satoshi import pkscript_decode


def test_cli_lookup_puzzle_entry(capsys):
    script = "OP_DUP\nOP_HASH160\nf6d8ce225ffbdecec170f8298c3fc28ae686df25\nOP_EQUALVERIFY\nOP_CHECKSIG"
    pkscript_decode.main([script, "--lookup"])
    captured = capsys.readouterr()
    assert "Hash160       : f6d8ce225ffbdecec170f8298c3fc28ae686df25" in captured.out
    assert "Legacy address: 1PWCx5fovoEaoBowAvF5k91m2Xat9bMgwb" in captured.out
    assert "Puzzle bits   : 35" in captured.out
    assert "Lookup        : matched puzzle entry" in captured.out


def test_cli_handles_p2pk_script(capsys):
    script = (
        "04001f255e5db2547c9c27591b14dde9b44f9ae24b8bf7cd01f20f45c0adc78ab862c8006a5bc35"
        "eb38f9d7c669c1c60e9d023f383e4368ecf4687dd052cd5093c OP_CHECKSIG"
    )
    pkscript_decode.main([script])
    captured = capsys.readouterr()
    assert "Script type   : p2pk" in captured.out
    assert (
        "Public key    : 04001f255e5db2547c9c27591b14dde9b44f9ae24b8bf7cd01f20f45c0adc78ab862c8006a5bc35"
        "eb38f9d7c669c1c60e9d023f383e4368ecf4687dd052cd5093c"
    ) in captured.out
    assert "Legacy address: 1MyfChU5YwBP4hXEUBDwVkYkLn5LqvBbp8" in captured.out
