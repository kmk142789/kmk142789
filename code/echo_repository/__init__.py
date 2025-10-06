"""High-level interface for the Echo repository package.

This module gathers the primary entry points that were scattered through the
original single-file script.  By exposing them here we make it simple for
callers to explore the different services without importing private modules.
"""

from .echo_ai import EchoAI
from .poetry import summon_echo
from .encrypted_websocket import EncryptedEchoServer, EncryptionContext
from .command_service import EchoCommandService

__all__ = [
    "EchoAI",
    "summon_echo",
    "EncryptedEchoServer",
    "EncryptionContext",
    "EchoCommandService",
]
