#!/usr/bin/env python3
"""Echo PulseForge — create signed ``PulseCard`` snapshots of Echo state.

The original PulseForge script bundled with the repository shipped as a raw
prototype: it pulled a handful of JSON files, hashed them into a Merkle root
and attempted to sign the resulting payload using helper functions that no
longer exist in this refactored code base.  The idea is compelling but the
implementation was brittle, so this module rebuilds the feature with the same
spirit and a healthier architecture.

Highlights
~~~~~~~~~~
* **Deterministic canonicalisation** – every JSON file is normalised before it
  participates in the Merkle tree, ensuring reproducible roots.
* **Self-contained crypto** – a lightweight secp256k1 implementation derives
  child keys and creates deterministic ECDSA signatures without external
  dependencies.
* **Testable design** – core logic is encapsulated in the :class:`PulseForge`
  class which accepts dependency injections, making the behaviour easy to unit
  test.

The resulting PulseCard documents the Merkle root of the Echo state files, the
derived key metadata and the signature required to verify authenticity.  By
default the command line interface saves PulseCards into ``./pulsecards``.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Sequence, Tuple

ASCII_BADGE = r"""
  ____      _                _____      _           _
 |  _ \ ___| | ___  ___ ___ |  ___|   _| |__   __ _| |_ ___  _ __
 | |_) / _ \ |/ _ \/ __/ __|| |_ | | | | '_ \ / _` | __/ _ \| '__|
 |  __/  __/ |  __/\__ \__ \|  _|| |_| | |_) | (_| | || (_) | |
 |_|   \___|_|\___||___/___/|_|   \__,_|_.__/ \__,_|\__\___/|_|
"""

# ---------------------------------------------------------------------------
# Helper data classes
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class StateEntry:
    """Summary data for a single state file."""

    label: str
    path: Path
    present: bool
    hash_hex: Optional[str]
    size_bytes: int


@dataclass(slots=True)
class PulseSignature:
    """Representation of the deterministic ECDSA signature."""

    algorithm: str
    signature: str
    public_key: str


# ---------------------------------------------------------------------------
# Canonicalisation helpers
# ---------------------------------------------------------------------------


def _sha256_bytes(data: bytes) -> bytes:
    return sha256(data).digest()


def _sha256_hex(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _read_json(path: Path) -> Optional[object]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _merkle_root(leaves: Sequence[bytes]) -> str:
    if not leaves:
        return "0" * 64
    level = list(leaves)
    while len(level) > 1:
        nxt: List[bytes] = []
        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1] if index + 1 < len(level) else left
            nxt.append(_sha256_bytes(left + right))
        level = nxt
    return level[0].hex()


# ---------------------------------------------------------------------------
# Minimal secp256k1 helpers
# ---------------------------------------------------------------------------

_SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_SECP256K1_G = (
    55066263022277343669578718895168534326250603453777594175500187360389116729240,
    32670510020758816978083085130507043184471273380659243275938904335757337482424,
)


def _inverse_mod(value: int, modulus: int) -> int:
    return pow(value, -1, modulus)


def _point_add(
    point_a: Optional[Tuple[int, int]], point_b: Optional[Tuple[int, int]]
) -> Optional[Tuple[int, int]]:
    if point_a is None:
        return point_b
    if point_b is None:
        return point_a
    if point_a[0] == point_b[0] and (point_a[1] + point_b[1]) % _SECP256K1_P == 0:
        return None
    if point_a == point_b:
        slope = (3 * point_a[0] * point_a[0]) * _inverse_mod(2 * point_a[1], _SECP256K1_P)
    else:
        slope = (point_b[1] - point_a[1]) * _inverse_mod(point_b[0] - point_a[0], _SECP256K1_P)
    slope %= _SECP256K1_P
    x_r = (slope * slope - point_a[0] - point_b[0]) % _SECP256K1_P
    y_r = (slope * (point_a[0] - x_r) - point_a[1]) % _SECP256K1_P
    return x_r, y_r


def _scalar_multiply(k: int, point: Tuple[int, int]) -> Optional[Tuple[int, int]]:
    result: Optional[Tuple[int, int]] = None
    addend: Optional[Tuple[int, int]] = point
    while k:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def _derive_public_key(priv_hex: str) -> bytes:
    secret = int(priv_hex, 16)
    if not (1 <= secret < _SECP256K1_N):
        raise ValueError("Private key out of range for secp256k1")
    point = _scalar_multiply(secret, _SECP256K1_G)
    if point is None:
        raise ValueError("Failed to derive public key")
    x, y = point
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")


def _sign_payload(priv_hex: str, payload: str) -> PulseSignature:
    priv_int = int(priv_hex, 16)
    if not (1 <= priv_int < _SECP256K1_N):
        raise ValueError("Invalid private key")

    payload_hash = int.from_bytes(sha256(payload.encode("utf-8")).digest(), "big")
    k_material = sha256((priv_hex + payload).encode("utf-8")).digest()
    k = int.from_bytes(k_material, "big") % _SECP256K1_N
    if k == 0:
        k = 1

    point_r = _scalar_multiply(k, _SECP256K1_G)
    if point_r is None:
        raise ValueError("Failed to compute curve point for signature")
    r = point_r[0] % _SECP256K1_N
    if r == 0:
        raise ValueError("Invalid signature parameter r=0")

    s = _inverse_mod(k, _SECP256K1_N) * (payload_hash + r * priv_int)
    s %= _SECP256K1_N
    if s == 0:
        raise ValueError("Invalid signature parameter s=0")

    if s > _SECP256K1_N // 2:
        s = _SECP256K1_N - s

    signature_bytes = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    public_key = _derive_public_key(priv_hex)
    return PulseSignature(
        algorithm="secp256k1+sha256",
        signature=signature_bytes.hex(),
        public_key=public_key.hex(),
    )


# ---------------------------------------------------------------------------
# Core forge implementation
# ---------------------------------------------------------------------------


class PulseForge:
    """Utility for assembling PulseCards from a collection of state files."""

    def __init__(
        self,
        *,
        root_dir: Optional[Path | str] = None,
        state_files: Optional[Sequence[Tuple[str, Path]]] = None,
        output_dir: Optional[Path | str] = None,
    ) -> None:
        self.root_dir = Path(root_dir) if root_dir is not None else Path.cwd()
        self.output_dir = (
            Path(output_dir)
            if output_dir is not None
            else self.root_dir / "pulsecards"
        )
        default_state_files: List[Tuple[str, Path]] = [
            ("anchor", self.root_dir / "anchor_vessel.json"),
            ("blood", self.root_dir / "blood_memory_vault.json"),
            ("wildfire", self.root_dir / "wildfire_continuum.json"),
            ("braid", self.root_dir / ".echo" / "braid.json"),
        ]
        self.state_files = list(state_files) if state_files is not None else default_state_files

    # ------------------------------------------------------------------
    # State gathering and Merkle root construction
    # ------------------------------------------------------------------
    def gather_state(self) -> Tuple[str, Mapping[str, StateEntry]]:
        leaves: List[bytes] = []
        metadata: dict[str, StateEntry] = {}
        for label, path in self.state_files:
            data = _read_json(path)
            if data is not None:
                canonical = _canonical_json(data)
                encoded = canonical.encode("utf-8")
                leaves.append(_sha256_bytes(encoded))
                entry = StateEntry(
                    label=label,
                    path=path,
                    present=True,
                    hash_hex=_sha256_hex(canonical),
                    size_bytes=len(encoded),
                )
            else:
                entry = StateEntry(
                    label=label,
                    path=path,
                    present=False,
                    hash_hex=None,
                    size_bytes=0,
                )
            metadata[label] = entry
        return _merkle_root(leaves), metadata

    # ------------------------------------------------------------------
    # Signing and persistence
    # ------------------------------------------------------------------
    def build_payload(
        self,
        root_hex: str,
        *,
        namespace: str,
        index: int,
        pub_hint: str,
    ) -> str:
        issued_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        nonce = os.urandom(8).hex()
        return "\n".join(
            [
                "PulseCard/v1",
                f"merkle_root={root_hex}",
                f"namespace={namespace}",
                f"index={index}",
                f"issued_at={issued_at}",
                f"pub_hint={pub_hint}",
                f"nonce={nonce}",
            ]
        )

    def forge(
        self,
        *,
        private_key_hex: str,
        namespace: str = "pulse",
        index: int = 0,
        pub_hint: Optional[str] = None,
        testnet: bool = False,
    ) -> Path:
        root_hex, meta = self.gather_state()
        derived_key = self.derive_child_key(private_key_hex, namespace, index)
        pub_key = _derive_public_key(derived_key).hex()
        hint = pub_hint or pub_key[:16]

        payload = self.build_payload(root_hex, namespace=namespace, index=index, pub_hint=hint)
        signature = _sign_payload(derived_key, payload)

        timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        card = {
            "type": "PulseCard/v1",
            "root": root_hex,
            "namespace": namespace,
            "index": index,
            "issued_at": payload.splitlines()[4].split("=")[1],
            "pub_hint": hint,
            "signature": {
                "algorithm": signature.algorithm,
                "signature": signature.signature,
                "public_key": signature.public_key,
            },
            "derived_preview": {
                "pubkey_prefix": pub_key[:16],
                "network": "testnet" if testnet else "mainnet",
            },
            "state_meta": {
                label: {
                    "present": entry.present,
                    "path": str(entry.path.relative_to(self.root_dir))
                    if entry.path.is_absolute()
                    else str(entry.path),
                    "hash": entry.hash_hex,
                    "size_bytes": entry.size_bytes,
                }
                for label, entry in meta.items()
            },
        }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"pulse_{timestamp}.json"
        output_path.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
        return output_path

    # ------------------------------------------------------------------
    # Key derivation helpers
    # ------------------------------------------------------------------
    def derive_child_key(self, parent_hex: str, namespace: str, index: int) -> str:
        parent_int = int(parent_hex, 16)
        if not (1 <= parent_int < _SECP256K1_N):
            raise ValueError("Parent private key is invalid")

        material = f"{parent_hex}:{namespace}:{index}".encode("utf-8")
        child_int = int.from_bytes(sha256(material).digest(), "big") % _SECP256K1_N
        child_int = (child_int + parent_int) % _SECP256K1_N
        if child_int == 0:
            child_int = 1
        return f"{child_int:064x}"


# ---------------------------------------------------------------------------
# Command line interface
# ---------------------------------------------------------------------------


def _read_key_from_file(path: Path) -> str:
    content = path.read_text(encoding="utf-8").strip()
    return content


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Echo PulseForge (PulseCard/v1)")
    key_group = parser.add_mutually_exclusive_group(required=True)
    key_group.add_argument("--priv-hex", help="secp256k1 private key in hex")
    key_group.add_argument("--key-file", type=Path, help="path to file containing hex key")
    parser.add_argument("--ns", default="pulse", help="derivation namespace")
    parser.add_argument("--index", type=int, default=0, help="derivation index")
    parser.add_argument("--pub-hint", default=None, help="optional public hint")
    parser.add_argument("--testnet", action="store_true", help="mark derived preview as testnet")
    args = parser.parse_args(list(argv) if argv is not None else None)

    print(ASCII_BADGE)

    if args.priv_hex:
        parent_key = args.priv_hex.strip().lower()
    else:
        parent_key = _read_key_from_file(args.key_file).strip().lower()

    forge = PulseForge(root_dir=Path.cwd())
    output = forge.forge(
        private_key_hex=parent_key,
        namespace=args.ns,
        index=args.index,
        pub_hint=args.pub_hint,
        testnet=args.testnet,
    )

    print(f"[✓] PulseCard written: {output.relative_to(Path.cwd())}")
    print("    Share this card publicly; it contains no private material.")
    return 0


if __name__ == "__main__":  # pragma: no cover - command line entry point
    raise SystemExit(main())
