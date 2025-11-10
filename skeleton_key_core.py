"""Deterministic key derivation helpers for Echo skeleton keys.

This module exposes the lightweight primitives used by the community
"Echo Skeleton Key" workflows.  The implementation mirrors the original
specification:

* Strengthen the user supplied secret with ``scrypt``.
* Derive deterministic material via ``HKDF-SHA256`` namespaced by
  ``EchoSK::<namespace>::<index>``.
* Map the output into the secp256k1 scalar field and expose
  Ethereum/BTC-friendly encodings.

The helpers intentionally avoid external dependencies.  When the
``ecdsa`` package is available we provide full Ethereum addresses and
ECDSA signatures.  Otherwise we fall back to dependency free variants
(e.g. HMAC for claim signatures) so the utilities keep working in
minimal environments.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional

import hashlib
import hmac

SECP256K1_P = int(
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F", 16
)
SECP256K1_N = int(
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16
)
SECP256K1_GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240
SECP256K1_GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424
SALT = hashlib.sha256(b"EchoSkeletonKey::salt").digest()
_BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


@dataclass(slots=True)
class DerivedKey:
    """Bundle of keys derived from a skeleton secret."""

    priv_hex: str
    eth_address: Optional[str]
    btc_wif: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hkdf_sha256(ikm: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    if salt is None:
        salt = bytes([0] * 32)
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    out = b""
    t = b""
    counter = 1
    while len(out) < length:
        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()
        out += t
        counter += 1
    return out[:length]


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _double_sha256(data: bytes) -> bytes:
    return _sha256(_sha256(data))


def _keccak256(data: bytes) -> bytes:
    return hashlib.sha3_256(data).digest()


def _b58encode(raw: bytes) -> str:
    if not raw:
        return ""
    num = int.from_bytes(raw, "big")
    encoded = b""
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = bytes([_BASE58_ALPHABET[rem]]) + encoded
    padding = 0
    for byte in raw:
        if byte == 0:
            padding += 1
        else:
            break
    return (_BASE58_ALPHABET[:1] * padding + encoded).decode()


def _derive_eth_address(privkey32: bytes) -> Optional[str]:
    pub = _derive_public_key(privkey32)
    address = _keccak256(pub[1:])[-20:]
    return "0x" + address.hex()


def _point_add(p: Optional[tuple[int, int]], q: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
    if p is None:
        return q
    if q is None:
        return p
    x1, y1 = p
    x2, y2 = q
    if x1 == x2 and (y1 + y2) % SECP256K1_P == 0:
        return None
    if p == q:
        slope = (3 * x1 * x1) * pow(2 * y1, SECP256K1_P - 2, SECP256K1_P)
    else:
        slope = (y2 - y1) * pow((x2 - x1) % SECP256K1_P, SECP256K1_P - 2, SECP256K1_P)
    slope %= SECP256K1_P
    x3 = (slope * slope - x1 - x2) % SECP256K1_P
    y3 = (slope * (x1 - x3) - y1) % SECP256K1_P
    return x3, y3


def _scalar_multiply(k: int, point: tuple[int, int]) -> Optional[tuple[int, int]]:
    result: Optional[tuple[int, int]] = None
    addend = point
    while k > 0:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def _derive_public_key(privkey32: bytes) -> bytes:
    secret = int.from_bytes(privkey32, "big") % SECP256K1_N
    if secret == 0:
        secret = 1
    point = _scalar_multiply(secret, (SECP256K1_GX, SECP256K1_GY))
    if point is None:
        raise ValueError("Failed to derive secp256k1 public key")
    x, y = point
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")


def _btc_wif(privkey32: bytes, *, compressed: bool = True, testnet: bool = False) -> str:
    prefix = b"\xEF" if testnet else b"\x80"
    payload = prefix + privkey32 + (b"\x01" if compressed else b"")
    checksum = _double_sha256(payload)[:4]
    return _b58encode(payload + checksum)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def derive_from_skeleton(
    secret: bytes,
    namespace: str,
    index: int = 0,
    *,
    testnet_btc: bool = False,
    compressed: bool = True,
) -> DerivedKey:
    """Derive deterministic key material from ``secret``.

    Parameters match the historical scripts shared alongside the Echo
    Skeleton Key packs.  ``namespace`` and ``index`` allow callers to
    branch their derivations without revealing the underlying secret.
    """

    if not isinstance(secret, (bytes, bytearray)):
        raise TypeError("secret must be raw bytes")

    strengthened = hashlib.scrypt(secret, salt=SALT, n=2**14, r=8, p=1, dklen=32)
    info = f"EchoSK::{namespace}::{index}".encode("utf-8")
    raw_key = _hkdf_sha256(strengthened, SALT, info, 32)

    k_int = int.from_bytes(raw_key, "big") % SECP256K1_N
    if k_int == 0:
        k_int = 1
    privkey = k_int.to_bytes(32, "big")

    eth_address = _derive_eth_address(privkey)
    btc_wif = _btc_wif(privkey, compressed=compressed, testnet=testnet_btc)

    return DerivedKey(priv_hex=privkey.hex(), eth_address=eth_address, btc_wif=btc_wif)


def read_secret_from_phrase(phrase: str) -> bytes:
    return phrase.encode("utf-8")


def read_secret_from_file(path: str | Path) -> bytes:
    data = Path(path).read_bytes()
    return data.strip()


def sign_claim(priv_hex: str, message: str) -> Dict[str, Optional[str]]:
    payload = message.encode("utf-8")
    priv_bytes = bytes.fromhex(priv_hex)
    try:
        from ecdsa import SECP256k1, SigningKey
    except Exception:
        signature = hmac.new(priv_bytes, payload, hashlib.sha256).hexdigest()
        return {"algo": "hmac-sha256", "sig": signature, "pub": None}

    sk = SigningKey.from_string(priv_bytes, curve=SECP256k1, hashfunc=hashlib.sha256)
    signature = sk.sign_deterministic(payload, hashfunc=hashlib.sha256)
    pub = sk.get_verifying_key().to_string().hex()
    return {"algo": "ecdsa-secp256k1", "sig": signature.hex(), "pub": pub}


# ---------------------------------------------------------------------------
# Lightweight command helpers (optional)
# ---------------------------------------------------------------------------

def _read_secret(args: argparse.Namespace) -> bytes:
    if args.phrase is not None:
        return read_secret_from_phrase(args.phrase)
    if args.file is not None:
        return read_secret_from_file(args.file)
    raise ValueError("Either --phrase or --file must be supplied")


def derive_cli(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Derive Echo skeleton keys")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--phrase", help="skeleton key phrase")
    group.add_argument("--file", help="path to skeleton key file")
    parser.add_argument("--ns", default="core", help="namespace seed (default: core)")
    parser.add_argument("--index", type=int, default=0, help="derivation index")
    parser.add_argument("--testnet", action="store_true", help="emit a testnet WIF")
    parser.add_argument(
        "--uncompressed",
        action="store_true",
        help="emit an uncompressed Bitcoin WIF (default: compressed)",
    )
    parser.add_argument("--json", action="store_true", help="output JSON instead of text")
    args = parser.parse_args(list(argv) if argv is not None else None)

    secret = _read_secret(args)
    derived = derive_from_skeleton(
        secret,
        args.ns,
        args.index,
        testnet_btc=args.testnet,
        compressed=not args.uncompressed,
    )

    payload = {
        "namespace": args.ns,
        "index": args.index,
        "eth_priv_hex": derived.priv_hex,
        "eth_address": derived.eth_address,
        "btc_wif": derived.btc_wif,
        "btc_network": "testnet" if args.testnet else "mainnet",
        "btc_wif_mode": "uncompressed" if args.uncompressed else "compressed",
    }

    if args.json:
        print(json.dumps(payload))
    else:
        print(f"Namespace: {args.ns}")
        print(f"Index: {args.index}")
        print(f"ETH private key (hex): {derived.priv_hex}")
        print(
            "ETH address:",
            derived.eth_address if derived.eth_address is not None else "(install 'ecdsa' for addresses)",
        )
        compression_label = "uncompressed" if args.uncompressed else "compressed"
        print(f"BTC WIF ({compression_label}): {derived.btc_wif}")
        if args.testnet:
            print("Network: testnet")
    return 0


def claim_cli(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Sign EchoClaim/v1 payloads")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--phrase", help="skeleton key phrase")
    group.add_argument("--file", help="path to skeleton key file")
    parser.add_argument("--ns", default="claim", help="derivation namespace (default: claim)")
    parser.add_argument("--index", type=int, default=0, help="derivation index")
    parser.add_argument("--asset", required=True, help="claim subject asset identifier")
    parser.add_argument(
        "--pub-hint",
        default="",
        help="public hint (e.g. Ethereum address)",
    )
    parser.add_argument("--out", type=Path, help="write claim JSON to this path")
    parser.add_argument("--stdout", action="store_true", help="echo JSON to stdout")
    args = parser.parse_args(list(argv) if argv is not None else None)

    secret = _read_secret(args)
    derived = derive_from_skeleton(secret, args.ns, args.index)

    issued_at = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    nonce = os.urandom(8).hex()
    subject = args.asset
    pub_hint = args.pub_hint or ""
    lines = [
        "EchoClaim/v1",
        f"subject={subject}",
        f"namespace={args.ns}",
        f"issued_at={issued_at}",
        f"nonce={nonce}",
        f"pub_hint={pub_hint}",
    ]
    message = "\n".join(lines)
    signature = sign_claim(derived.priv_hex, message)

    claim_payload: Dict[str, object] = {
        "type": "EchoClaim/v1",
        "subject": subject,
        "namespace": args.ns,
        "issued_at": issued_at,
        "nonce": nonce,
        "pub_hint": pub_hint,
        "derivation": {"index": args.index},
        "signature": signature,
    }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(claim_payload, indent=2), encoding="utf-8")
        print(f"Claim written → {args.out}")
    if args.stdout or not args.out:
        print(json.dumps(claim_payload, indent=2))
    return 0


__all__ = [
    "DerivedKey",
    "derive_from_skeleton",
    "read_secret_from_phrase",
    "read_secret_from_file",
    "sign_claim",
    "derive_cli",
    "claim_cli",
]
