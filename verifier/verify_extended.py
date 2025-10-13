#!/usr/bin/env python3
"""Verify address <-> pubkey consistency (P2PKH + simple bech32 support)."""

from __future__ import annotations

import binascii
import hashlib
import re
import sys

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58_decode(s: str) -> bytes:
    n = 0
    for ch in s:
        n = n * 58 + B58.index(ch)
    b = n.to_bytes((n.bit_length() + 7) // 8, "big") or b"\0"
    return b"\x00" * (len(s) - len(s.lstrip("1"))) + b


def address_to_hash160(addr: str) -> bytes:
    if addr.lower().startswith(("bc1", "tb1", "bcrt1")):
        # minimal witness program extraction (P2WPKH only)
        data = addr.split("1", 1)[1]
        cs = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
        vals = [cs.index(c) for c in data]
        acc = 0
        bits = 0
        out = []
        for v in vals:
            acc = (acc << 5) | v
            bits += 5
            if bits >= 8:
                bits -= 8
                out.append((acc >> bits) & 255)
        # search 20-byte window
        for i in range(max(0, len(out) - 20) + 1):
            chunk = bytes(out[i : i + 20])
            if len(chunk) == 20:
                return chunk
        raise ValueError("bech32 not P2WPKH")
    dec = base58_decode(addr)
    return dec[1:21]


def pubkey_to_hash160(pubhex: str) -> bytes:
    pub = binascii.unhexlify(pubhex)
    return hashlib.new("ripemd160", hashlib.sha256(pub).digest()).digest()


def normalize(h: str) -> str:
    h = h.strip().lower()
    while h.startswith("00") and len(h) > 66:
        h = h[2:]
    return h


def try_forms(pubhex: str) -> list[str]:
    p = normalize(pubhex)
    try:
        raw = binascii.unhexlify(p)
    except Exception:
        return []
    cands = [p]
    if raw and raw[0] == 4 and len(raw) == 65:
        x = raw[1:33]
        y = raw[33:]
        prefix = "03" if (int.from_bytes(y, "big") % 2) else "02"
        cands.append(prefix + x.hex())
    return cands


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: verify_extended.py dataset.csv")
    total = passed = 0
    fails: list[tuple[int, str, str]] = []
    with open(sys.argv[1], encoding="utf-8", errors="replace") as handle:
        for ln, line in enumerate(handle, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            total += 1
            try:
                addr, pubhex = re.split(r",\s*", line, maxsplit=1)
                h160 = address_to_hash160(addr)
                ok = False
                for cand in try_forms(pubhex):
                    if pubkey_to_hash160(cand) == h160:
                        ok = True
                        break
                if ok:
                    passed += 1
                else:
                    fails.append((ln, addr, "no match"))
            except Exception as exc:
                fails.append((ln, line, str(exc)))
    print(f"Total: {total} | Passed: {passed} | Failed: {len(fails)}")
    for fail in fails[:25]:
        print("FAIL:", fail)


if __name__ == "__main__":
    main()
