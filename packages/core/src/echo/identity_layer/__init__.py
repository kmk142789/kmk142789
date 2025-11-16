"""Secure, persistent identity layer primitives."""

from .vault import EncryptedIdentityVault, VaultEvent
from .verifiable_credentials import (
    CredentialIssuer,
    CredentialVerificationError,
    verify_credential,
)
from .trust_fabric import (
    CrossJurisdictionTrustFabric,
    TrustEntity,
    TrustLink,
)
from .zk_attestation_layer import (
    CapabilityCredential,
    CapabilityCredentialFactory,
    CapabilityVerifier,
    EchoShellIntegrityVerifier,
    EncryptedMemoryContainer,
    MerkleSelectiveDisclosure,
    ProofNode,
    RecursiveProofPipeline,
    SelectiveDisclosureProof,
    SelfAttestingUpgrade,
    SovereignIdentityLayer,
    StealthCommandChannel,
    ZKAttestationLayer,
)

try:  # pragma: no cover - optional gRPC dependency not shipped in kata runtime
    from .service import IdentityLayerConfig, IdentityService
except ModuleNotFoundError:
    IdentityLayerConfig = None  # type: ignore[assignment]
    IdentityService = None  # type: ignore[assignment]

__all__ = [
    "EncryptedIdentityVault",
    "VaultEvent",
    "IdentityService",
    "IdentityLayerConfig",
    "CredentialIssuer",
    "CredentialVerificationError",
    "verify_credential",
    "CrossJurisdictionTrustFabric",
    "TrustEntity",
    "TrustLink",
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
