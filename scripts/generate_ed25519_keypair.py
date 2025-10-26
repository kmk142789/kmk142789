"""Generate an Ed25519 keypair suitable for the lfs-vc-issuer service.

Usage:
    python scripts/generate_ed25519_keypair.py --out-dir keys

Outputs `issuer-ed25519-private.key`, `issuer-ed25519-public.key`, and a base64 seed string
that can be dropped into `VC_ISSUER_KEY_SEED`.
"""

from __future__ import annotations

import argparse
import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def generate_keypair() -> tuple[bytes, bytes, bytes]:
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    seed = base64.b64encode(private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ))

    return private_bytes, public_bytes, seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Ed25519 keypair")
    parser.add_argument("--out-dir", default=".", help="Directory to write key files")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    private_bytes, public_bytes, seed = generate_keypair()

    (out_dir / "issuer-ed25519-private.key").write_bytes(private_bytes)
    (out_dir / "issuer-ed25519-public.key").write_bytes(public_bytes)
    (out_dir / "issuer-ed25519-seed.b64").write_bytes(seed)

    print(f"Private key written to: {out_dir / 'issuer-ed25519-private.key'}")
    print(f"Public key written to:  {out_dir / 'issuer-ed25519-public.key'}")
    print(f"Seed (base64) stored in: {out_dir / 'issuer-ed25519-seed.b64'}")

    print("\nEnvironment variable suggestion:")
    print("VC_ISSUER_KEY_SEED=" + seed.decode())


if __name__ == "__main__":
    main()
