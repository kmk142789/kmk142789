# Puzzle #45 P2PKH Reconstruction

Puzzle #45 publishes the familiar five-opcode pay-to-public-key-hash (P2PKH) locking script accompanied by a Base58Check address whose middle segment was removed:

- Partial address: `1NtiLNGeg-Ug4TW7bbk`
- HASH160 digest: `f0225bfc68a6e17e87cd8b5e60ae3be18f120753`

The script layout matches the canonical P2PKH template:

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Encoding the hash with the Bitcoin mainnet version byte (`0x00`) and Base58Check restores the missing characters.  The procedure follows the well-known three-step workflow:

1. Concatenate the version byte with the 20-byte HASH160 payload to form the 21-byte buffer.
2. Double-SHA256 hash the buffer and append the first four checksum bytes.
3. Base58 encode the 25-byte sequence, prepending `1` characters for any leading zero bytes.

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

payload = bytes.fromhex("00" + "f0225bfc68a6e17e87cd8b5e60ae3be18f120753")
print(base58check_encode(payload))
# 1NtiLNGegHWE3Mp9g2JPkgx6wUg4TW7bbk
```

Executing the script reconstructs the omitted substring (`HWE3Mp9g2JPkgx6w`) and matches the attested Puzzle #45 entry stored in `satoshi/puzzle-proofs/puzzle045.json`.
