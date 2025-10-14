from __future__ import annotations

from typing import List

import pytest
from nacl.secret import SecretBox

from echo.vault import Vault, VaultPolicy
from echo.vault import vault as vault_module

HEX_KEY = "f8f8a2b49d74b5eb1c9bf1120afcba91860f7dfabd3c8abf77c045f85a9c2c51"
WIF_KEY = "5KhwDZuG1b6zn3gPqWhfmVwp1XcQ4eK8kZRy58wVWSzbaVsBohE"
PAYLOAD = bytes.fromhex("deadbeef")


def _new_vault(tmp_path, passphrase: str = "secret") -> Vault:
    path = tmp_path / "vault.db"
    return Vault.open(str(path), passphrase)


def test_open_round_trip(tmp_path):
    vault = _new_vault(tmp_path)
    record = vault.import_key(label="alpha", key=HEX_KEY, fmt="hex")
    record_id = record.id
    vault.close()

    reopened = Vault.open(str(tmp_path / "vault.db"), "secret")
    retrieved = reopened.get(record_id)
    assert retrieved.label == "alpha"
    reopened.close()


def test_import_formats(tmp_path):
    vault = _new_vault(tmp_path)
    hex_record = vault.import_key(label="hex", key=HEX_KEY, fmt="hex")
    wif_record = vault.import_key(label="wif", key=WIF_KEY, fmt="wif")
    assert hex_record.fmt == "hex"
    assert wif_record.fmt == "wif"
    vault.close()


def test_find_by_label_and_tags(tmp_path):
    vault = _new_vault(tmp_path)
    vault.import_key(label="ops-key", key=HEX_KEY, fmt="hex", tags=["ops", "hot"])
    vault.import_key(label="cold-key", key=HEX_KEY, fmt="hex", tags=["ops", "cold"])
    matches = vault.find(q="ops")
    assert len(matches) == 2
    hot_only = vault.find(tags=["hot"])
    assert len(hot_only) == 1
    assert hot_only[0].label == "ops-key"
    vault.close()


def test_policy_enforcement(monkeypatch, tmp_path):
    vault = _new_vault(tmp_path)
    policy = VaultPolicy(max_sign_uses=2, cooldown_s=5)
    record = vault.import_key(label="guarded", key=HEX_KEY, fmt="hex", policy=policy)

    time_state = {"value": vault_module.time.time()}

    def fake_time():
        return time_state["value"]

    monkeypatch.setattr(vault_module.time, "time", fake_time)

    vault.sign(record.id, PAYLOAD)
    with pytest.raises(PermissionError):
        vault.sign(record.id, PAYLOAD)

    time_state["value"] += 10
    vault.sign(record.id, PAYLOAD)
    with pytest.raises(PermissionError):
        vault.sign(record.id, PAYLOAD)
    vault.close()


def test_signatures_unique_and_use_count(tmp_path):
    vault = _new_vault(tmp_path)
    record = vault.import_key(label="unique", key=HEX_KEY, fmt="hex")
    sig1 = vault.sign(record.id, PAYLOAD)["sig"]
    sig2 = vault.sign(record.id, PAYLOAD)["sig"]
    assert sig1 != sig2
    updated = vault.get(record.id)
    assert updated.use_count == 2
    vault.close()


def test_encrypt_at_rest(tmp_path):
    vault = _new_vault(tmp_path)
    record = vault.import_key(label="enc", key=HEX_KEY, fmt="hex")
    ciphertext, nonce = vault._store.get_ciphertext(record.id)
    assert ciphertext != bytes.fromhex(HEX_KEY)
    assert len(nonce) == SecretBox.NONCE_SIZE
    vault.close()


def test_zeroize_invoked(monkeypatch, tmp_path):
    vault = _new_vault(tmp_path)
    record = vault.import_key(label="wipe", key=HEX_KEY, fmt="hex")

    original = vault_module.zeroize
    calls: List[int] = []

    def spy(buffer):
        calls.append(len(buffer))
        original(buffer)

    monkeypatch.setattr(vault_module, "zeroize", spy)
    vault.sign(record.id, PAYLOAD)
    assert calls, "zeroize was not invoked"
    vault.close()
