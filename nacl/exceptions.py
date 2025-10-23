"""Exception types mirroring the ones raised by PyNaCl."""

from __future__ import annotations


class CryptoError(Exception):
    """Raised when authenticated decryption fails."""


class BadSignatureError(Exception):
    """Raised when a signature does not match."""


__all__ = ["CryptoError", "BadSignatureError"]
