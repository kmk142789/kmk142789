from pathlib import Path

from atlas.storage import StorageReceipt, StorageService


def test_storage_receipts(tmp_path: Path):
    service = StorageService({}, tmp_path)
    receipt = service.put("memory", "demo", b"hello")
    data = service.get("memory", receipt)
    assert data == b"hello"

    fs_receipt = service.put("fs", "files/demo.txt", b"world")
    retrieved = service.get("fs", fs_receipt)
    assert retrieved == b"world"

    vault_receipt = service.put("vault_v1", "vault/demo", b"secret")
    vault_data = service.get("vault_v1", vault_receipt)
    assert vault_data == b"secret"
