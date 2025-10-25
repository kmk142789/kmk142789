# Puzzle #22 P2PKH Reconstruction

Puzzle #22 publishes a legacy pay-to-public-key-hash (P2PKH) locking script with an address where the middle section is redacted:

- Partial address: `1CfZWK1QT-KDjZzfNcv`
- HASH160 digest: `7ff45303774ef7a52fffd8011981034b258cb86b`

The script matches the standard five-opcode template:

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Encoding the provided HASH160 with the mainnet version byte (`0x00`) and Base58Check restores the missing characters. The recovery procedure mirrors the other Satoshi puzzle P2PKH reconstructions:

1. Prefix the 20-byte HASH160 with the version byte to build the payload.
2. Compute the four-byte checksum via double SHA-256.
3. Append the checksum and encode the 25-byte result using the Base58 alphabet, preserving leading zero bytes as `1` characters.

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

payload = bytes.fromhex("007ff45303774ef7a52fffd8011981034b258cb86b")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 1CfZWK1QTQE3eS9qn61dQjV89KDjZzfNcv
```

Executing the snippet restores the missing `QE3eS9qn61dQjV89` segment and matches the attested entry for Puzzle #22 in `satoshi/puzzle_solutions.json`, confirming the canonical P2PKH output.
