# Puzzle #40 P2PKH Reconstruction

Puzzle #40 exposes a legacy pay-to-public-key-hash (P2PKH) locking script that pairs with an address whose middle section was intentionally removed:

- Partial address: `1EeAxcprB-WuxyiNEFv`
- HASH160 digest: `95a156cd21b4a69de969eb6716864f4c8b82a82a`

The assembly follows the standard five-opcode P2PKH template:

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Encoding the 20-byte hash with the mainnet version byte (`0x00`) and Base58Check restores the missing characters.  The recovery steps mirror every other P2PKH reconstruction:

1. Prefix the HASH160 value with the version byte to form the payload.
2. Double-SHA256 hash the payload and keep the first four bytes as the checksum.
3. Append the checksum, then Base58 encode the 25-byte sequence, preserving any leading zeros as `1` characters.

## Address recovery

```python
import hashlib

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def base58check_encode(payload: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    value = int.from_bytes(payload + checksum, "big")
    encoded = ""
    while value:
        value, mod = divmod(value, 58)
        encoded = ALPHABET[mod] + encoded
    for byte in payload + checksum:
        if byte == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded

payload = bytes.fromhex("00" + "95a156cd21b4a69de969eb6716864f4c8b82a82a")
print(base58check_encode(payload))
# 1EeAxcprB2PpCnr34VfZdFrkUWuxyiNEFv
```

Running the script reconstructs the omitted substring (`2PpCnr34VfZdFrkU`) and matches the attested Puzzle #40 entry stored in `satoshi/puzzle-proofs/puzzle040.json`.
