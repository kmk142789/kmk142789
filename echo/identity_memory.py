"""Echo-facing facade for the cognitive harmonix identity & memory stack."""

from __future__ import annotations

from cognitive_harmonics.identity_memory import (
    IdentityDoc,
    IdentityKeys,
    IdentityManager,
    IdentityMemoryBundle,
    MemoryStore,
    SignResult,
    bootstrap_identity_memory,
    data_dir,
)

identity_memory_data_dir = data_dir

__all__ = [
    "IdentityDoc",
    "IdentityKeys",
    "IdentityManager",
    "IdentityMemoryBundle",
    "MemoryStore",
    "SignResult",
    "bootstrap_identity_memory",
    "data_dir",
    "identity_memory_data_dir",
]
