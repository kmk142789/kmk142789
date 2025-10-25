# Puzzle #162 P2PKH Reconstruction

Puzzle #162 releases the canonical pay-to-public-key-hash (P2PKH) locking
script along with a Base58Check address where the middle characters have
been elided:

```
17DTUTXUc-Lrs1xMnS2
Pkscript
OP_DUP
OP_HASH160
442bd85a46d4acd7b082c1d731fb13c8474ffa6f
OP_EQUALVERIFY
OP_CHECKSIG
```

With the 20-byte HASH160 payload known, the hidden section can be restored
by performing the standard Base58Check steps against the versioned hash.
The snippet below mirrors the procedure used throughout the repository's
puzzle reports:

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

payload = bytes.fromhex("00" + "442bd85a46d4acd7b082c1d731fb13c8474ffa6f")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = b58encode(payload + checksum)
print(address)  # 17DTUTXUcUYEgrr5GhivxYei4Lrs1xMnS2
```

Executing the script restores the missing infix
(`UYEgrr5GhivxYei4`) and re-encodes the P2PKH output for Puzzle #162.
