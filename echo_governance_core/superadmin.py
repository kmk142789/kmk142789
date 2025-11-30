"""Superadmin profile definition."""

SUPERADMIN = {
    "id": "josh.superadmin",
    "name": "Josh",
    "roles": ["superadmin"],
    "keys": {
        "signing": "superadmin_signing_key",
        "auth": "superadmin_auth_key",
    },
}

__all__ = ["SUPERADMIN"]
