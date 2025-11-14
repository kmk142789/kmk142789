"""Minimal BIP32 extended key parsing utilities.

The historic JavaScript tooling in the ecosystem supported a wide range of
coin-specific version bytes (Bitcoin, Litecoin, Dogecoin, Monacoin, Kumacoin
and their respective test networks).  Several verification routines inside
this repository only need to *parse* an extended key rather than derive new
children, so this module focuses on robust decoding and validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .base58 import Base58Error, b58check_decode


class ExtendedKeyError(ValueError):
    """Raised when an extended key cannot be decoded or validated."""


@dataclass(frozen=True)
class VersionInfo:
    version: int
    coin: str
    network: str
    is_private: bool


_VERSION_TABLE: Dict[int, VersionInfo] = {
    0x0488B21E: VersionInfo(0x0488B21E, "bitcoin", "mainnet", False),
    0x0488ADE4: VersionInfo(0x0488ADE4, "bitcoin", "mainnet", True),
    0x043587CF: VersionInfo(0x043587CF, "bitcoin", "testnet", False),
    0x04358394: VersionInfo(0x04358394, "bitcoin", "testnet", True),
    0x02FACAFD: VersionInfo(0x02FACAFD, "dogecoin", "mainnet", False),
    0x02FAC398: VersionInfo(0x02FAC398, "dogecoin", "mainnet", True),
    0x0432A9A8: VersionInfo(0x0432A9A8, "dogecoin", "testnet", False),
    0x0432A243: VersionInfo(0x0432A243, "dogecoin", "testnet", True),
    0x019DA462: VersionInfo(0x019DA462, "litecoin", "mainnet", False),
    0x019D9CFE: VersionInfo(0x019D9CFE, "litecoin", "mainnet", True),
    0x0436F6E1: VersionInfo(0x0436F6E1, "litecoin", "testnet", False),
    0x0436EF7D: VersionInfo(0x0436EF7D, "litecoin", "testnet", True),
    0x01B04071: VersionInfo(0x01B04071, "monacoin", "mainnet", False),
    0x01B040F5: VersionInfo(0x01B040F5, "monacoin", "mainnet", True),
    0x0434C85B: VersionInfo(0x0434C85B, "monacoin", "testnet", False),
    0x0434C8E0: VersionInfo(0x0434C8E0, "monacoin", "testnet", True),
    0x01864F84: VersionInfo(0x01864F84, "kumacoin", "mainnet", False),
    0x01865009: VersionInfo(0x01865009, "kumacoin", "mainnet", True),
    0x04346C97: VersionInfo(0x04346C97, "kumacoin", "testnet", False),
    0x04346D1B: VersionInfo(0x04346D1B, "kumacoin", "testnet", True),
}


def _parse_version(raw: bytes) -> VersionInfo:
    version = int.from_bytes(raw, byteorder="big")
    try:
        return _VERSION_TABLE[version]
    except KeyError as exc:  # pragma: no cover - KeyError message is enough
        raise ExtendedKeyError(f"Unknown extended key version 0x{version:08X}") from exc


@dataclass(frozen=True)
class ExtendedKey:
    """Container for decoded extended key metadata."""

    version_info: VersionInfo
    depth: int
    parent_fingerprint: bytes
    child_index: int
    chain_code: bytes
    key_bytes: bytes

    @classmethod
    def from_string(cls, encoded: str) -> "ExtendedKey":
        try:
            payload = b58check_decode(encoded)
        except Base58Error as exc:  # pragma: no cover - error message propagated
            raise ExtendedKeyError(str(exc)) from exc

        if len(payload) != 78:
            raise ExtendedKeyError("Extended keys must be 78 bytes after decoding")

        version_info = _parse_version(payload[:4])
        depth = payload[4]
        parent_fingerprint = payload[5:9]
        child_index = int.from_bytes(payload[9:13], byteorder="big")
        chain_code = payload[13:45]
        key_data = payload[45:]

        if version_info.is_private:
            if key_data[0] != 0:
                raise ExtendedKeyError("Private extended keys must be padded with 0x00")
            key_bytes = key_data[1:]
        else:
            if key_data[0] not in (2, 3):
                raise ExtendedKeyError("Public extended keys must contain a compressed point")
            key_bytes = key_data

        return cls(
            version_info=version_info,
            depth=depth,
            parent_fingerprint=parent_fingerprint,
            child_index=child_index,
            chain_code=chain_code,
            key_bytes=key_bytes,
        )

    @property
    def is_private(self) -> bool:
        return self.version_info.is_private

    @property
    def fingerprint_hex(self) -> str:
        return self.parent_fingerprint.hex()

    @property
    def key_hex(self) -> str:
        return self.key_bytes.hex()

    def describe(self) -> Tuple[str, str, bool]:
        """Return a tuple describing the coin, network, and key class."""

        return (self.version_info.coin, self.version_info.network, self.version_info.is_private)


__all__ = ["ExtendedKey", "ExtendedKeyError", "VersionInfo"]
