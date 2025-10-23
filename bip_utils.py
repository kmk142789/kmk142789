"""Minimal subset of :mod:`bip_utils` required by the tests."""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass

_WORDS = [
    "echo",
    "bridge",
    "pulse",
    "atlas",
    "kaleidoscope",
    "harmony",
    "resonance",
    "quantum",
    "aurora",
    "stellar",
    "cosmic",
    "glyph",
    "oracle",
    "vault",
    "forge",
    "saga",
    "nexus",
    "lattice",
    "cipher",
    "signal",
    "dream",
    "weaver",
    "symphony",
    "ember",
]


class Bip39WordsNum:
    WORDS_NUM_24 = 24


class Bip39MnemonicGenerator:
    def FromWordsNumber(self, words_num: int) -> str:
        words = []
        for _ in range(words_num):
            entropy = os.urandom(2)
            idx = int.from_bytes(entropy, "big") % len(_WORDS)
            words.append(_WORDS[idx])
        return " ".join(words)


class Bip39SeedGenerator:
    def __init__(self, mnemonic: str) -> None:
        self._mnemonic = mnemonic

    def Generate(self) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", self._mnemonic.encode("utf-8"), b"bip-utils", 2048, dklen=32)


class Bip44Changes(int):
    pass


class _Coin(int):
    @property
    def value(self) -> int:
        return int(self)


class Bip44Coins:
    BITCOIN = _Coin(0)
    ETHEREUM = _Coin(60)
    LITECOIN = _Coin(2)
    DOGECOIN = _Coin(3)


class Bip44:
    def __init__(self, seed: bytes, coin: int) -> None:
        self._seed = seed
        self._coin = coin
        self._components: list[str] = []

    @classmethod
    def FromSeed(cls, seed: bytes, coin: _Coin) -> "Bip44":
        return cls(seed, int(coin))

    def Purpose(self) -> "Bip44":
        self._components.append("44'")
        return self

    def Coin(self) -> "Bip44":
        self._components.append(f"{self._coin}'")
        return self

    def Account(self, account: int) -> "Bip44":
        self._components.append(f"{int(account)}'")
        return self

    def Change(self, change: Bip44Changes) -> "Bip44":
        self._components.append(str(int(change)))
        return self

    def AddressIndex(self, index: int) -> "_Bip44Address":
        components = self._components + [str(int(index))]
        return _Bip44Address(self._seed, components)


@dataclass
class _KeyMaterial:
    data: bytes

    def RawCompressed(self) -> "_KeyMaterial":
        return self

    def Raw(self) -> "_KeyMaterial":
        return self

    def ToBytes(self) -> bytes:
        return self.data

    def ToExtended(self) -> str:
        return base64.b64encode(self.data).decode("ascii")


class _Bip44Address:
    def __init__(self, seed: bytes, components: list[str]) -> None:
        self._seed = seed
        self._components = components

    def _derive(self, flavour: bytes, length: int) -> bytes:
        payload = "/".join(self._components).encode("utf-8")
        digest = hashlib.sha256(flavour + self._seed + payload).digest()
        while len(digest) < length:
            digest += hashlib.sha256(digest).digest()
        return digest[:length]

    def PublicKey(self) -> _KeyMaterial:
        data = self._derive(b"pub", 33)
        return _KeyMaterial(data=data)

    def PrivateKey(self) -> _KeyMaterial:
        data = self._derive(b"prv", 32)
        return _KeyMaterial(data=data)


__all__ = [
    "Bip39MnemonicGenerator",
    "Bip39SeedGenerator",
    "Bip39WordsNum",
    "Bip44",
    "Bip44Changes",
    "Bip44Coins",
]
