from __future__ import annotations

import json

import pytest

from echo.tools.evm_metadata_decoder import (
    CBORDecodeError,
    decode_cbor,
    describe_metadata,
    extract_metadata,
    load_bytecode,
)


SAMPLE_METADATA_HEX = "a2646970667342123464736f6c634400051100"
SAMPLE_BYTECODE_HEX = "6000" + SAMPLE_METADATA_HEX + "0013"


def test_load_bytecode_strips_non_hex_characters():
    messy_input = "0x60 00\n" + SAMPLE_METADATA_HEX + " 00 13"
    bytecode = load_bytecode(messy_input)
    assert bytecode == bytes.fromhex(SAMPLE_BYTECODE_HEX)


def test_extract_metadata_decodes_expected_map():
    result = extract_metadata(bytes.fromhex(SAMPLE_BYTECODE_HEX))
    assert result.bytecode_length == len(bytes.fromhex(SAMPLE_BYTECODE_HEX))
    assert result.metadata_length == len(bytes.fromhex(SAMPLE_METADATA_HEX))
    assert result.metadata_bytes == bytes.fromhex(SAMPLE_METADATA_HEX)
    assert isinstance(result.metadata, dict)
    assert result.metadata == {"ipfs": "0x1234", "solc": "0x00051100"}


def test_describe_metadata_includes_human_readable_output():
    result = extract_metadata(bytes.fromhex(SAMPLE_BYTECODE_HEX))
    summary = describe_metadata(result)
    assert "Bytecode length" in summary
    assert "Metadata length" in summary
    assert "ipfs" in summary
    assert "0x1234" in summary


def test_decode_cbor_rejects_trailing_data():
    payload = bytes.fromhex("a0ff")
    with pytest.raises(CBORDecodeError):
        decode_cbor(payload)


def test_cli_json_output(tmp_path, capsys):
    path = tmp_path / "bytecode.txt"
    path.write_text(SAMPLE_BYTECODE_HEX, encoding="utf-8")

    exit_code = load_module_main([str(path), "--json"])
    assert exit_code == 0
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)
    assert payload["metadata"]["ipfs"] == "0x1234"
    assert payload["metadata_length"] == len(bytes.fromhex(SAMPLE_METADATA_HEX))


def load_module_main(argv: list[str]) -> int:
    from echo.tools import evm_metadata_decoder

    return evm_metadata_decoder.main(argv)
