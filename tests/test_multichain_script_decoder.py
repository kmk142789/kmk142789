from __future__ import annotations

import base64

import pytest

from tools.script_decoder import decode_script, get_decoder


@pytest.mark.parametrize(
    "script, network, expected_address, script_type",
    [
        (
            [
                "Pkscript",
                "OP_DUP",
                "OP_HASH160",
                "b99c0c36e80c3409e730bfed297a85359489043d",
                "OP_EQUALVERIFY",
                "OP_CHECKSIG",
            ],
            "mainnet",
            "1HvQwsgSXk5p2DfWRAbbqDrWSSppuLLdha",
            "p2pkh",
        ),
        (
            "0014751e76e8199196d454941c45d1b3a323f1433bd6",
            "mainnet",
            "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
            "p2wpkh",
        ),
    ],
)
def test_bitcoin_decoding_variants(
    script: list[str] | str, network: str, expected_address: str, script_type: str
) -> None:
    decoded = decode_script("bitcoin", script, network=network)

    assert decoded.address == expected_address
    assert decoded.metadata["script_type"] == script_type
    assert decoded.metadata["network"] == network
    assert decoded.opcodes[0].startswith("OP")


def test_bitcoin_decoder_alias() -> None:
    decoder = get_decoder("btc")
    assert decoder.chain == "bitcoin"


def test_ethereum_contract_call_decoding() -> None:
    call_data = (
        "0xa9059cbb"
        "000000000000000000000000deadbeef00000000000000000000000000000000"
        "0000000000000000000000000000000000000000000000000000000000000001"
    )

    decoded = decode_script("ethereum", call_data)

    assert decoded.address is None
    assert decoded.metadata["call_type"] == "contract_call"
    assert decoded.metadata["function_selector"] == "0xa9059cbb"
    assert decoded.metadata["argument_words"]
    assert decoded.opcodes[0].startswith("CALLDATA_SELECTOR")


def test_ethereum_bytecode_uses_opcode_table() -> None:
    bytecode = "600a600052600a6020f3"

    decoded = decode_script("ethereum", bytecode)

    assert decoded.metadata["bytecode_hex"] == f"0x{bytecode}"
    assert decoded.opcodes == [
        "PUSH1 0x0a",
        "PUSH1 0x00",
        "MSTORE",
        "PUSH1 0x0a",
        "PUSH1 0x20",
        "RETURN",
    ]


def test_solana_instruction_decoding() -> None:
    payload = {
        "program_id": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        "accounts": [
            "Source1111111111111111111111111111111111111",
            "Dest11111111111111111111111111111111111111",
        ],
        "data": base64.b64encode(b"\x01\x02\x03").decode("ascii"),
    }

    decoded = decode_script("solana", payload)

    assert decoded.metadata["program_id"] == payload["program_id"]
    assert decoded.metadata["account_count"] == 2
    assert decoded.metadata["instruction_discriminator"] == "0x01"
    assert any(op.startswith("ACCOUNT") for op in decoded.opcodes)
    assert decoded.opcodes[-1].startswith("INSTRUCTION 0x010203")
