# Puzzle #163 P2PKH Reconstruction

Puzzle #163 once again presents the five-opcode pay-to-public-key-hash
(P2PKH) locking script together with a Base58Check address whose middle
section has been elided:

```
1H6e7SLxv-3cKBWJRmx
Pkscript
OP_DUP
OP_HASH160
b093122f7fb36d11c9f2c80cff2971fba7c9c1ff
OP_EQUALVERIFY
OP_CHECKSIG
```

With the HASH160 payload in hand, restoring the hidden infix is a direct
application of the Base58Check encoding steps.  The helper below mirrors
the routine used throughout the repository's puzzle reports:

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

payload = bytes.fromhex("00" + "b093122f7fb36d11c9f2c80cff2971fba7c9c1ff")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = b58encode(payload + checksum)
print(address)  # 1H6e7SLxv6ZUbuAaZpeUdVNfh3cKBWJRmx
```

Executing the snippet restores the missing `6ZUbuAaZpeUdVNfh` segment and
re-encodes the P2PKH output for Puzzle #163.
