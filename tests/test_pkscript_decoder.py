import pytest

from tools.pkscript_decoder import decode_p2pkh_script


def test_decode_mainnet_script():
    script = (
        "OP_DUP OP_HASH160 "
        "77ac8098d4726a592aed489e3880c23cfaf719ae OP_EQUALVERIFY OP_CHECKSIG"
    )
    assert decode_p2pkh_script(script) == "1Bun4VzuBJ7SUoQn97dinVfDyWAS336Ldg"


def test_invalid_script_template():
    with pytest.raises(ValueError):
        decode_p2pkh_script("OP_HASH160 00 OP_EQUALVERIFY")


def test_invalid_hash_length():
    script = "OP_DUP OP_HASH160 1234 OP_EQUALVERIFY OP_CHECKSIG"
    with pytest.raises(ValueError):
        decode_p2pkh_script(script)


def test_testnet_script():
    script = (
        "OP_DUP OP_HASH160 "
        "89abcdefabbaabbaabbaabbaabbaabbaabbaabba OP_EQUALVERIFY OP_CHECKSIG"
    )
    assert (
        decode_p2pkh_script(script, network="testnet")
        == "mt4tgWuYiNAnoweSUsbfQMPENRWw72ccPh"
    )
