"""Secure, persistent identity layer primitives."""

from .service import IdentityService, IdentityLayerConfig
from .vault import EncryptedIdentityVault, VaultEvent

__all__ = [
    "EncryptedIdentityVault",
    "VaultEvent",
    "IdentityService",
    "IdentityLayerConfig",
]
