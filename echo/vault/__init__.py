"""Encrypted, policy-aware key vault for Echo tooling."""

from .models import VaultPolicy, VaultRecord
from .vault import Vault, open_vault
from .cli import vault_cli

__all__ = [
    "Vault",
    "VaultRecord",
    "VaultPolicy",
    "open_vault",
    "vault_cli",
]
