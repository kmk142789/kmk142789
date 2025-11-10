"""Web3 Domain NFT System package."""

from __future__ import annotations

from .app import create_app
from .src.models import db
from .src.routes import (
    SecureKeyHandler,
    create_nft_blueprint,
    crypto_bp,
    nft_bp,
    user_bp,
)

__all__ = [
    "SecureKeyHandler",
    "create_app",
    "create_nft_blueprint",
    "crypto_bp",
    "db",
    "nft_bp",
    "user_bp",
]
