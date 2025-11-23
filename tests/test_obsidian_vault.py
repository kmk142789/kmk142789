from __future__ import annotations

from pathlib import Path

import pytest

from echo.vault.obsidian import ObsidianVault, VaultIntegrityError, VaultPaths


def test_obsidian_vault_round_trip(tmp_path: Path) -> None:
    paths = VaultPaths(vault_path=tmp_path / "vault.bin", key_path=tmp_path / "master.key")
    vault = ObsidianVault(paths=paths, anchor="Test Anchor")
    vault.forge_key()

    payload = {
        "anchor": "Test Anchor",
        "message": "The lattice is sealed.",
        "index": 7,
    }
    locked_payload = vault.lock_reality(payload)
    unlocked = vault.unlock_reality()

    assert locked_payload == payload
    assert unlocked == payload
    assert paths.vault_path.read_bytes().startswith(b"OBSIDIANv2")


@pytest.mark.parametrize("replacement", ["00" * 32, "ff" * 32])
def test_obsidian_vault_rejects_wrong_key(tmp_path: Path, replacement: str) -> None:
    paths = VaultPaths(vault_path=tmp_path / "vault.bin", key_path=tmp_path / "master.key")
    vault = ObsidianVault(paths=paths)
    vault.forge_key()
    vault.lock_reality()

    # Swap in a different key with the correct length to trigger auth failure.
    paths.key_path.write_text(replacement)

    with pytest.raises(VaultIntegrityError):
        vault.unlock_reality()
