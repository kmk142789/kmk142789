from tools.decode_pkscript import DecodedScript, ScriptDecodeError, decode_p2pkh_script


def test_decode_textual_script_handles_split_opcodes() -> None:
    script = """OP_DUP\nOP_HASH160\n03b7892656a4c3df81b2f3e974f8e5ed2dc78dee\nOP_EQUALVERIFY\nOP_CH\nECKSIG"""
    decoded = decode_p2pkh_script(script)
    assert decoded == DecodedScript(
        address="1Lets1xxxx1use1xxxxxxxxxxxy2EaMkJ",
        pubkey_hash="03b7892656a4c3df81b2f3e974f8e5ed2dc78dee",
        network="mainnet",
    )


def test_decode_hex_script() -> None:
    script = "76a91403b7892656a4c3df81b2f3e974f8e5ed2dc78dee88ac"
    decoded = decode_p2pkh_script(script, network="mainnet")
    assert decoded.address == "1Lets1xxxx1use1xxxxxxxxxxxy2EaMkJ"


def test_invalid_script_raises() -> None:
    bad_script = "OP_HASH160 00112233445566778899aabbccddeeff00112233 OP_EQUALVERIFY"
    try:
        decode_p2pkh_script(bad_script)
    except ScriptDecodeError as exc:
        assert "five elements" in str(exc)
    else:
        raise AssertionError("expected ScriptDecodeError to be raised")
