"""Route blueprints for the Web3 domain NFT system."""

from .crypto_handler import crypto_bp, SecureKeyHandler
from .user import user_bp

__all__ = ["crypto_bp", "SecureKeyHandler", "user_bp"]
