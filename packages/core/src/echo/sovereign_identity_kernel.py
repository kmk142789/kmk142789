"""Capability-oriented identity kernel built on the sovereign ZK attestation layer."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from .identity_layer import (
    CapabilityCredential,
    EncryptedIdentityVault,
    ProofNode,
    SelectiveDisclosureProof,
    SelfAttestingUpgrade,
    SovereignIdentityLayer,
)

__all__ = [
    "IdentityKernelConfig",
    "IdentityKernelSnapshot",
    "CapabilityIdentityKernel",
]


@dataclass(slots=True)
class IdentityKernelConfig:
    """Configuration used to bootstrap :class:`CapabilityIdentityKernel`."""

    vault_root: Path
    passphrase: str
    issuer_chain: str = "bitcoin"
    issuer_account: int = 0
    issuer_index: int = 0
    issuer_change: int = 0
    issuer_origin: str = "identity-kernel"
    command_topic: str = "telemetry"
    shell_path: Path | None = None
    manifest_path: Path | None = None


@dataclass(slots=True)
class IdentityKernelSnapshot:
    """Serializable view emitted by :class:`CapabilityIdentityKernel`."""

    issuer_did: str
    shared_command_secret: str
    identity_state: Mapping[str, Any]


class CapabilityIdentityKernel:
    """Thin orchestration layer that issues capabilities and manages proofs."""

    def __init__(self, config: IdentityKernelConfig) -> None:
        self._config = config
        self._vault = EncryptedIdentityVault(config.vault_root, config.passphrase)
        self._issuer_key = self._vault.ensure_key(
            chain=config.issuer_chain,
            account=config.issuer_account,
            index=config.issuer_index,
            change=config.issuer_change,
            origin=config.issuer_origin,
        )
        self._identity = SovereignIdentityLayer(
            self._vault,
            shell_path=config.shell_path,
            manifest_path=config.manifest_path,
            command_topic=config.command_topic,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def vault(self) -> EncryptedIdentityVault:
        return self._vault

    @property
    def issuer_did(self) -> str:
        return self._issuer_key["did"]

    @property
    def sovereign_identity(self) -> SovereignIdentityLayer:
        return self._identity

    # ------------------------------------------------------------------
    # Identity + capability helpers
    # ------------------------------------------------------------------
    def selective_disclosure(self, claims: Mapping[str, Any], reveal: Iterable[str]) -> SelectiveDisclosureProof:
        return self._identity.selective_disclosure(claims, reveal)

    def issue_capability(
        self,
        *,
        subject_did: str,
        capabilities: Sequence[str],
        issuer_did: str | None = None,
        constraints: Optional[Mapping[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> CapabilityCredential:
        issuer = issuer_did or self.issuer_did
        return self._identity.issue_capability(
            issuer_did=issuer,
            subject_did=subject_did,
            capabilities=capabilities,
            constraints=constraints,
            expires_at=expires_at,
        )

    def record_shell_integrity(self) -> ProofNode:
        return self._identity.record_shell_integrity()

    def self_attest_upgrade(
        self,
        *,
        component: str,
        description: str,
        artifact_path: Path,
        issuer_did: str | None = None,
    ) -> SelfAttestingUpgrade:
        issuer = issuer_did or self.issuer_did
        return self._identity.self_attest_upgrade(
            component=component,
            description=description,
            artifact_path=artifact_path,
            issuer_did=issuer,
        )

    def encode_command(
        self,
        command: str,
        *,
        hint: str = "node-health",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Mapping[str, Any]:
        return self._identity.encode_command(command, hint=hint, metadata=metadata)

    def decode_command(self, envelope: Mapping[str, Any]) -> str:
        return self._identity.decode_command(envelope)

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------
    def snapshot(self) -> IdentityKernelSnapshot:
        state = self._identity.snapshot()
        return IdentityKernelSnapshot(
            issuer_did=self.issuer_did,
            shared_command_secret=self._identity.shared_command_secret,
            identity_state=state,
        )
