"""Sovereign identity helpers with selective disclosure + recursive proofs."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from nacl.signing import VerifyKey

from .vault import EncryptedIdentityVault


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Selective disclosure Merkle helper
# ---------------------------------------------------------------------------


def _leaf_hash(key: str, value: Any) -> bytes:
    payload = _canonical_json({"key": key, "value": value})
    return _sha256(payload)


def _parent_hash(left: bytes, right: bytes) -> bytes:
    if right is None:
        right = left
    return _sha256(left + right)


@dataclass(frozen=True)
class ProofSegment:
    direction: str
    hash_hex: str

    def to_dict(self) -> Dict[str, str]:
        return {"direction": self.direction, "hash": self.hash_hex}


@dataclass(frozen=True)
class SelectiveDisclosureProof:
    """Proof container describing disclosed claims and their Merkle paths."""

    root: str
    disclosed: Mapping[str, Any]
    paths: Mapping[str, Sequence[ProofSegment]]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "root": self.root,
            "disclosed": {k: self.disclosed[k] for k in self.disclosed},
            "paths": {key: [segment.to_dict() for segment in self.paths[key]] for key in self.paths},
        }

    def verify(self, *, claims: Mapping[str, Any] | None = None) -> bool:
        candidate = claims or self.disclosed
        for key, segments in self.paths.items():
            if key not in candidate:
                return False
            node = _leaf_hash(key, candidate[key])
            for segment in segments:
                sibling = bytes.fromhex(segment.hash_hex)
                if segment.direction == "left":
                    node = _parent_hash(sibling, node)
                else:
                    node = _parent_hash(node, sibling)
            if node.hex() != self.root:
                return False
        return True


class MerkleSelectiveDisclosure:
    """Builds a deterministic Merkle tree for identity claims."""

    def __init__(self, claims: Mapping[str, Any]) -> None:
        if not isinstance(claims, Mapping) or not claims:
            raise ValueError("claims must be a non-empty mapping")
        self._claims = {str(k): claims[k] for k in sorted(claims)}
        self._levels: List[List[bytes]] = []
        self._key_index: Dict[str, int] = {}
        self._build_tree()

    @property
    def root(self) -> str:
        return self._levels[-1][0].hex()

    def prove(self, reveal_keys: Iterable[str]) -> SelectiveDisclosureProof:
        disclosed: Dict[str, Any] = {}
        paths: Dict[str, List[ProofSegment]] = {}
        for key in reveal_keys:
            if key not in self._claims:
                continue
            disclosed[key] = self._claims[key]
            index = self._key_index[key]
            path_segments = []
            current_index = index
            for level in self._levels[:-1]:
                sibling_index = current_index ^ 1
                if sibling_index >= len(level):
                    sibling_index = current_index
                sibling_hash = level[sibling_index]
                direction = "right" if sibling_index > current_index else "left"
                path_segments.append(ProofSegment(direction=direction, hash_hex=sibling_hash.hex()))
                current_index //= 2
            paths[key] = path_segments
        return SelectiveDisclosureProof(root=self.root, disclosed=disclosed, paths=paths)

    def _build_tree(self) -> None:
        leaves: List[bytes] = []
        for idx, (key, value) in enumerate(self._claims.items()):
            leaf = _leaf_hash(key, value)
            self._key_index[key] = idx
            leaves.append(leaf)
        self._levels = [leaves]
        current = leaves
        while len(current) > 1:
            next_level: List[bytes] = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else None
                next_level.append(_parent_hash(left, right))
            self._levels.append(next_level)
            current = next_level


# ---------------------------------------------------------------------------
# Capability credentials
# ---------------------------------------------------------------------------


def _encode_signature(signature: bytes) -> str:
    return base64.b64encode(signature).decode("ascii")


def _decode_signature(signature_b64: str) -> bytes:
    return base64.b64decode(signature_b64.encode("ascii"))


@dataclass
class CapabilityCredential:
    issuer: str
    subject: str
    capabilities: Sequence[str]
    nonce: str
    issued_at: str
    expires_at: Optional[str]
    constraints: Mapping[str, Any]
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issuer": self.issuer,
            "subject": self.subject,
            "capabilities": list(self.capabilities),
            "nonce": self.nonce,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "constraints": dict(self.constraints),
            "signature": self.signature,
        }

    def summary(self) -> Dict[str, Any]:
        return {
            "issuer": self.issuer,
            "subject": self.subject,
            "capabilities": list(self.capabilities),
            "expires_at": self.expires_at,
            "nonce": self.nonce,
        }


class CapabilityCredentialFactory:
    """Issues capability credentials anchored to the vault."""

    def __init__(self, vault: EncryptedIdentityVault, namespace: str = "echo.capability") -> None:
        self._vault = vault
        self._namespace = namespace

    def issue(
        self,
        *,
        issuer_did: str,
        subject_did: str,
        capabilities: Sequence[str],
        constraints: Optional[Mapping[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> CapabilityCredential:
        payload = {
            "@context": self._namespace,
            "issuer": issuer_did,
            "subject": subject_did,
            "capabilities": list(capabilities),
            "nonce": secrets.token_hex(16),
            "issued_at": _utc_now(),
            "expires_at": expires_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if expires_at else None,
            "constraints": dict(constraints or {}),
        }
        signature = self._vault.sign(issuer_did, _canonical_json(payload))
        payload.pop("@context", None)
        return CapabilityCredential(signature=_encode_signature(signature), **payload)


class CapabilityVerifier:
    """Validates capability credentials using DID verification keys."""

    def __init__(self, key_resolver: Mapping[str, str] | Callable[[str], Optional[str]]):
        if callable(key_resolver):
            self._resolver = key_resolver
        else:
            mapping = dict(key_resolver)

            def _resolver(did: str) -> Optional[str]:
                return mapping.get(did)

            self._resolver = _resolver

    def verify(self, credential: CapabilityCredential) -> bool:
        public_key = self._resolver(credential.issuer)
        if not public_key:
            raise KeyError(f"Unknown issuer DID: {credential.issuer}")

        payload = {
            "@context": "echo.capability",
            "issuer": credential.issuer,
            "subject": credential.subject,
            "capabilities": list(credential.capabilities),
            "nonce": credential.nonce,
            "issued_at": credential.issued_at,
            "expires_at": credential.expires_at,
            "constraints": dict(credential.constraints),
        }
        VerifyKey(base64.b64decode(public_key)).verify(
            _canonical_json(payload), _decode_signature(credential.signature)
        )
        if credential.expires_at:
            expiry = datetime.fromisoformat(credential.expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expiry:
                raise ValueError("Capability credential expired")
        return True


# ---------------------------------------------------------------------------
# Proof-of-integrity + encrypted memory
# ---------------------------------------------------------------------------


def _default_shell_path() -> Path:
    return Path(__file__).resolve().parents[2] / "echoshell.py"


class EchoShellIntegrityVerifier:
    """Tracks allowed hashes for the EchoShell entry point."""

    def __init__(
        self,
        *,
        shell_path: Path | None = None,
        manifest_path: Path | None = None,
    ) -> None:
        self._shell_path = Path(shell_path or _default_shell_path())
        self._manifest = self._load_manifest(manifest_path)

    @staticmethod
    def _load_manifest(manifest_path: Path | None) -> Mapping[str, Any]:
        candidate = manifest_path
        if candidate is None:
            try:
                candidate = resources.files(__package__).joinpath("echoshell_integrity_manifest.json")
            except FileNotFoundError:
                candidate = None
        if candidate and Path(candidate).exists():
            with open(candidate, "r", encoding="utf-8") as handle:
                return json.load(handle)
        return {"artifact": str(_default_shell_path()), "measurements": []}

    def measure(self) -> str:
        data = self._shell_path.read_bytes()
        return hashlib.sha256(data).hexdigest()

    def allowed_measurements(self) -> Sequence[Mapping[str, Any]]:
        return tuple(self._manifest.get("measurements", []))

    def status(self) -> Dict[str, Any]:
        measurement = self.measure()
        allowed = {entry.get("sha256") for entry in self.allowed_measurements()}
        matching = [entry for entry in self.allowed_measurements() if entry.get("sha256") == measurement]
        return {
            "path": str(self._shell_path),
            "measurement": measurement,
            "allowed": measurement in allowed,
            "labels": [entry.get("label") for entry in matching],
        }


class EncryptedMemoryContainer:
    """Ephemeral encrypted-memory container backed by AES-GCM."""

    def __init__(self, *, key: bytes | None = None) -> None:
        self._key = key or os.urandom(32)

    @property
    def key_b64(self) -> str:
        return base64.b64encode(self._key).decode("ascii")

    def seal(self, payload: bytes | str) -> str:
        data = payload if isinstance(payload, bytes) else payload.encode("utf-8")
        nonce = os.urandom(12)
        cipher = AESGCM(self._key)
        ciphertext = cipher.encrypt(nonce, data, None)
        token = base64.b64encode(nonce + ciphertext).decode("ascii")
        return token

    def open(self, token: str) -> bytes:
        blob = base64.b64decode(token.encode("ascii"))
        nonce, ciphertext = blob[:12], blob[12:]
        cipher = AESGCM(self._key)
        plaintext = bytearray(cipher.decrypt(nonce, ciphertext, None))
        try:
            return bytes(plaintext)
        finally:
            for i in range(len(plaintext)):
                plaintext[i] = 0


class StealthCommandChannel:
    """Carries encrypted commands disguised as telemetry envelopes."""

    def __init__(self, *, container: EncryptedMemoryContainer | None = None, topic: str = "telemetry") -> None:
        self._container = container or EncryptedMemoryContainer()
        self._topic = topic

    @property
    def shared_secret(self) -> str:
        return self._container.key_b64

    @property
    def topic(self) -> str:
        return self._topic

    def encode(self, command: str, *, hint: str = "node-health", metadata: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
        envelope = {
            "topic": self._topic,
            "hint": hint,
            "issued_at": _utc_now(),
            "payload": self._container.seal(command),
        }
        if metadata:
            envelope["metadata"] = dict(metadata)
        return envelope

    def decode(self, envelope: Mapping[str, Any]) -> str:
        token = envelope.get("payload")
        if not isinstance(token, str):
            raise ValueError("Envelope missing payload")
        payload = self._container.open(token)
        return payload.decode("utf-8")


# ---------------------------------------------------------------------------
# Recursive proof pipeline + self-attesting upgrades
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProofNode:
    claim_id: str
    statement: str
    commitment: str
    parent_commitment: Optional[str]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "commitment": self.commitment,
            "parent": self.parent_commitment,
            "metadata": dict(self.metadata),
        }


class RecursiveProofPipeline:
    """Builds chained commitments to simulate recursive ZK proofs."""

    def __init__(self, *, domain: str) -> None:
        self._domain = domain.encode("utf-8")
        self._nodes: List[ProofNode] = []

    def append(self, claim_id: str, statement: str, witness: Mapping[str, Any]) -> ProofNode:
        parent = self._nodes[-1].commitment if self._nodes else None
        witness_hash = _sha256(_canonical_json(witness)).hex()
        hasher = hashlib.sha256()
        hasher.update(self._domain)
        hasher.update(statement.encode("utf-8"))
        hasher.update(witness_hash.encode("ascii"))
        if parent:
            hasher.update(parent.encode("ascii"))
        commitment = hasher.hexdigest()
        node = ProofNode(
            claim_id=claim_id,
            statement=statement,
            commitment=commitment,
            parent_commitment=parent,
            metadata={"witness_hash": witness_hash, "timestamp": _utc_now()},
        )
        self._nodes.append(node)
        return node

    def verify_chain(self) -> bool:
        parent = None
        for node in self._nodes:
            hasher = hashlib.sha256()
            hasher.update(self._domain)
            hasher.update(node.statement.encode("utf-8"))
            witness_hash = node.metadata.get("witness_hash")
            if not isinstance(witness_hash, str):
                return False
            hasher.update(witness_hash.encode("ascii"))
            if parent:
                hasher.update(parent.encode("ascii"))
            if hasher.hexdigest() != node.commitment:
                return False
            parent = node.commitment
        return True

    def snapshot(self, limit: int = 6) -> Mapping[str, Any]:
        return {
            "depth": len(self._nodes),
            "latest_commitment": self._nodes[-1].commitment if self._nodes else None,
            "verified": self.verify_chain(),
            "recent_claims": [node.to_dict() for node in self._nodes[-limit:]],
        }


@dataclass
class SelfAttestingUpgrade:
    upgrade_id: str
    component: str
    description: str
    artifact_digest: str
    issuer: str
    issued_at: str
    signature: str

    @classmethod
    def create(
        cls,
        *,
        component: str,
        description: str,
        artifact_path: Path,
        issuer_did: str,
        vault: EncryptedIdentityVault,
    ) -> "SelfAttestingUpgrade":
        data = artifact_path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        payload = {
            "upgrade_id": f"upgrade:{component}:{int(time.time())}",
            "component": component,
            "description": description,
            "artifact_digest": digest,
            "issuer": issuer_did,
            "issued_at": _utc_now(),
        }
        signature = _encode_signature(vault.sign(issuer_did, _canonical_json(payload)))
        return cls(signature=signature, **payload)

    def verify(self, public_key_b64: str) -> bool:
        payload = {
            "upgrade_id": self.upgrade_id,
            "component": self.component,
            "description": self.description,
            "artifact_digest": self.artifact_digest,
            "issuer": self.issuer,
            "issued_at": self.issued_at,
        }
        VerifyKey(base64.b64decode(public_key_b64)).verify(
            _canonical_json(payload), _decode_signature(self.signature)
        )
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "upgrade_id": self.upgrade_id,
            "component": self.component,
            "description": self.description,
            "artifact_digest": self.artifact_digest,
            "issuer": self.issuer,
            "issued_at": self.issued_at,
            "signature": self.signature,
        }


# ---------------------------------------------------------------------------
# ZK Attestation layer + Sovereign identity surface
# ---------------------------------------------------------------------------


class ZKAttestationLayer:
    """Composes selective disclosure, capability creds, and proofs."""

    def __init__(
        self,
        vault: EncryptedIdentityVault,
        *,
        shell_path: Path | None = None,
        manifest_path: Path | None = None,
    ) -> None:
        self._vault = vault
        self._disclosures: deque[SelectiveDisclosureProof] = deque(maxlen=16)
        self._capability_factory = CapabilityCredentialFactory(vault)
        self._recent_capabilities: deque[CapabilityCredential] = deque(maxlen=8)
        self._proofs = RecursiveProofPipeline(domain="echo.zk-attestation")
        self._upgrades: deque[SelfAttestingUpgrade] = deque(maxlen=4)
        self._shell = EchoShellIntegrityVerifier(shell_path=shell_path, manifest_path=manifest_path)

    def selective_disclosure(self, claims: Mapping[str, Any], reveal: Iterable[str]) -> SelectiveDisclosureProof:
        tree = MerkleSelectiveDisclosure(claims)
        proof = tree.prove(reveal)
        if not proof.disclosed:
            raise ValueError("No claims disclosed")
        self._disclosures.append(proof)
        self._proofs.append(
            claim_id=f"disclosure:{proof.root}",
            statement="selective_disclosure",
            witness={"disclosed_keys": sorted(proof.disclosed)},
        )
        return proof

    def issue_capability(
        self,
        *,
        issuer_did: str,
        subject_did: str,
        capabilities: Sequence[str],
        constraints: Optional[Mapping[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> CapabilityCredential:
        credential = self._capability_factory.issue(
            issuer_did=issuer_did,
            subject_did=subject_did,
            capabilities=capabilities,
            constraints=constraints,
            expires_at=expires_at,
        )
        self._recent_capabilities.append(credential)
        self._proofs.append(
            claim_id=f"capability:{credential.nonce}",
            statement="capability-issued",
            witness={"issuer": issuer_did, "subject": subject_did, "caps": list(capabilities)},
        )
        return credential

    def record_shell_integrity(self) -> ProofNode:
        status = self._shell.status()
        node = self._proofs.append(
            claim_id=f"echoshell:{status['measurement']}",
            statement="echoshell-integrity",
            witness=status,
        )
        return node

    def self_attest_upgrade(
        self,
        *,
        component: str,
        description: str,
        artifact_path: Path,
        issuer_did: str,
    ) -> SelfAttestingUpgrade:
        upgrade = SelfAttestingUpgrade.create(
            component=component,
            description=description,
            artifact_path=artifact_path,
            issuer_did=issuer_did,
            vault=self._vault,
        )
        self._upgrades.append(upgrade)
        self._proofs.append(
            claim_id=upgrade.upgrade_id,
            statement="self-attesting-upgrade",
            witness={"component": upgrade.component, "digest": upgrade.artifact_digest},
        )
        return upgrade

    def snapshot(self) -> Mapping[str, Any]:
        return {
            "disclosures": [proof.to_payload() for proof in self._disclosures],
            "capabilities": [credential.summary() for credential in self._recent_capabilities],
            "proof_pipeline": self._proofs.snapshot(),
            "shell_integrity": self._shell.status(),
            "upgrades": [upgrade.to_dict() for upgrade in self._upgrades],
        }


class SovereignIdentityLayer:
    """High-level facade implementing the sovereign ZK attestation layer."""

    def __init__(
        self,
        vault: EncryptedIdentityVault,
        *,
        shell_path: Path | None = None,
        manifest_path: Path | None = None,
        command_topic: str = "telemetry",
    ) -> None:
        self._vault = vault
        self._zk = ZKAttestationLayer(vault, shell_path=shell_path, manifest_path=manifest_path)
        self._stealth_channel = StealthCommandChannel(topic=command_topic)

    @property
    def shared_command_secret(self) -> str:
        return self._stealth_channel.shared_secret

    def selective_disclosure(self, claims: Mapping[str, Any], reveal: Iterable[str]) -> SelectiveDisclosureProof:
        return self._zk.selective_disclosure(claims, reveal)

    def issue_capability(
        self,
        *,
        issuer_did: str,
        subject_did: str,
        capabilities: Sequence[str],
        constraints: Optional[Mapping[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> CapabilityCredential:
        return self._zk.issue_capability(
            issuer_did=issuer_did,
            subject_did=subject_did,
            capabilities=capabilities,
            constraints=constraints,
            expires_at=expires_at,
        )

    def record_shell_integrity(self) -> ProofNode:
        return self._zk.record_shell_integrity()

    def self_attest_upgrade(
        self,
        *,
        component: str,
        description: str,
        artifact_path: Path,
        issuer_did: str,
    ) -> SelfAttestingUpgrade:
        return self._zk.self_attest_upgrade(
            component=component,
            description=description,
            artifact_path=artifact_path,
            issuer_did=issuer_did,
        )

    def encode_command(self, command: str, *, hint: str = "node-health", metadata: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
        return self._stealth_channel.encode(command, hint=hint, metadata=metadata)

    def decode_command(self, envelope: Mapping[str, Any]) -> str:
        return self._stealth_channel.decode(envelope)

    def snapshot(self) -> Mapping[str, Any]:
        state = self._zk.snapshot()
        state["stealth_channel"] = {"topic": self._stealth_channel.topic, "secret": self.shared_command_secret}
        return state


__all__ = [
    "CapabilityCredential",
    "CapabilityCredentialFactory",
    "CapabilityVerifier",
    "EchoShellIntegrityVerifier",
    "EncryptedMemoryContainer",
    "MerkleSelectiveDisclosure",
    "ProofNode",
    "RecursiveProofPipeline",
    "SelectiveDisclosureProof",
    "SelfAttestingUpgrade",
    "SovereignIdentityLayer",
    "StealthCommandChannel",
    "ZKAttestationLayer",
]
