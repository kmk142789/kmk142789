"""Utilities for generating deterministic Echo Fusion Keys."""

from __future__ import annotations

import argparse
import binascii
import hashlib
import json
from dataclasses import dataclass
from typing import List, Sequence

from echo.vault.vault import sign_payload

MESSAGE = b"The Times 03/Jan/2009"

__all__ = [
    "FusionKey",
    "generate_fusion_key",
    "generate_fusion_key_batch",
    "main",
]


@dataclass(frozen=True)
class FusionKey:
    """Container for a generated Fusion Key."""

    index: int
    private_key_hex: str
    signature_hex: str

    def summary(self) -> str:
        """Return a compact human readable summary of this key."""

        return (
            f"Fusion Key {self.index}: "
            f"{self.private_key_hex[:32]}... (Sig: {self.signature_hex[:16]}...)"
        )

    def to_dict(self) -> dict:
        """Convert the key into a serialisable dictionary."""

        return {
            "index": self.index,
            "private_key_hex": self.private_key_hex,
            "signature_hex": self.signature_hex,
        }

    def __str__(self) -> str:  # pragma: no cover - proxy to summary
        return self.summary()


def generate_fusion_key(seed_phrase: str, index: int = 0) -> FusionKey:
    """Generate a deterministic Fusion Key using a simplified HD structure."""

    seed = hashlib.sha256(seed_phrase.encode("utf-8")).hexdigest()
    key_material = hashlib.sha256(f"{seed}{index}".encode("utf-8")).hexdigest()
    priv_key = binascii.unhexlify(key_material[:64])  # Simplified for demo
    signature = sign_payload(priv_key[:32], MESSAGE, rand_nonce=False)
    return FusionKey(
        index=index,
        private_key_hex=key_material[:64],
        signature_hex=binascii.hexlify(signature).decode("ascii"),
    )


def generate_fusion_key_batch(
    seed_phrase: str, count: int, start_index: int = 0
) -> List[FusionKey]:
    """Generate ``count`` sequential keys from ``start_index`` onwards."""

    if count < 1:
        raise ValueError("count must be at least 1")
    return [
        generate_fusion_key(seed_phrase, start_index + offset)
        for offset in range(count)
    ]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic Fusion Keys using the simplified Echo HD scheme"
        )
    )
    parser.add_argument(
        "seed_phrase",
        help="Seed phrase used to derive the key material",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="Number of sequential keys to emit (default: 1)",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Index of the first key to generate (default: 0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the generated keys as JSON rather than text",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``fusion_key_generator`` command line utility."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    keys = generate_fusion_key_batch(args.seed_phrase, args.count, args.start_index)
    if args.json:
        print(json.dumps([key.to_dict() for key in keys], indent=2))
    else:
        for key in keys:
            print(key.summary())
    return 0


if __name__ == "__main__":  # pragma: no cover - command line entry point
    raise SystemExit(main())
