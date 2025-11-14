from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.crypto import keystore


FIXTURE = Path("tests/fixtures/echo_demo_keystore.json")
EXPECTED_KEY = bytes.fromhex(
    "d3c9e7f2105f62c98cbfbacfea3884d13a392fa1430df6a5e672ff7d8c6f7c16"
)


def test_decrypt_keyfile_json_round_trip():
    keyfile = json.loads(FIXTURE.read_text())
    result = keystore.decrypt_keyfile_json(keyfile, "echo-demo")
    assert result == EXPECTED_KEY


def test_decrypt_keyfile_path_helper():
    result = keystore.decrypt_keyfile(FIXTURE, "echo-demo")
    assert result == EXPECTED_KEY


def test_mac_mismatch_raises():
    keyfile = json.loads(FIXTURE.read_text())
    keyfile["crypto"]["mac"] = "00" * 32
    with pytest.raises(keystore.KeystoreDecryptError):
        keystore.decrypt_keyfile_json(keyfile, "echo-demo")


def test_unsupported_kdf_rejected():
    keyfile = json.loads(FIXTURE.read_text())
    keyfile["crypto"]["kdf"] = "argon2"
    with pytest.raises(ValueError):
        keystore.decrypt_keyfile_json(keyfile, "echo-demo")
