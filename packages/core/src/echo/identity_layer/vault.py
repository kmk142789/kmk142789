"""Encrypted vault for deterministic identity key management."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from bip_utils import (
    Bip39MnemonicGenerator,
    Bip39SeedGenerator,
    Bip39WordsNum,
    Bip44,
    Bip44Changes,
    Bip44Coins,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from nacl import signing


@dataclass
class Argon2Parameters:
    """Parameters used to derive the vault encryption key."""

    salt: bytes
    time_cost: int = 4
    memory_cost: int = 102400  # in KiB (100 MiB)
    parallelism: int = 8
    hash_len: int = 32

    @classmethod
    def create(cls, salt_len: int = 32, *, time_cost: int = 4, memory_cost: int = 102400, parallelism: int = 8) -> "Argon2Parameters":
        return cls(
            salt=os.urandom(salt_len),
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
        )


@dataclass
class VaultEvent:
    """Represents an event recorded in the encrypted history."""

    event: str
    did: str
    path: str
    timestamp: float
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "event": self.event,
            "did": self.did,
            "path": self.path,
            "timestamp": self.timestamp,
        }
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


class VaultIntegrityError(RuntimeError):
    """Raised when a vault checksum can not be restored."""


class EncryptedIdentityVault:
    """Secure storage for deterministic extended keys and metadata."""

    def __init__(
        self,
        root: Path,
        passphrase: str,
        *,
        argon2_params: Optional[Argon2Parameters] = None,
        history_filename: str = "history.log",
    ) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._vault_path = self._root / "vault.enc"
        self._history_path = self._root / history_filename
        self._passphrase = passphrase.encode("utf-8")
        self._argon2_params = argon2_params
        self._state: Dict[str, object] = {}

        if self._vault_path.exists():
            self._load()
        else:
            self._argon2_params = argon2_params or Argon2Parameters.create()
            self._initialize_new_vault()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_keys(self) -> List[Dict[str, object]]:
        return list(self._state.get("keys", []))

    def get_key(self, *, chain: str, account: int, index: int, change: int = 0) -> Optional[Dict[str, object]]:
        for entry in self.list_keys():
            derivation = entry.get("derivation", {})
            if (
                derivation.get("chain") == chain
                and derivation.get("account") == account
                and derivation.get("index") == index
                and derivation.get("change") == change
            ):
                return entry
        return None

    def ensure_key(
        self,
        *,
        chain: str,
        account: int,
        index: int,
        change: int = 0,
        origin: str,
        platform_name: Optional[str] = None,
    ) -> Dict[str, object]:
        existing = self.get_key(chain=chain, account=account, index=index, change=change)
        if existing:
            return existing
        key_entry = self._derive_key_entry(
            chain=chain,
            account=account,
            index=index,
            change=change,
            origin=origin,
            platform_name=platform_name or platform.platform(),
        )
        keys = self._state.setdefault("keys", [])
        keys.append(key_entry)
        self._persist()
        self._record_event(
            VaultEvent(
                event="key.generated",
                did=key_entry["did"],
                path=key_entry["derivation"]["path"],
                timestamp=time.time(),
                metadata={"origin": origin, "platform": key_entry["metadata"]["platform"]},
            )
        )
        return key_entry

    def sign(self, did: str, message: bytes) -> bytes:
        for entry in self.list_keys():
            if entry.get("did") != did:
                continue
            sk = base64.b64decode(entry["secret_key_b64"])
            signer = signing.SigningKey(sk)
            signed = signer.sign(message)
            self._record_event(
                VaultEvent(
                    event="key.signed",
                    did=did,
                    path=entry["derivation"]["path"],
                    timestamp=time.time(),
                )
            )
            return signed.signature
        raise KeyError(f"Unknown DID: {did}")

    def rotate(self, *, chain: str, account: int, index: int, change: int = 0, origin: str) -> Dict[str, object]:
        keys = self._state.setdefault("keys", [])
        keys = [k for k in keys if not self._matches_derivation(k, chain, account, index, change)]
        self._state["keys"] = keys
        new_entry = self.ensure_key(
            chain=chain,
            account=account,
            index=index,
            change=change,
            origin=origin,
        )
        self._record_event(
            VaultEvent(
                event="key.rotated",
                did=new_entry["did"],
                path=new_entry["derivation"]["path"],
                timestamp=time.time(),
                metadata={"origin": origin},
            )
        )
        return new_entry

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _initialize_new_vault(self) -> None:
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)
        seed = Bip39SeedGenerator(mnemonic).Generate()
        self._state = {
            "master_seed_b64": base64.b64encode(seed).decode("ascii"),
            "keys": [],
            "checksum": "",
            "mnemonic": str(mnemonic),
            "argon2": self._argon_header(),
        }
        self._persist()
        self._persist_history([])

    def _persist(self) -> None:
        self._state["argon2"] = self._argon_header()
        checksum = self._compute_checksum(self._state)
        self._state["checksum"] = checksum
        encoded = json.dumps(self._state, sort_keys=True).encode("utf-8")
        cipher = AESGCM(self._derive_aes_key())
        nonce = os.urandom(12)
        ciphertext = cipher.encrypt(nonce, encoded, None)
        header = json.dumps(self._argon_header()).encode("utf-8")
        header_len = len(header).to_bytes(4, "big")
        payload = header_len + header + nonce + ciphertext
        self._vault_path.write_bytes(payload)

    def _load(self) -> None:
        data = self._vault_path.read_bytes()
        header_len = int.from_bytes(data[:4], "big")
        header = json.loads(data[4 : 4 + header_len])
        params = Argon2Parameters(
            salt=base64.b64decode(header["salt_b64"]),
            time_cost=int(header["time_cost"]),
            memory_cost=int(header["memory_cost"]),
            parallelism=int(header["parallelism"]),
            hash_len=int(header.get("hash_len", 32)),
        )
        self._argon2_params = params
        offset = 4 + header_len
        nonce, ciphertext = data[offset : offset + 12], data[offset + 12 :]
        cipher = AESGCM(self._derive_aes_key(params))
        decoded = cipher.decrypt(nonce, ciphertext, None)
        state = json.loads(decoded)
        expected = self._compute_checksum(state)
        if expected != state.get("checksum"):
            self._state = state
            self._attempt_self_heal()
        else:
            self._state = state

    def _attempt_self_heal(self) -> None:
        mnemonic = self._state.get("mnemonic")
        if mnemonic:
            seed = Bip39SeedGenerator(mnemonic).Generate()
            self._state["master_seed_b64"] = base64.b64encode(seed).decode("ascii")
        keys = self._state.get("keys", [])
        restored: List[Dict[str, object]] = []
        for entry in keys:
            derivation = entry.get("derivation", {})
            try:
                regenerated = self._derive_key_entry(
                    chain=derivation["chain"],
                    account=int(derivation["account"]),
                    index=int(derivation["index"]),
                    change=int(derivation.get("change", 0)),
                    origin=entry.get("metadata", {}).get("origin", "unknown"),
                    platform_name=entry.get("metadata", {}).get("platform"),
                )
                regenerated["metadata"] = self._restore_metadata(entry.get("did", ""), regenerated["metadata"], entry.get("metadata", {}))
                restored.append(regenerated)
            except Exception as exc:  # noqa: BLE001
                raise VaultIntegrityError("Unable to self-heal vault") from exc
        self._state["keys"] = restored
        self._persist()

    def _derive_aes_key(self, params: Optional[Argon2Parameters] = None) -> bytes:
        params = params or self._argon2_params
        if params is None:
            raise VaultIntegrityError("Argon2 parameters missing")
        iterations = max(params.time_cost, 1) * 60_000
        return hashlib.pbkdf2_hmac(
            "sha256",
            self._passphrase,
            params.salt,
            iterations,
            dklen=params.hash_len,
        )

    def _matches_derivation(self, entry: Dict[str, object], chain: str, account: int, index: int, change: int) -> bool:
        deriv = entry.get("derivation", {})
        return (
            deriv.get("chain") == chain
            and int(deriv.get("account", -1)) == account
            and int(deriv.get("index", -1)) == index
            and int(deriv.get("change", -1)) == change
        )

    def _derive_key_entry(
        self,
        *,
        chain: str,
        account: int,
        index: int,
        change: int,
        origin: str,
        platform_name: Optional[str],
    ) -> Dict[str, object]:
        master_seed = base64.b64decode(self._state["master_seed_b64"])
        coin = self._resolve_coin(chain)
        coin_type = int(coin.value)
        root_ctx = Bip44.FromSeed(master_seed, coin)
        account_ctx = root_ctx.Purpose().Coin().Account(account)
        change_ctx = account_ctx.Change(Bip44Changes(change))
        addr_ctx = change_ctx.AddressIndex(index)
        did = self._make_did(chain, account, index, change)
        path = f"m/44'/{coin_type}'/{account}'/{change}/{index}"
        metadata = {
            "origin": origin,
            "platform": platform_name or platform.platform(),
            "created_at": time.time(),
        }
        entry = {
            "did": did,
            "public_key_b64": base64.b64encode(addr_ctx.PublicKey().RawCompressed().ToBytes()).decode("ascii"),
            "secret_key_b64": base64.b64encode(addr_ctx.PrivateKey().Raw().ToBytes()).decode("ascii"),
            "extended_public_key": addr_ctx.PublicKey().ToExtended(),
            "extended_private_key": addr_ctx.PrivateKey().ToExtended(),
            "derivation": {
                "path": path,
                "chain": chain,
                "account": account,
                "index": index,
                "change": change,
            },
            "metadata": metadata,
        }
        return entry

    def _make_did(self, chain: str, account: int, index: int, change: int) -> str:
        return f"did:echo:{chain}:{account}:{change}:{index}:{base64.urlsafe_b64encode(os.urandom(6)).decode('ascii')}"

    def _compute_checksum(self, payload: Dict[str, object]) -> str:
        material = json.dumps({k: v for k, v in payload.items() if k != "checksum"}, sort_keys=True).encode("utf-8")
        return hashlib.sha256(material).hexdigest()

    def _argon_header(self) -> Dict[str, object]:
        params = self._argon2_params or Argon2Parameters.create()
        self._argon2_params = params
        return {
            "salt_b64": base64.b64encode(params.salt).decode("ascii"),
            "time_cost": params.time_cost,
            "memory_cost": params.memory_cost,
            "parallelism": params.parallelism,
            "hash_len": params.hash_len,
        }

    def _record_event(self, event: VaultEvent) -> None:
        history = self._load_history()
        history.append(event.to_dict())
        self._persist_history(history)

    def _persist_history(self, events: Iterable[Dict[str, object]]) -> None:
        cipher = AESGCM(self._derive_aes_key())
        payload = json.dumps(list(events), sort_keys=True).encode("utf-8")
        nonce = os.urandom(12)
        encrypted = nonce + cipher.encrypt(nonce, payload, None)
        self._history_path.write_bytes(encrypted)

    def _load_history(self) -> List[Dict[str, object]]:
        if not self._history_path.exists():
            return []
        raw = self._history_path.read_bytes()
        nonce, ciphertext = raw[:12], raw[12:]
        cipher = AESGCM(self._derive_aes_key())
        decoded = cipher.decrypt(nonce, ciphertext, None)
        return json.loads(decoded)

    def export_history(self) -> List[VaultEvent]:
        return [VaultEvent(**item) for item in self._load_history()]

    def _resolve_coin(self, chain: str) -> Bip44Coins:
        mapping = {
            "bitcoin": Bip44Coins.BITCOIN,
            "ethereum": Bip44Coins.ETHEREUM,
            "litecoin": Bip44Coins.LITECOIN,
            "dogecoin": Bip44Coins.DOGECOIN,
        }
        try:
            return mapping[chain.lower()]
        except KeyError as exc:  # noqa: BLE001
            raise KeyError(f"Unsupported chain '{chain}'") from exc

    def _coin_type(self, chain: str) -> int:
        return int(self._resolve_coin(chain).value)

    def _restore_metadata(
        self,
        did: str,
        candidate: Dict[str, object],
        corrupted: Dict[str, object],
    ) -> Dict[str, object]:
        metadata = dict(candidate)
        history = self._load_history()
        for event in history:
            if event.get("event") == "key.generated" and event.get("did") == did:
                event_meta = event.get("metadata") or {}
                metadata.update(event_meta)
                break
        # Always prefer persisted timestamps when present
        if "created_at" in corrupted and isinstance(corrupted["created_at"], (int, float)):
            metadata.setdefault("created_at", corrupted["created_at"])
        metadata.setdefault("origin", corrupted.get("origin", "unknown"))
        metadata.setdefault("platform", corrupted.get("platform", platform.platform()))
        return metadata

