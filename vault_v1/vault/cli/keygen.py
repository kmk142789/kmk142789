from __future__ import annotations

from pathlib import Path

from jwcrypto import jwk


def generate_key(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    key = jwk.JWK.generate(kty="EC", crv="P-256")
    path.write_text(key.export(private_key=True))
    return path


__all__ = ["generate_key"]
