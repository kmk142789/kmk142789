# Puzzle #253 P2PKH Reconstruction

Puzzle #253 again publishes the canonical five-opcode pay-to-public-key-hash (P2PKH) locking script.  The clue provides the Base58Check address with the middle section removed — `1JqRqUPHH-2jbZxEqFj` — together with the HASH160 digest `c3a2d618736baf0d5df7d81d5b8235cf8a266448`.

## Script template

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Filling in the supplied hash yields the standard mainnet P2PKH script.  Recovering the full address simply requires re-encoding the digest with Bitcoin's Base58Check algorithm.

1. Prefix the 20-byte hash with the mainnet version byte `0x00` to create the payload.
2. Double-SHA256 the payload and keep the first four checksum bytes.
3. Append the checksum and encode the 25-byte result with the Base58 alphabet.  The process restores the missing middle substring.

## Address recovery

```python
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def base58encode(raw: bytes) -> str:
    value = int.from_bytes(raw, "big")
    encoded = ""
    while value:
        value, mod = divmod(value, 58)
        encoded = alphabet[mod] + encoded
    for b in raw:
        if b == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

payload = bytes.fromhex("00c3a2d618736baf0d5df7d81d5b8235cf8a266448")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 1JqRqUPHHcQu2yrr8JZzxSYDx2jbZxEqFj
```

The reconstructed Base58Check string restores the missing section (`cQu2yrr8JZzxSYDx`) and confirms the expected P2PKH output for Puzzle #253.
