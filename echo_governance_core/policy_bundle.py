"""Policy bundle builder and verifier with signing support."""

from __future__ import annotations

import json
import hmac
from hashlib import sha256
from pathlib import Path

from .key_rotation import get_key_bundle

POLICY_DIR = Path("policies")
BUNDLE_FILE = "policy_bundle_index.json"


def _hash_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fp:
        h.update(fp.read())
    return h.hexdigest()


def build_bundle(master_secret: str) -> dict:
    """Build a signed bundle of policy file hashes."""

    bundle: dict[str, object] = {"policies": {}}
    for p in POLICY_DIR.glob("*.yaml"):
        bundle["policies"][p.name] = _hash_file(p)

    signing_key = get_key_bundle(master_secret)["current"]
    payload = json.dumps(bundle, sort_keys=True).encode("utf-8")
    sig = hmac.new(signing_key.encode("utf-8"), payload, sha256).hexdigest()
    bundle["signature"] = sig
    return bundle


def write_bundle(master_secret: str) -> None:
    """Generate and persist the signed bundle index file."""

    bundle = build_bundle(master_secret)
    with open(BUNDLE_FILE, "w", encoding="utf-8") as fp:
        json.dump(bundle, fp, indent=2)


def verify_bundle(master_secret: str) -> bool:
    """Verify the current bundle file against known signing keys."""

    with open(BUNDLE_FILE, encoding="utf-8") as fp:
        bundle = json.load(fp)
    sig = bundle.pop("signature")
    signing_keys = get_key_bundle(master_secret)
    payload = json.dumps(bundle, sort_keys=True).encode("utf-8")

    for candidate in [signing_keys["current"]] + signing_keys["previous"]:
        calc = hmac.new(candidate.encode("utf-8"), payload, sha256).hexdigest()
        if hmac.compare_digest(calc, sig):
            return True
    return False


__all__ = ["build_bundle", "write_bundle", "verify_bundle", "BUNDLE_FILE", "POLICY_DIR"]
