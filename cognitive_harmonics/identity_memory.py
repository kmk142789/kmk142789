"""Persistent identity + memory layer translated for Cognitive Harmonix.

This module adapts the portable C++ reference implementation of Echo's
identity and memory substrate into a Pythonic form that integrates directly
with the Harmonix stack.  It provides:

* Cross-platform data directory management with optional ``ECHO_DATA_DIR``
  overrides so deployments can pin storage wherever the bridge orchestrator
  expects it.
* An :class:`IdentityManager` backed by Ed25519 keys, Argon2id key derivation,
  and XChaCha20-Poly1305 authenticated encryption powered by PyNaCl.
* A durable :class:`MemoryStore` powered by SQLite with a KV overlay, append-only
  event log, Merkle-style hash chaining, and a content-addressed blob space
  using BLAKE3 CIDs.
* Convenience helpers for bootstrapping the identity+memory bundle used by the
  Echo Harmonix bridge so callers only need to supply a passphrase.

The resulting layer is fully portable across Linux, macOS, and Windows while
remaining dependency-light and Harmonix-aware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import base64
import json
import os
import sqlite3
import threading
import time

try:  # pragma: no cover - optional dependency but required in production
    from blake3 import blake3 as _blake3_hash
except Exception:  # pragma: no cover - CI fallback
    _blake3_hash = None

from nacl import utils
from nacl.bindings import (
    crypto_aead_xchacha20poly1305_ietf_KEYBYTES,
    crypto_aead_xchacha20poly1305_ietf_NPUBBYTES,
    crypto_aead_xchacha20poly1305_ietf_decrypt,
    crypto_aead_xchacha20poly1305_ietf_encrypt,
)
from nacl.exceptions import CryptoError
from nacl.pwhash import argon2id
from nacl.signing import SigningKey, VerifyKey


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_file_atomic(path: Path, data: bytes) -> None:
    _ensure_parent(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_bytes(data)
    tmp_path.replace(path)


def _read_file(path: Path) -> bytes:
    return path.read_bytes()


def _b58encode(data: bytes) -> str:
    alphabet = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    if not data:
        return ""
    num = int.from_bytes(data, "big")
    encoded = bytearray()
    while num > 0:
        num, rem = divmod(num, 58)
        encoded.insert(0, alphabet[rem])
    # preserve leading zeros
    pad = 0
    for byte in data:
        if byte == 0:
            pad += 1
        else:
            break
    return (alphabet[0:1] * pad + encoded).decode()


def _now_ms() -> int:
    return int(time.time_ns() // 1_000_000)


def _blake3_digest(data: bytes) -> bytes:
    if _blake3_hash is not None:  # pragma: no branch - fast path
        return _blake3_hash(data).digest(length=32)
    # Fall back to hashlib.blake2b for environments without the blake3 module.
    # This keeps deterministic hashing for tests, albeit with slower throughput.
    from hashlib import blake2b  # local import avoids global dependency

    return blake2b(data, digest_size=32).digest()


def data_dir() -> str:
    """Return the platform-appropriate Echo data directory."""

    override = os.environ.get("ECHO_DATA_DIR")
    if override:
        path = Path(override).expanduser()
    else:
        if os.name == "nt":
            appdata = os.environ.get("APPDATA")
            path = Path(appdata) / "Echo" if appdata else Path.home() / "Echo"
        else:
            path = Path.home() / ".echo"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def _default_keystore_path(base: Optional[Path] = None) -> Path:
    base_dir = Path(base) if base is not None else Path(data_dir())
    return base_dir / "identity.keystore"


def _default_doc_path(base: Optional[Path] = None) -> Path:
    base_dir = Path(base) if base is not None else Path(data_dir())
    return base_dir / "identity.json"


def _default_memory_path(base: Optional[Path] = None) -> Path:
    base_dir = Path(base) if base is not None else Path(data_dir())
    return base_dir / "memory.db"


@dataclass(slots=True)
class IdentityKeys:
    """Raw Ed25519 keys."""

    public_key: bytes
    secret_key: bytes


@dataclass(slots=True)
class IdentityDoc:
    """Metadata tracked alongside the keystore."""

    did: str
    created_ms: int
    updated_ms: int
    prev_sig_b58: str = ""
    sig_chain: List[str] = field(default_factory=list)
    current_pk_b58: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "did": self.did,
            "created_ms": self.created_ms,
            "updated_ms": self.updated_ms,
            "prev_sig_b58": self.prev_sig_b58,
            "sig_chain": list(self.sig_chain),
            "current_pk_b58": self.current_pk_b58,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "IdentityDoc":
        return cls(
            did=str(payload["did"]),
            created_ms=int(payload["created_ms"]),
            updated_ms=int(payload["updated_ms"]),
            prev_sig_b58=str(payload.get("prev_sig_b58", "")),
            sig_chain=list(payload.get("sig_chain", [])),
            current_pk_b58=str(payload.get("current_pk_b58", "")),
        )


@dataclass(slots=True)
class SignResult:
    signature: bytes


class IdentityManager:
    """Manage the lifecycle of an Echo decentralized identifier."""

    def __init__(self, keys: IdentityKeys, doc: IdentityDoc, *, keystore_path: Path, doc_path: Path) -> None:
        self._keys = keys
        self._doc = doc
        self._keystore_path = keystore_path
        self._doc_path = doc_path
        self._signing_key = SigningKey(self._keys.secret_key)
        self._verify_key = VerifyKey(self._keys.public_key)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    @staticmethod
    def default_keystore_path() -> str:
        return str(_default_keystore_path())

    @staticmethod
    def default_doc_path() -> str:
        return str(_default_doc_path())

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------
    @classmethod
    def create(cls, keystore_path: str, doc_path: str, passphrase: str) -> "IdentityManager":
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key

        keys = IdentityKeys(
            public_key=bytes(verify_key),
            secret_key=signing_key.encode(),
        )
        did = f"did:echo:{_b58encode(keys.public_key)}"
        created = _now_ms()
        doc = IdentityDoc(
            did=did,
            created_ms=created,
            updated_ms=created,
            prev_sig_b58="",
            sig_chain=[],
            current_pk_b58=_b58encode(keys.public_key),
        )

        instance = cls(keys, doc, keystore_path=Path(keystore_path), doc_path=Path(doc_path))
        instance._persist_keystore(passphrase)
        instance._persist_doc()
        return instance

    @classmethod
    def load(cls, keystore_path: str, doc_path: str, passphrase: str) -> "IdentityManager":
        ks_path = Path(keystore_path)
        doc_path_obj = Path(doc_path)
        if not ks_path.exists() or not doc_path_obj.exists():
            raise FileNotFoundError("keystore and document must exist to load identity")

        payload = json.loads(_read_file(ks_path).decode("utf-8"))
        encrypted = bool(payload.get("encrypted", bool(passphrase)))
        salt_b64 = payload.get("salt")
        nonce_b64 = payload.get("nonce")
        pk = base64.b64decode(payload["pk"]) if isinstance(payload.get("pk"), str) else bytes(payload["pk"])
        sk_enc = base64.b64decode(payload["sk"]) if isinstance(payload.get("sk"), str) else bytes(payload["sk"])

        if encrypted:
            if not passphrase:
                raise ValueError("passphrase required to unlock encrypted keystore")
            salt = base64.b64decode(salt_b64) if isinstance(salt_b64, str) else bytes(salt_b64)
            nonce = base64.b64decode(nonce_b64) if isinstance(nonce_b64, str) else bytes(nonce_b64)
            key = argon2id.kdf(
                crypto_aead_xchacha20poly1305_ietf_KEYBYTES,
                passphrase.encode("utf-8"),
                salt,
                opslimit=argon2id.OPSLIMIT_SENSITIVE,
                memlimit=argon2id.MEMLIMIT_SENSITIVE,
            )
            try:
                sk = crypto_aead_xchacha20poly1305_ietf_decrypt(
                    sk_enc,
                    None,
                    nonce,
                    key,
                )
            except CryptoError as exc:
                raise ValueError("invalid passphrase for identity keystore") from exc
        else:
            sk = sk_enc

        keys = IdentityKeys(public_key=pk, secret_key=sk)
        doc_payload = json.loads(_read_file(doc_path_obj).decode("utf-8"))
        doc = IdentityDoc.from_dict(doc_payload)
        instance = cls(keys, doc, keystore_path=ks_path, doc_path=doc_path_obj)
        instance._persist_doc()  # ensures optional fields are present if older format
        return instance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def doc(self) -> IdentityDoc:
        return self._doc

    @property
    def pubkey(self) -> bytes:
        return self._keys.public_key

    def sign(self, message: bytes) -> SignResult:
        signature = self._signing_key.sign(message).signature
        return SignResult(signature=signature)

    def verify(self, message: bytes, signature: bytes) -> bool:
        try:
            self._verify_key.verify(message, signature)
            return True
        except CryptoError:
            return False

    def rotate(self, passphrase: str) -> None:
        new_signing = SigningKey.generate()
        new_verify = new_signing.verify_key
        link_signature = self._signing_key.sign(bytes(new_verify)).signature
        link_b58 = _b58encode(link_signature)

        self._doc.prev_sig_b58 = link_b58
        self._doc.sig_chain.append(link_b58)
        self._doc.updated_ms = _now_ms()
        self._doc.current_pk_b58 = _b58encode(bytes(new_verify))

        self._keys = IdentityKeys(public_key=bytes(new_verify), secret_key=new_signing.encode())
        self._signing_key = new_signing
        self._verify_key = new_verify

        self._persist_keystore(passphrase)
        self._persist_doc()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _persist_keystore(self, passphrase: str) -> None:
        salt: Optional[bytes] = None
        nonce: Optional[bytes] = None
        ciphertext: bytes
        encrypted = bool(passphrase)
        if passphrase:
            salt = utils.random(16)
            nonce = utils.random(crypto_aead_xchacha20poly1305_ietf_NPUBBYTES)
            key = argon2id.kdf(
                crypto_aead_xchacha20poly1305_ietf_KEYBYTES,
                passphrase.encode("utf-8"),
                salt,
                opslimit=argon2id.OPSLIMIT_SENSITIVE,
                memlimit=argon2id.MEMLIMIT_SENSITIVE,
            )
            ciphertext = crypto_aead_xchacha20poly1305_ietf_encrypt(
                self._keys.secret_key,
                None,
                nonce,
                key,
            )
        else:
            ciphertext = self._keys.secret_key

        payload = {
            "kty": "OKP",
            "crv": "Ed25519",
            "pk": base64.b64encode(self._keys.public_key).decode("ascii"),
            "sk": base64.b64encode(ciphertext).decode("ascii"),
            "encrypted": encrypted,
        }
        if encrypted and salt is not None and nonce is not None:
            payload["salt"] = base64.b64encode(salt).decode("ascii")
            payload["nonce"] = base64.b64encode(nonce).decode("ascii")

        _write_file_atomic(self._keystore_path, json.dumps(payload, sort_keys=True).encode("utf-8"))

    def _persist_doc(self) -> None:
        payload = self._doc.to_dict()
        payload["current_pk"] = base64.b64encode(self._keys.public_key).decode("ascii")
        _write_file_atomic(self._doc_path, json.dumps(payload, sort_keys=True).encode("utf-8"))


class MemoryStore:
    """Durable append-only memory with KV and blob overlays."""

    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path)
        _ensure_parent(self._path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._lock = threading.RLock()

    @property
    def path(self) -> Path:
        return self._path

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def __del__(self) -> None:  # pragma: no cover - best-effort cleanup
        try:
            self.close()
        except Exception:
            pass

    def init_schema(self) -> None:
        with self._lock, self._conn:  # type: ignore[arg-type]
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS kv (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    updated_ms INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_ms INTEGER NOT NULL,
                    actor_did TEXT NOT NULL,
                    type TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value BLOB NOT NULL,
                    prev_hash TEXT NOT NULL,
                    hash TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS blobs (
                    cid TEXT PRIMARY KEY,
                    data BLOB NOT NULL,
                    size INTEGER NOT NULL
                );
                """
            )

    # ------------------------------------------------------------------
    # KV overlay
    # ------------------------------------------------------------------
    def put(self, key: str, value: bytes) -> bool:
        with self._lock, self._conn:  # type: ignore[arg-type]
            self._conn.execute(
                """
                INSERT INTO kv(key, value, updated_ms)
                VALUES(?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_ms = excluded.updated_ms
                """,
                (key, value, _now_ms()),
            )
        return True

    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            cursor = self._conn.execute("SELECT value FROM kv WHERE key = ?", (key,))
            row = cursor.fetchone()
            return bytes(row[0]) if row else None

    # ------------------------------------------------------------------
    # Event log
    # ------------------------------------------------------------------
    def remember_event(self, actor_did: str, event_type: str, key: str, value: bytes) -> int:
        with self._lock, self._conn:  # type: ignore[arg-type]
            prev_hash = ""
            cursor = self._conn.execute(
                "SELECT hash FROM events ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                prev_hash = row[0]

            ts_ms = _now_ms()
            digest_input = (
                prev_hash.encode("utf-8")
                + actor_did.encode("utf-8")
                + b"\x00"
                + event_type.encode("utf-8")
                + b"\x00"
                + key.encode("utf-8")
                + b"\x00"
                + value
            )
            digest = _blake3_digest(digest_input).hex()
            cursor = self._conn.execute(
                """
                INSERT INTO events(ts_ms, actor_did, type, key, value, prev_hash, hash)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (ts_ms, actor_did, event_type, key, value, prev_hash, digest),
            )
            return int(cursor.lastrowid)

    def export_since(self, last_event_id: int) -> str:
        with self._lock:
            cursor = self._conn.execute(
                """
                SELECT id, ts_ms, actor_did, type, key, value, prev_hash, hash
                FROM events
                WHERE id > ?
                ORDER BY id ASC
                """,
                (last_event_id,),
            )
            lines: List[str] = []
            for row in cursor.fetchall():
                eid, ts_ms, actor_did, event_type, key, value, prev_hash, digest = row
                payload = {
                    "id": eid,
                    "ts_ms": ts_ms,
                    "actor_did": actor_did,
                    "type": event_type,
                    "key": key,
                    "value_b64": base64.b64encode(value).decode("ascii"),
                    "prev_hash": prev_hash,
                    "hash": digest,
                }
                lines.append(json.dumps(payload, sort_keys=True))
            return "\n".join(lines)

    def head_hash(self) -> str:
        with self._lock:
            cursor = self._conn.execute("SELECT hash FROM events ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else ""

    # ------------------------------------------------------------------
    # Blob store
    # ------------------------------------------------------------------
    def put_blob(self, data: bytes) -> str:
        digest = _blake3_digest(data).hex()
        cid = f"b3:{digest}"
        with self._lock, self._conn:  # type: ignore[arg-type]
            self._conn.execute(
                """
                INSERT OR IGNORE INTO blobs(cid, data, size)
                VALUES(?, ?, ?)
                """,
                (cid, data, len(data)),
            )
        return cid

    def get_blob(self, cid: str) -> Optional[bytes]:
        with self._lock:
            cursor = self._conn.execute("SELECT data FROM blobs WHERE cid = ?", (cid,))
            row = cursor.fetchone()
            return bytes(row[0]) if row else None


@dataclass(slots=True)
class IdentityMemoryBundle:
    """Convenience structure returned by :func:`bootstrap_identity_memory`."""

    identity: IdentityManager
    memory: MemoryStore
    keystore_path: Path
    doc_path: Path
    db_path: Path

    def close(self) -> None:
        self.memory.close()


def bootstrap_identity_memory(passphrase: str, *, base_dir: Optional[str | Path] = None) -> IdentityMemoryBundle:
    """Create or load the identity + memory stack in one call."""

    base_path = Path(base_dir) if base_dir is not None else Path(data_dir())
    keystore_path = _default_keystore_path(base_path)
    doc_path = _default_doc_path(base_path)
    db_path = _default_memory_path(base_path)

    if keystore_path.exists() and doc_path.exists():
        identity = IdentityManager.load(str(keystore_path), str(doc_path), passphrase)
    else:
        identity = IdentityManager.create(str(keystore_path), str(doc_path), passphrase)

    memory = MemoryStore(str(db_path))
    memory.init_schema()

    return IdentityMemoryBundle(
        identity=identity,
        memory=memory,
        keystore_path=keystore_path,
        doc_path=doc_path,
        db_path=db_path,
    )


__all__ = [
    "IdentityKeys",
    "IdentityDoc",
    "SignResult",
    "IdentityManager",
    "MemoryStore",
    "IdentityMemoryBundle",
    "bootstrap_identity_memory",
    "data_dir",
]
