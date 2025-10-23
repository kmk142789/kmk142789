from pathlib import Path

import pytest

from tools.decode_raw_tx import decode_raw_transaction


DATA_DIR = Path(__file__).with_name("data")


def test_decode_simple_transaction():
    raw_hex = (
        "0100000001"
        "0000000000000000000000000000000000000000000000000000000000000000"
        "01000000"
        "01"
        "51"
        "ffffffff"
        "01"
        "00f2052a01000000"
        "01"
        "51"
        "00000000"
    )

    decoded = decode_raw_transaction(raw_hex)

    assert decoded.version == 1
    assert decoded.lock_time == 0
    assert decoded.txid == "9796f3d9d720dbf4d6648c91e2c26072396c96059e4da709715cbd1b1eb46a95"
    assert decoded.wtxid == decoded.txid

    assert len(decoded.inputs) == 1
    txin = decoded.inputs[0]
    assert txin.prev_txid == "0000000000000000000000000000000000000000000000000000000000000000"
    assert txin.output_index == 1
    assert txin.script_sig == "51"
    assert txin.sequence == 0xFFFFFFFF
    assert txin.witness == []

    assert len(decoded.outputs) == 1
    txout = decoded.outputs[0]
    assert txout.value_satoshis == 5_000_000_000
    assert txout.script_pubkey == "51"
    assert txout.address is None


@pytest.mark.parametrize(
    "bad_hex, message",
    [
        ("00f", "even"),
        ("", "short"),
    ],
)
def test_decode_invalid_hex_inputs(bad_hex, message):
    with pytest.raises(ValueError, match=message):
        decode_raw_transaction(bad_hex)


def test_decode_standard_addresses_across_networks():
    raw_hex = (
        "01000000"
        "01"
        + "22" * 32
        + "00000000"
        "01"
        "51"
        "ffffffff"
        "04"
        "00f2052a01000000"
        "19"
        "76a91400112233445566778899aabbccddeeff0011223388ac"
        "0100000000000000"
        "17"
        "a91400112233445566778899aabbccddeeff0011223387"
        "0200000000000000"
        "16"
        "001400112233445566778899aabbccddeeff00112233"
        "0300000000000000"
        "22"
        "5120000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
        "00000000"
    )

    decoded_mainnet = decode_raw_transaction(raw_hex)
    addresses = [txout.address for txout in decoded_mainnet.outputs]
    assert addresses == [
        "11MXTrefsj1ZS3Q5e9D6DxGzZKHWALyo9",
        "31hNT1M6Dn3PebjqCjooWrKD95c187fi2j",
        "bc1qqqgjyv6y24n80zye42aueh0wluqpzg3ndy2ehs",
        "bc1pqqqsyqcyq5rqwzqfpg9scrgwpugpzysnzs23v9ccrydpk8qarc0sg5tmnz",
    ]

    decoded_testnet = decode_raw_transaction(raw_hex, network="testnet")
    testnet_addresses = [txout.address for txout in decoded_testnet.outputs]
    assert testnet_addresses == [
        "mfXJpWwdUuAGLYX1oD7av9AbrYuzUZSGHb",
        "2MsFaWkH7qEYjrPNNssRg8oJUMRpAs4D6Ps",
        "tb1qqqgjyv6y24n80zye42aueh0wluqpzg3n8z32vr",
        "tb1pqqqsyqcyq5rqwzqfpg9scrgwpugpzysnzs23v9ccrydpk8qarc0slua5fd",
    ]

    decoded_regtest = decode_raw_transaction(raw_hex, network="regtest")
    regtest_addresses = [txout.address for txout in decoded_regtest.outputs]
    assert regtest_addresses[0] == "mfXJpWwdUuAGLYX1oD7av9AbrYuzUZSGHb"
    assert regtest_addresses[1] == "2MsFaWkH7qEYjrPNNssRg8oJUMRpAs4D6Ps"
    assert regtest_addresses[2] == "bcrt1qqqgjyv6y24n80zye42aueh0wluqpzg3n9tg8m2"
    assert regtest_addresses[3] == "bcrt1pqqqsyqcyq5rqwzqfpg9scrgwpugpzysnzs23v9ccrydpk8qarc0sj9hjuh"


def test_decode_p2pk_script_returns_legacy_address():
    pubkey = (
        "04001dedd724d2b4bbd7eca4cb718e794295a8ed8026131e7e1b2f65292b805df56a2da041c6"
        "ac52784c5ee25109f095958bf85ac348a6458b08d2d2c7ed7cd23f"
    )
    script_pubkey = "41" + pubkey + "ac"
    script_len = f"{len(script_pubkey) // 2:02x}"
    raw_hex = "".join(
        [
            "01000000",
            "01",
            "00" * 32,
            "00000000",
            "00",
            "ffffffff",
            "01",
            "00f2052a01000000",
            script_len,
            script_pubkey,
            "00000000",
        ]
    )

    decoded = decode_raw_transaction(raw_hex)

    assert decoded.outputs[0].address == "1F1R16o5vDABgnrxKGxHstcVswtgsJtHHx"


def test_decode_large_legacy_transaction():
    raw_hex = (DATA_DIR / "tx_e67a0550848b7932d7796aeea16ab0e48a5cfe81c4e8cca2c5b03e0416850114.hex").read_text().strip()

    decoded = decode_raw_transaction(raw_hex)

    assert decoded.version == 1
    assert decoded.lock_time == 0
    assert decoded.txid == "e67a0550848b7932d7796aeea16ab0e48a5cfe81c4e8cca2c5b03e0416850114"
    assert decoded.wtxid == decoded.txid

    assert len(decoded.inputs) == 27
    assert decoded.inputs[0].prev_txid == "7d74a566c2f3c198cd18e4346c98fa34004c8d74442cf67c55b07b84011f5704"
    assert decoded.inputs[-1].prev_txid == "46ec391a35a0a06494b5026feca98178a69d1e590407a2ad6f2692aa5f13adfa"

    assert len(decoded.outputs) == 2
    values = [txout.value_satoshis for txout in decoded.outputs]
    assert values == [7_995_600_000_000, 55_000_000]

    addresses = [txout.address for txout in decoded.outputs]
    assert addresses == [
        "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF",
        "1GPuT4JD1yKTEGnw2csTCqSAtS3DRiTD69",
    ]


def test_decode_segwit_input_with_witness_data():
    raw_hex = "".join(
        [
            "020000000001",
            "01",
            "11" * 32,
            "01000000",
            "00",
            "feffffff",
            "01",
            "50c3000000000000",
            "16",
            "00140f63219fedadc34ed6ff94f1b3b88ab8a504cfa9",
            "02",
            "47",
            "304402202867960a27050983e51f8e7841357abcc0e4ac2f30b97e7aa67969179aa8bd1e",
            "02204b809269c74b35b8ddc37e840ffabb3b7b862873ba99034d7e3a564056f9fedf01",
            "21",
            "027a4872acb18555c58daec8be1bd288596e3ea3cd29d41b67ee372b5839f7b998",
            "00000000",
        ]
    )

    decoded = decode_raw_transaction(raw_hex)

    assert decoded.version == 2
    assert decoded.lock_time == 0
    assert decoded.txid == "41ab3bb7c19441e1f4f098bdf3feed7f0ed54143b301cb2c530c64290a4716c5"
    assert decoded.wtxid == "2dffb2fb985fd0d3184898bf486551717cdd0d17aef79ae718ecb031eb56da8a"

    assert len(decoded.inputs) == 1
    txin = decoded.inputs[0]
    assert txin.prev_txid == "1111111111111111111111111111111111111111111111111111111111111111"
    assert txin.output_index == 1
    assert txin.script_sig == ""
    assert txin.sequence == 0xFFFFFFFE
    assert txin.witness == [
        "304402202867960a27050983e51f8e7841357abcc0e4ac2f30b97e7aa67969179aa8bd1e02204b809269c74b35b8ddc37e840ffabb3b7b862873ba99034d7e3a564056f9fedf01",
        "027a4872acb18555c58daec8be1bd288596e3ea3cd29d41b67ee372b5839f7b998",
    ]

    assert len(decoded.outputs) == 1
    txout = decoded.outputs[0]
    assert txout.value_satoshis == 50_000
    assert txout.script_pubkey == "00140f63219fedadc34ed6ff94f1b3b88ab8a504cfa9"
    assert txout.address == "bc1qpa3jr8ld4hp5a4hljncm8wy2hzjsfnafycxqg8"
