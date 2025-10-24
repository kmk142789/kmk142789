# Puzzle #94 P2PKH Reconstruction

The published locking script for Puzzle #94 shows the five-opcode template for a legacy pay-to-public-key-hash (P2PKH) output.  The puzzle statement provides both the Base58Check address with a missing middle segment — `1K6xGMUbs-6wjBWtNpL` — and the HASH160 payload `c6927a00970d0165327d0a6db7950f05720c295c`.

## Script template

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Substituting the supplied hash yields the standard mainnet P2PKH assembly.  Recovering the complete address only requires encoding the provided digest into the Base58 alphabet.

1. Prefix the 20-byte hash with the mainnet version byte `0x00` to form the 21-byte payload.
2. Double-SHA256 the payload and take the leading four checksum bytes.
3. Append the checksum and encode the resulting 25-byte sequence with Bitcoin's Base58 alphabet.  Each leading zero byte maps to the character `1`, which completes the missing middle segment.

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

payload = bytes.fromhex("00c6927a00970d0165327d0a6db7950f05720c295c")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 1K6xGMUbs6ZTXBnhw1pippqwK6wjBWtNpL
```

The reconstructed Base58Check string restores the missing section (`6ZTXBnhw1pippqwK`) and agrees with the dataset entry recorded in `satoshi/puzzle_solutions.json`, confirming the standard P2PKH script for Puzzle #94.
