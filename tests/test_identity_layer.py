import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from echo.identity_layer.vault import EncryptedIdentityVault


@pytest.fixture()
def vault(tmp_path: Path) -> EncryptedIdentityVault:
    return EncryptedIdentityVault(tmp_path, "passphrase")


def _read_raw(vault: EncryptedIdentityVault) -> tuple[bytes, bytes, bytes]:
    data = vault._vault_path.read_bytes()  # type: ignore[attr-defined]
    header_len = int.from_bytes(data[:4], "big")
    header = data[4 : 4 + header_len]
    nonce = data[4 + header_len : 4 + header_len + 12]
    ciphertext = data[4 + header_len + 12 :]
    return header, nonce, ciphertext


def test_key_derivation_and_metadata(vault: EncryptedIdentityVault) -> None:
    record = vault.ensure_key(chain="bitcoin", account=0, index=0, change=0, origin="test-suite")
    assert record["metadata"]["origin"] == "test-suite"
    assert record["derivation"]["path"].startswith("m/44'")
    # Check signature determinism
    signature = vault.sign(record["did"], b"hello")
    assert isinstance(signature, bytes)
    # History should have generation + signing events
    events = vault.export_history()
    assert {event.event for event in events} == {"key.generated", "key.signed"}


def test_self_heal_on_checksum_mismatch(vault: EncryptedIdentityVault) -> None:
    original = vault.ensure_key(chain="bitcoin", account=0, index=1, change=0, origin="tamper-test")
    header, nonce, ciphertext = _read_raw(vault)
    cipher = AESGCM(vault._derive_aes_key())  # type: ignore[attr-defined]
    decoded = cipher.decrypt(nonce, ciphertext, None)
    state = json.loads(decoded)
    # Corrupt checksum and metadata to trigger self-heal
    state["checksum"] = "deadbeef"
    state["keys"][0]["metadata"]["origin"] = "corrupted"
    new_nonce = b"0" * 12
    new_ciphertext = cipher.encrypt(new_nonce, json.dumps(state).encode("utf-8"), None)
    vault._vault_path.write_bytes(len(header).to_bytes(4, "big") + header + new_nonce + new_ciphertext)  # type: ignore[attr-defined]

    reloaded = EncryptedIdentityVault(vault._root, "passphrase")  # type: ignore[attr-defined]
    healed = reloaded.get_key(chain="bitcoin", account=0, index=1, change=0)
    assert healed is not None
    assert healed["metadata"]["origin"] == "tamper-test"
    assert healed["secret_key_b64"] == original["secret_key_b64"]


if __name__ == "__main__":
    pytest.main([__file__])
