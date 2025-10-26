"""Blueprint providing CRUD endpoints for :class:`~models.user.User`."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..models import db
from ..models.user import User

user_bp = Blueprint("user", __name__)


@user_bp.route("/users", methods=["GET"])
def get_users():
    """Return all users as a JSON array."""

    users = User.query.all()
    return jsonify([user.to_dict() for user in users])


@user_bp.route("/users", methods=["POST"])
def create_user():
    """Create a new user from the supplied JSON payload."""

    data = request.get_json(silent=True) or {}
    username = data.get("username")
    email = data.get("email")

    if not username or not email:
        return (
            jsonify({"error": "Both 'username' and 'email' are required."}),
            400,
        )

    user = User(username=username, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    """Fetch a single user by identifier."""

    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    """Update mutable fields on a user record."""

    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]

    db.session.commit()
    return jsonify(user.to_dict())


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int):
    """Remove a user from the database."""

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200


__all__ = ["user_bp"]
