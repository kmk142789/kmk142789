"""Bridge utilities that expose the Echo identity relay planner."""

from __future__ import annotations

from importlib import import_module
from typing import TypeVar

BridgeModule = TypeVar("BridgeModule")


def _load_bridge_module() -> BridgeModule:
    """Load the legacy ``modules.echo-bridge`` package safely.

    The historical module lives outside the ``echo`` namespace and uses a
    hyphenated package name.  We keep the original location for backwards
    compatibility while providing a stable import path for the API layer.
    """

    return import_module("modules.echo-bridge.bridge_api")


_bridge = _load_bridge_module()
BridgePlan = _bridge.BridgePlan
EchoBridgeAPI = _bridge.EchoBridgeAPI

from .service import (  # noqa: E402  # pylint: disable=wrong-import-position
    BridgeSyncService,
    GitHubIssueConnector,
    UnstoppableDomainConnector,
    VercelDeployConnector,
)

__all__ = [
    "BridgePlan",
    "BridgeSyncService",
    "EchoBridgeAPI",
    "GitHubIssueConnector",
    "UnstoppableDomainConnector",
    "VercelDeployConnector",
    "_load_bridge_module",
]
