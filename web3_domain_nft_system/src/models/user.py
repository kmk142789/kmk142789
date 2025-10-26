"""Database model for application users."""

from __future__ import annotations

from . import db


class User(db.Model):
    """Simple user record used by the demo API."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - for debugging
        return f"<User {self.username}>"

    def to_dict(self) -> dict[str, str | int]:
        """Serialise the model into a JSON friendly dictionary."""

        return {"id": self.id, "username": self.username, "email": self.email}


__all__ = ["User"]
