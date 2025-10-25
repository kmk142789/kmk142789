# Puzzle #99 P2PKH Reconstruction

Puzzle #99 publishes the usual five-opcode pay-to-public-key-hash (P2PKH)
locking script together with a hyphenated Base58Check address hint:

```
1JWnE6p6U-jFtuDWoNL
Pkscript
OP_DUP
OP_HASH160
c01bf430a97cbcdaedddba87ef4ea21c456cebdb
OP_EQUALVERIFY
OP_CHECKSIG
```

Because the HASH160 fingerprint is supplied, restoring the missing address
segment is a direct application of the Base58Check steps that govern all
legacy Bitcoin addresses:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte buffer and append the
   first four bytes.
3. Encode the resulting 25-byte value with the Bitcoin Base58 alphabet.

The short helper below mirrors the encoder used throughout the repository's
puzzle reports and reproduces the published clue:

```python
import hashlib

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(raw: bytes) -> str:
    value = int.from_bytes(raw, "big")
    encoded = ""
    while value:
        value, mod = divmod(value, 58)
        encoded = ALPHABET[mod] + encoded
    for byte in raw:
        if byte == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

payload = bytes.fromhex("00" + "c01bf430a97cbcdaedddba87ef4ea21c456cebdb")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = b58encode(payload + checksum)
print(address)  # 1JWnE6p6UN7ZJBN7TtcbNDoRcjFtuDWoNL
```

Executing the snippet fills in the missing `N7ZJBN7TtcbNDoRc` infix and
re-encodes the P2PKH output for Puzzle #99.  The reconstructed destination
matches the authoritative dataset entry recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).
