"""Public interface for the Echo Codex package.

This module proxies the historical :mod:`packages.core.src.codex` module while
exposing new registry tooling under the ``codex`` namespace.
"""
from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType
from typing import Any

from . import registry_builder

_core = import_module("packages.core.src.codex")

__all__ = sorted(
    set(getattr(_core, "__all__", ()))
    | {
        "PullRequestRecord",
        "build_registry_manifest",
        "fetch_merged_pull_requests",
        "generate_markdown",
        "registry_builder",
    }
)


class _ProxyModule(ModuleType):
    __slots__ = ()

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - passthrough proxy
        return getattr(_core, name)

    def __dir__(self) -> list[str]:  # pragma: no cover - passthrough proxy
        return sorted(set(super().__dir__()) | set(dir(_core)))

    def __setattr__(self, name: str, value: Any) -> None:  # pragma: no cover
        if name in self.__dict__:
            super().__setattr__(name, value)
        else:
            setattr(_core, name, value)

    def __delattr__(self, name: str) -> None:  # pragma: no cover
        if name in self.__dict__:
            super().__delattr__(name)
        else:
            delattr(_core, name)


_proxy = _ProxyModule(__name__)
ModuleType.__setattr__(_proxy, "__doc__", __doc__)
ModuleType.__setattr__(_proxy, "__all__", __all__)
ModuleType.__setattr__(_proxy, "__package__", __package__)
ModuleType.__setattr__(_proxy, "__spec__", __spec__)
ModuleType.__setattr__(_proxy, "__file__", __file__)
ModuleType.__setattr__(_proxy, "__path__", __path__)

ModuleType.__setattr__(_proxy, "registry_builder", registry_builder)
ModuleType.__setattr__(
    _proxy, "PullRequestRecord", registry_builder.PullRequestRecord
)
ModuleType.__setattr__(
    _proxy, "build_registry_manifest", registry_builder.build_registry_manifest
)
ModuleType.__setattr__(
    _proxy,
    "fetch_merged_pull_requests",
    registry_builder.fetch_merged_pull_requests,
)
ModuleType.__setattr__(
    _proxy, "generate_markdown", registry_builder.generate_markdown
)

sys.modules[__name__] = _proxy
