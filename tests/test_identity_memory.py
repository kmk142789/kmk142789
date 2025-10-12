from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.identity_memory import (
    IdentityManager,
    MemoryStore,
    bootstrap_identity_memory,
)


@pytest.fixture()
def tmp_echo_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ECHO_DATA_DIR", str(tmp_path))
    return tmp_path


def test_identity_create_sign_verify_rotate(tmp_echo_dir: Path) -> None:
    keystore = tmp_echo_dir / "identity.keystore"
    doc = tmp_echo_dir / "identity.json"

    manager = IdentityManager.create(str(keystore), str(doc), passphrase="secret")
    assert manager.doc.did.startswith("did:echo:")
    assert keystore.exists() and doc.exists()

    payload = b"echo-test-payload"
    signature = manager.sign(payload).signature
    assert manager.verify(payload, signature) is True

    manager.rotate(passphrase="secret")
    signature2 = manager.sign(payload).signature
    assert signature2 != signature
    assert manager.verify(payload, signature2)

    # ensure persisted doc records the sig chain
    persisted_doc = json.loads(doc.read_text())
    assert persisted_doc["sig_chain"], "rotation should append signature chain"

    # load should succeed with same passphrase
    loaded = IdentityManager.load(str(keystore), str(doc), passphrase="secret")
    assert loaded.doc.prev_sig_b58 == manager.doc.prev_sig_b58


def test_memory_store_operations(tmp_echo_dir: Path) -> None:
    db_path = tmp_echo_dir / "memory.db"
    store = MemoryStore(str(db_path))
    store.init_schema()

    assert store.put("alpha", b"beta")
    assert store.get("alpha") == b"beta"

    event_id = store.remember_event("did:echo:test", "update", "alpha", b"beta")
    assert event_id == 1
    export = store.export_since(0)
    payloads = [json.loads(line) for line in export.splitlines() if line]
    assert payloads and payloads[0]["id"] == event_id
    assert store.head_hash() == payloads[-1]["hash"]

    cid = store.put_blob(b"blob-data")
    assert cid.startswith("b3:")
    assert store.get_blob(cid) == b"blob-data"

    store.close()


def test_bootstrap_identity_memory(tmp_echo_dir: Path) -> None:
    bundle = bootstrap_identity_memory("", base_dir=tmp_echo_dir)
    try:
        assert bundle.identity.doc.did.startswith("did:echo:")
        assert bundle.memory.path == tmp_echo_dir / "memory.db"
        assert bundle.keystore_path.exists()
        assert bundle.doc_path.exists()
    finally:
        bundle.close()
