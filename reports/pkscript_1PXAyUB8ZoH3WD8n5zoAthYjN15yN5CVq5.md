# Puzzle #125 P2PKH Reconstruction

Puzzle #125 supplies the canonical five-opcode pay-to-public-key-hash (P2PKH)
locking script together with a Base58Check address whose interior glyphs are
suppressed:

```
1PXAyUB8Z-15yN5CVq5
Pkscript
OP_DUP
OP_HASH160
f7079256aa027dc437cbb539f955472416725fc8
OP_EQUALVERIFY
OP_CHECKSIG
```

The HASH160 payload allows the missing infix to be restored directly via the
standard Base58Check procedure.  The helper below mirrors the approach used
throughout the repository's earlier puzzle notes:

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

payload = bytes.fromhex("00" + "f7079256aa027dc437cbb539f955472416725fc8")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = b58encode(payload + checksum)
print(address)  # 1PXAyUB8ZoH3WD8n5zoAthYjN15yN5CVq5
```

Executing the snippet reproduces the hidden `oH3WD8n5zoAthYjN` segment and
reconstructs the full Puzzle #125 P2PKH address.
