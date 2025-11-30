import hashlib
import json
from pathlib import Path

VAULT_PATH = Path("vault/secure_store.json")


def compute_integrity():
    if not VAULT_PATH.exists():
        return 0.0

    content = VAULT_PATH.read_bytes()
    hashed = hashlib.sha256(content).hexdigest()

    meta_path = Path("vault/secure_store.meta")
    if not meta_path.exists():
        return 1.0

    with meta_path.open() as fp:
        meta = json.load(fp)

    stored_hash = meta.get("sha256")

    return 1.0 if stored_hash == hashed else 0.0


def write_integrity():
    content = VAULT_PATH.read_bytes()
    hashed = hashlib.sha256(content).hexdigest()
    meta_path = Path("vault/secure_store.meta")
    with meta_path.open("w") as fp:
        json.dump({"sha256": hashed}, fp)
