import pytest

from tools.decode_raw_tx import decode_raw_transaction


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
