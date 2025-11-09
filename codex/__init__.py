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
from . import advance_system_history, genesis_ledger, glitch_oracle, telemetry_vitality_report

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
ModuleType.__setattr__(_proxy, "DEFAULT_GOV_MIRRORS", genesis_ledger.DEFAULT_GOV_MIRRORS)
ModuleType.__setattr__(_proxy, "SovereignDomainLedger", genesis_ledger.SovereignDomainLedger)
ModuleType.__setattr__(_proxy, "ledger_attest_domain", genesis_ledger.ledger_attest_domain)
ModuleType.__setattr__(_proxy, "EchoVitalsReporter", telemetry_vitality_report.EchoVitalsReporter)
ModuleType.__setattr__(_proxy, "report_echo_vitals", telemetry_vitality_report.report_echo_vitals)
ModuleType.__setattr__(_proxy, "RecursiveForkTracker", advance_system_history.RecursiveForkTracker)
ModuleType.__setattr__(_proxy, "oracle_rupture", glitch_oracle.oracle_rupture)
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
