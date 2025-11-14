"""Helpers for decrypting Ethereum V3 keystore files.

The project occasionally receives keystore archives that need to be
inspected without pulling in the heavy ``eth_account`` dependency. This
module provides a lightweight, auditable implementation of the subset of
Web3's keystore logic that Echo relies on: PBKDF2/Scrypt key derivation,
AES-128-CTR decryption, and the MAC guard enforced by geth-style
keyfiles. When both ``pycryptodome`` and ``cryptography`` are unavailable
we raise a descriptive error so callers can install one explicitly
instead of silently failing mid-way through the decrypt.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

_AES_BACKEND: str | None = None
try:  # pragma: no cover - backend detection
    from Crypto.Cipher import AES as _AES

    _AES_BACKEND = "pycryptodome"
except Exception:  # pragma: no cover - backend detection
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        _AES_BACKEND = "cryptography"
    except Exception:  # pragma: no cover - backend detection
        _AES_BACKEND = None


class KeystoreDecryptError(RuntimeError):
    """Raised when the keystore cannot be decrypted."""


def _keccak_256(data: bytes) -> bytes:
    try:  # pragma: no cover - prefer eth-hash for accuracy
        from eth_hash.auto import keccak  # type: ignore

        return keccak(data)
    except Exception:  # pragma: no cover - fallback to pycryptodome
        try:
            from Crypto.Hash import keccak  # type: ignore

            h = keccak.new(digest_bits=256)
            h.update(data)
            return h.digest()
        except Exception:
            return hashlib.sha3_256(data).digest()


def _aes_128_ctr_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    if len(key) != 16:
        raise ValueError("AES-128 requires a 16-byte key")
    if len(iv) != 16:
        raise ValueError("aes-128-ctr IV must be 16 bytes")

    if _AES_BACKEND == "pycryptodome":
        counter = int.from_bytes(iv, "big")
        cipher = _AES.new(key, _AES.MODE_CTR, nonce=b"", initial_value=counter)
        return cipher.decrypt(ciphertext)
    if _AES_BACKEND == "cryptography":
        cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
    raise KeystoreDecryptError(
        "No AES backend available. Install 'pycryptodome' or 'cryptography'."
    )


def _derive_key(password: str, params: Mapping[str, Any], *, kdf: str) -> bytes:
    salt = binascii.unhexlify(params["salt"])
    dklen = int(params.get("dklen", 32))

    if kdf == "scrypt":
        n = int(params["n"])
        r = int(params["r"])
        p = int(params["p"])
        return hashlib.scrypt(password=password.encode(), salt=salt, n=n, r=r, p=p, dklen=dklen)

    if kdf == "pbkdf2":
        c = int(params["c"])
        prf = params.get("prf", "hmac-sha256")
        if prf.lower() != "hmac-sha256":
            raise ValueError(f"Unsupported PBKDF2 PRF: {prf}")
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, c, dklen=dklen)

    raise ValueError(f"Unsupported kdf: {kdf}")


def decrypt_keyfile_json(keyfile: Mapping[str, Any], password: str) -> bytes:
    """Return the raw 32-byte private key contained in ``keyfile``."""

    crypto = keyfile.get("crypto") or keyfile.get("Crypto")
    if not crypto:
        raise ValueError("Invalid keystore: missing 'crypto' block")

    kdf = crypto["kdf"]
    kdfparams = crypto["kdfparams"]
    derived_key = _derive_key(password, kdfparams, kdf=kdf)

    cipher = crypto["cipher"]
    if cipher != "aes-128-ctr":
        raise ValueError(f"Unsupported cipher: {cipher}")
    iv = binascii.unhexlify(crypto["cipherparams"]["iv"])
    ciphertext = binascii.unhexlify(crypto["ciphertext"])

    mac_expected = binascii.unhexlify(crypto["mac"])
    mac_actual = _keccak_256(derived_key[16:32] + ciphertext)
    if mac_actual != mac_expected:
        raise KeystoreDecryptError("MAC mismatch (wrong password?)")

    private_key = _aes_128_ctr_decrypt(derived_key[:16], iv, ciphertext)
    if len(private_key) != 32:
        raise KeystoreDecryptError(
            f"Decrypted payload must be 32 bytes, received {len(private_key)}"
        )
    return private_key


def decrypt_keyfile(path: str | Path, password: str) -> bytes:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return decrypt_keyfile_json(data, password)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Decrypt an Ethereum keystore and print the hex key.")
    parser.add_argument("--file", required=True, type=Path, help="Path to the keystore JSON file")
    parser.add_argument("--password", required=True, help="Password used to encrypt the keystore")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    private_key = decrypt_keyfile(args.file, args.password)
    print(private_key.hex())
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    raise SystemExit(main())
