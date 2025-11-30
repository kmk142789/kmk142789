"""Signing key rotation utilities backed by the encrypted vault."""

from __future__ import annotations

import time
from hashlib import sha256

from .vault import load_vault, save_vault

ROTATION_PERIOD_SECONDS = 7 * 24 * 3600  # weekly


def _now() -> int:
    return int(time.time())


def get_key_bundle(master_secret: str) -> dict:
    """Fetch the signing key bundle, initializing it if missing."""

    vault = load_vault(master_secret)
    bundle = vault.get("signing_keys")
    if not bundle:
        seed = f"josh-superadmin-{_now()}"
        current_key = sha256(seed.encode("utf-8")).hexdigest()
        bundle = {
            "created_at": _now(),
            "current": current_key,
            "previous": [],
        }
        vault["signing_keys"] = bundle
        save_vault(vault, master_secret)
    return bundle


def rotate_if_needed(master_secret: str) -> str:
    """Rotate the current signing key if the rotation window has elapsed."""

    vault = load_vault(master_secret)
    bundle = get_key_bundle(master_secret)
    age = _now() - bundle["created_at"]

    if age < ROTATION_PERIOD_SECONDS:
        return bundle["current"]

    new_seed = f"josh-rotation-{_now()}-{bundle['current']}"
    new_key = sha256(new_seed.encode("utf-8")).hexdigest()

    bundle["previous"].append(bundle["current"])
    bundle["current"] = new_key
    bundle["created_at"] = _now()

    vault["signing_keys"] = bundle
    save_vault(vault, master_secret)
    return new_key


__all__ = ["get_key_bundle", "rotate_if_needed", "ROTATION_PERIOD_SECONDS"]
