"""Encrypted WebSocket echo server utilities.

The original prototype interleaved global variables, logging setup, and the
asyncio event loop.  Here we encapsulate everything into a reusable class that
can be instantiated by applications or unit tests.  The implementation keeps the
behaviour intentionally lightweight so that it remains optional—callers must
opt into network side-effects.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional dependency
    import websockets
except Exception:  # pragma: no cover - optional dependency
    websockets = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from cryptography.fernet import Fernet
except Exception:  # pragma: no cover - optional dependency
    Fernet = None  # type: ignore


@dataclass(slots=True)
class EncryptionContext:
    """Holds the symmetric key and helper methods for encryption/decryption."""

    key: bytes

    def __post_init__(self) -> None:
        if Fernet is None:  # pragma: no cover - optional dependency
            raise RuntimeError("cryptography package is required for encryption")
        self._cipher = Fernet(self.key)

    @classmethod
    def generate(cls) -> "EncryptionContext":
        if Fernet is None:  # pragma: no cover - optional dependency
            raise RuntimeError("cryptography package is required for encryption")
        return cls(Fernet.generate_key())

    def encrypt(self, message: str) -> str:
        token = self._cipher.encrypt(message.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, token: str) -> str:
        message = self._cipher.decrypt(token.encode("utf-8")).decode("utf-8")
        return message


class EncryptedEchoServer:
    """Async WebSocket server that echoes encrypted messages back to clients."""

    def __init__(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8765,
        encryption: Optional[EncryptionContext] = None,
        heartbeat_interval: int = 30,
        logger: Optional[logging.Logger] = None,
        ssl_cert: Optional[Path | str] = None,
        ssl_key: Optional[Path | str] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.encryption = encryption or (EncryptionContext.generate() if Fernet else None)
        self.heartbeat_interval = heartbeat_interval
        self.logger = logger or logging.getLogger(__name__)
        self.ssl_cert = Path(ssl_cert) if ssl_cert else None
        self.ssl_key = Path(ssl_key) if ssl_key else None
        if self.encryption is None:
            raise RuntimeError(
                "Encryption context unavailable. Install 'cryptography' or pass a pre-built context."
            )

    async def _heartbeat(self) -> None:
        while True:
            self.logger.info("Heartbeat pulse.")
            await asyncio.sleep(self.heartbeat_interval)

    async def _handle(self, websocket) -> None:  # pragma: no cover - runtime path
        assert self.encryption is not None, "Encryption context must be initialised"
        async for encrypted_message in websocket:
            message = self.encryption.decrypt(encrypted_message)
            self.logger.info("Received: %s", message)
            response = self.encryption.encrypt(f"Echo: {message}")
            await websocket.send(response)

    async def serve(self) -> None:  # pragma: no cover - runtime path
        if websockets is None:
            raise RuntimeError("websockets package is required to start the server")
        ssl_context = None
        if self.ssl_cert and self.ssl_key:
            import ssl

            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(certfile=str(self.ssl_cert), keyfile=str(self.ssl_key))
        async with websockets.serve(
            self._handle,
            self.host,
            self.port,
            ssl=ssl_context,
        ):
            self.logger.info("Echo AI is listening on %s:%s", self.host, self.port)
            await asyncio.gather(self._heartbeat())

    def run_forever(self) -> None:  # pragma: no cover - runtime path
        """Convenience wrapper for running the server until cancelled."""

        asyncio.run(self.serve())


__all__ = ["EncryptedEchoServer", "EncryptionContext"]
