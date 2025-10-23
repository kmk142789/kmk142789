"""Encrypted, policy-aware key vault for Echo tooling."""

from .authority import load_authority_bindings
from .models import AuthorityBinding, VaultPolicy, VaultRecord
from .vault import Vault, open_vault

try:  # pragma: no cover - optional dependency is exercised via CLI tooling
    from .cli import vault_cli
except ModuleNotFoundError:  # ``rich`` is not available in the kata environment
    def vault_cli(*_args, **_kwargs):
        raise ModuleNotFoundError("vault_cli requires the 'rich' package")

__all__ = [
    "Vault",
    "VaultRecord",
    "VaultPolicy",
    "AuthorityBinding",
    "open_vault",
    "vault_cli",
    "load_authority_bindings",
]
