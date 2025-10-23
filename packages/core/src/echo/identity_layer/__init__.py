"""Secure, persistent identity layer primitives."""

from .vault import EncryptedIdentityVault, VaultEvent

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
]
