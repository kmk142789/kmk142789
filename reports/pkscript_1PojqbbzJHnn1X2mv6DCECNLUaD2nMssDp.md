# Puzzle #168 P2PKH Reconstruction

Puzzle #168 publishes the standard pay-to-public-key-hash (P2PKH) locking
script together with a Base58Check address whose middle section has been
suppressed:

```
1PojqbbzJ-aD2nMssDp
Pkscript
OP_DUP
OP_HASH160
fa29a9264b9c18fa5925e38d201934ed89e64dd6
OP_EQUALVERIFY
OP_CHECKSIG
```

The five-opcode template matches the legacy `OP_DUP OP_HASH160 <20-byte hash>
OP_EQUALVERIFY OP_CHECKSIG` structure.  To recover the missing characters we
prefix the HASH160 digest with the mainnet version byte (`0x00`), append the
double-SHA256 checksum, and encode the 25-byte result with the Base58 alphabet
while preserving any leading zero bytes as `1` characters.

## Address recovery

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

payload = bytes.fromhex("00" + "fa29a9264b9c18fa5925e38d201934ed89e64dd6")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = b58encode(payload + checksum)
print(address)  # 1PojqbbzJHnn1X2mv6DCECNLUaD2nMssDp
```

Running the snippet restores the redacted segment (`Hnn1X2mv6DCECNLUa`) and
confirms that the script encodes the canonical P2PKH output for Puzzle #168.
