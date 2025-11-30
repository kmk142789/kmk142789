"""Policy bundle builder and verifier with signing support."""

from __future__ import annotations

import json
import hmac
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, List

from .key_rotation import get_key_bundle

POLICY_DIR = Path("policies")
BUNDLE_FILE = "policy_bundle_index.json"
MODULAR_DIR = POLICY_DIR / "modules"


def _hash_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fp:
        h.update(fp.read())
    return h.hexdigest()


def _iter_policy_files() -> Iterable[Path]:
    """Yield all modular policy files in a stable order."""

    yield from sorted(POLICY_DIR.glob("*.yaml"))
    if MODULAR_DIR.exists():
        for path in sorted(MODULAR_DIR.rglob("*.yaml")):
            yield path


def _assemble_modular_entries() -> Dict[str, List[dict]]:
    """Collect policy fragments grouped by module name."""

    modules: Dict[str, List[dict]] = {}
    for path in _iter_policy_files():
        rel = path.relative_to(POLICY_DIR)
        module = rel.parts[0] if len(rel.parts) > 1 else "root"
        modules.setdefault(module, []).append({"file": str(rel), "hash": _hash_file(path)})
    return modules


def build_bundle(master_secret: str) -> dict:
    """Build a signed bundle of policy file hashes, including modular sources."""

    bundle: dict[str, object] = {
        "modules": _assemble_modular_entries(),
    }

    signing_key = get_key_bundle(master_secret)["current"]
    payload = json.dumps(bundle, sort_keys=True).encode("utf-8")
    sig = hmac.new(signing_key.encode("utf-8"), payload, sha256).hexdigest()
    bundle["signature"] = sig
    bundle["bundle_checksum"] = sha256(payload).hexdigest()
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
    sig = bundle.get("signature")
    signing_keys = get_key_bundle(master_secret)
    payload = json.dumps({k: v for k, v in bundle.items() if k != "signature"}, sort_keys=True).encode("utf-8")

    for candidate in [signing_keys["current"]] + signing_keys["previous"]:
        calc = hmac.new(candidate.encode("utf-8"), payload, sha256).hexdigest()
        if hmac.compare_digest(calc, sig):
            break
    else:
        return False

    for entries in bundle.get("modules", {}).values():
        for entry in entries:
            path = POLICY_DIR / entry["file"]
            if not path.exists():
                return False
            if entry.get("hash") != _hash_file(path):
                return False
    return True


def assemble_bundle(master_secret: str) -> dict:
    """Compile and persist a fresh bundle for consumers that need immediacy."""

    bundle = build_bundle(master_secret)
    with open(BUNDLE_FILE, "w", encoding="utf-8") as fp:
        json.dump(bundle, fp, indent=2)
    return bundle


__all__ = [
    "build_bundle",
    "write_bundle",
    "verify_bundle",
    "assemble_bundle",
    "BUNDLE_FILE",
    "POLICY_DIR",
    "MODULAR_DIR",
]
