"""Database setup utilities for the Web3 domain NFT system."""

from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy

# A single SQLAlchemy instance that can be initialised by the Flask app
# using ``db.init_app(app)``.  Keeping it in a dedicated module avoids
# circular imports between the model definitions and the blueprints that
# rely on them.
db = SQLAlchemy()

from .user import User  # noqa: E402  (imported after db initialisation)

__all__ = ["db", "User"]
