from tools.decode_pkscript import DecodedScript, ScriptDecodeError, decode_p2pkh_script


def test_decode_textual_script_handles_split_opcodes() -> None:
    script = """OP_DUP\nOP_HASH160\n03b7892656a4c3df81b2f3e974f8e5ed2dc78dee\nOP_EQUALVERIFY\nOP_CH\nECKSIG"""
    decoded = decode_p2pkh_script(script)
    assert decoded == DecodedScript(
        address="1Lets1xxxx1use1xxxxxxxxxxxy2EaMkJ",
        pubkey_hash="03b7892656a4c3df81b2f3e974f8e5ed2dc78dee",
        network="mainnet",
    )


def test_decode_textual_script_handles_op_prefix_fragments() -> None:
    script = """OP\nDUP\nOP_HASH\n160\n03b7892656a4c3df81b2f3e974f8e5ed2dc78dee\nOP_EQUAL\nVERIFY\nOP\nCHECK\nSIG"""
    decoded = decode_p2pkh_script(script)
    assert decoded == DecodedScript(
        address="1Lets1xxxx1use1xxxxxxxxxxxy2EaMkJ",
        pubkey_hash="03b7892656a4c3df81b2f3e974f8e5ed2dc78dee",
        network="mainnet",
    )


def test_decode_script_ignores_metadata_lines() -> None:
    script = """1PWo3JeB9-as7fsVzXU\nPkscript\nOP_DUP\nOP_HASH160\nf6f5431d25bbf7b12e8add9af5e3475c44a0a5b8\nOP_EQUALVERIFY\nOP_CH\nECKSIG"""
    decoded = decode_p2pkh_script(script)
    assert decoded == DecodedScript(
        address="1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU",
        pubkey_hash="f6f5431d25bbf7b12e8add9af5e3475c44a0a5b8",
        network="mainnet",
    )


def test_decode_script_handles_literal_newline_escapes() -> None:
    script = "OP_DUP\\nOP_HASH160\\n03b7892656a4c3df81b2f3e974f8e5ed2dc78dee\\nOP_EQUALVERIFY\\nOP_CHECKSIG"
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


def test_decode_p2wpkh_hex_script() -> None:
    script = "00144469a262062f22997d827c8b31d09cbbe88684b3"
    decoded = decode_p2pkh_script(script)
    assert decoded == DecodedScript(
        address="bc1qg356ycsx9u3fjlvz0j9nr5yuh05gdp9n2d5htf",
        pubkey_hash="4469a262062f22997d827c8b31d09cbbe88684b3",
        network="mainnet",
        script_type="p2wpkh",
        witness_version=0,
    )


def test_decode_script_ignores_comment_lines_and_fragments() -> None:
    script = """# leading metadata
OP_DUP # duplicate top stack item
# inline payload comment follows
OP_HASH160
03b7892656a4c3df81b2f3e974f8e5ed2dc78dee
# enforce equality
OP_EQUALVERIFY # ensure signature matches
#
OP_CHECKSIG
"""
    decoded = decode_p2pkh_script(script)
    assert decoded == DecodedScript(
        address="1Lets1xxxx1use1xxxxxxxxxxxy2EaMkJ",
        pubkey_hash="03b7892656a4c3df81b2f3e974f8e5ed2dc78dee",
        network="mainnet",
    )


def test_invalid_script_raises() -> None:
    bad_script = "OP_HASH160 00112233445566778899aabbccddeeff00112233 OP_EQUALVERIFY"
    try:
        decode_p2pkh_script(bad_script)
    except ScriptDecodeError as exc:
        assert "five elements" in str(exc)
    else:
        raise AssertionError("expected ScriptDecodeError to be raised")


def test_decode_p2pk_script_returns_derived_address() -> None:
    pubkey = (
        "04001a23137d302f70eb0f78af6009262c85588562c1ba5e214052506393d36cb654af995cbba0c6a4"
        "6533da7da895047965e619dd0c862bf340d2f235b330169b"
    )
    script = f"{pubkey} OP_CHECKSIG"

    decoded = decode_p2pkh_script(script)

    assert decoded.script_type == "p2pk"
    assert decoded.pubkey == pubkey.lower()
    assert decoded.pubkey_hash == "37277ab3ad1c32e2a166045bd1591d95f6e1c1d1"
    assert decoded.address == "162dTd1RGztAFZ9YMmFZEpKuz3vFQ1DpgA"
