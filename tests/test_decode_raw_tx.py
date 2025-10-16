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
