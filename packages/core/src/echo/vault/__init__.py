"""Encrypted, policy-aware key vault for Echo tooling."""

from .authority import load_authority_bindings
from .models import AuthorityBinding, VaultPolicy, VaultRecord
from .vault import Vault, open_vault
from .cli import vault_cli

__all__ = [
    "Vault",
    "VaultRecord",
    "VaultPolicy",
    "AuthorityBinding",
    "open_vault",
    "vault_cli",
    "load_authority_bindings",
]
