"""Environment isolation helpers for the Atlas runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, MutableMapping


@dataclass
class SandboxEnvironment:
    """Controls the environment variables exposed to sandboxed code."""

    base: Mapping[str, str] = field(default_factory=lambda: dict(os.environ))
    allowed_variables: Iterable[str] = field(default_factory=list)
    overrides: MutableMapping[str, str] = field(default_factory=dict)

    def build(self) -> Dict[str, str]:
        env: Dict[str, str] = {}
        allowed = set(self.allowed_variables)
        for key, value in self.base.items():
            if not allowed or key in allowed:
                env[key] = value
        env.update(self.overrides)
        return env

    def set(self, key: str, value: str) -> None:
        self.overrides[key] = value

    def remove(self, key: str) -> None:
        self.overrides.pop(key, None)

    def merge(self, updates: Mapping[str, str]) -> None:
        for key, value in updates.items():
            self.overrides[key] = value


__all__ = ["SandboxEnvironment"]
