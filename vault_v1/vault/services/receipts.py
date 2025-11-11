from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import json
import os

from jwcrypto import jwk, jws

from ..config import get_settings


def _load_signing_key() -> Optional[jwk.JWK]:
    key_env = os.getenv("VAULT_SIGNING_KEY")
    key_path: Optional[Path]
    if key_env:
        key_path = Path(key_env)
    else:
        key_path = get_settings().vault_signing_key
    if key_path and key_path.exists():
        return jwk.JWK.from_json(key_path.read_text())
    return None


def build_payload(cid: str, total_size: int, merkle_root: str, receipt_type: str) -> dict[str, Any]:
    return {
        "cid": cid,
        "total_size": total_size,
        "merkle_root": merkle_root,
        "receipt_type": receipt_type,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }


def sign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    key = _load_signing_key()
    if not key:
        return {"payload": payload, "signature": None}

    token = jws.JWS(json.dumps(payload).encode())
    token.add_signature(
        key,
        protected={"alg": "ES256", "typ": "JWT"},
    )
    return {"payload": payload, "signature": token.serialize(compact=True)}


__all__ = ["build_payload", "sign_payload"]
