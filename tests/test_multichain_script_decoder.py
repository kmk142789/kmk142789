from __future__ import annotations

from tools.script_decoder import decode_script


def test_bitcoin_decoder_returns_normalised_metadata() -> None:
    script = [
        "Pkscript",
        "OP_DUP",
        "OP_HASH160",
        "b99c0c36e80c3409e730bfed297a85359489043d",
        "OP_EQUALVERIFY",
        "OP_CHECKSIG",
    ]

    result = decode_script("bitcoin", script, network="mainnet")

    assert result.addresses == ["1HvQwsgSXk5p2DfWRAbbqDrWSSppuLLdha"]
    assert result.metadata["script_type"] == "p2pkh"
    assert result.opcode_trace[0] == "OP_DUP"


def test_bitcoin_decoder_handles_segwit_programs() -> None:
    script = ["OP_0", "985658becff8c12af60a1039cfd4049e834b6fd2"]

    result = decode_script("bitcoin", script, network="mainnet")

    assert result.addresses == ["bc1qnpt930k0lrqj4as2zquul4qyn6p5km7jjf4d4r"]
    assert result.metadata["script_type"] == "p2wpkh"
    assert "witness_version" in result.metadata


def test_ethereum_decoder_disassembles_bytecode() -> None:
    result = decode_script("ethereum", "0x600160005260206000f3")

    assert result.metadata["format"] == "bytecode"
    assert result.metadata["length_bytes"] == 10
    assert result.opcode_trace[:3] == ["PUSH1 0x01", "PUSH1 0x00", "MSTORE"]
    assert result.opcode_trace[-1] == "RETURN"


def test_ethereum_calldata_mode_extracts_function_selector() -> None:
    arg1 = f"{0x0102030405060708090A0B0C0D0E0F10:064x}"
    arg2 = f"{1:064x}"
    payload = "a9059cbb" + arg1 + arg2
    result = decode_script("ethereum", payload, mode="calldata")

    assert result.metadata["format"] == "calldata"
    assert result.metadata["function_selector"] == "a9059cbb"
    assert result.metadata["argument_count"] == 2
    assert result.opcode_trace == ["ARG0", "ARG1"]


def test_solana_decoder_normalises_accounts_and_bytes() -> None:
    instruction = {
        "program_id": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        "accounts": [
            "Source1111111111111111111111111111111111111",
            "Dest222222222222222222222222222222222222222",
        ],
        "data": "AQIDBA==",
        "anchor_hint": "token_transfer",
    }

    result = decode_script("solana", instruction)

    assert result.addresses == instruction["accounts"]
    assert result.metadata["program_id"] == instruction["program_id"]
    assert result.metadata["format"] == "anchor_idl"
    assert result.metadata["data_length"] == 4
    assert result.opcode_trace[:4] == ["BYTE_01", "BYTE_02", "BYTE_03", "BYTE_04"]
