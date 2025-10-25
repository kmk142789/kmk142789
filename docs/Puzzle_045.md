# Bitcoin Puzzle #45 — Restoring the Hidden Infix

Puzzle #45 in the Bitcoin puzzle catalogue reprises the canonical five-opcode pay-to-public-key-hash (P2PKH) locking script, but the broadcast address published with the clue omits its middle section:

```
1NtiLNGeg-Ug4TW7bbk
OP_DUP
OP_HASH160
f0225bfc68a6e17e87cd8b5e60ae3be18f120753
OP_EQUALVERIFY
OP_CHECKSIG
```

The recovery mirrors every other legacy P2PKH reconstruction:

1. Prefix the HASH160 payload with the Bitcoin mainnet version byte `0x00` to obtain the 21-byte Base58Check payload.
2. Double-SHA256 hash the payload and append the first four checksum bytes.
3. Base58 encode the resulting 25-byte buffer, preserving any leading zero bytes as `1` characters.

Carrying out these steps restores the removed substring and yields the full destination string:

- **Address:** `1NtiLNGegHWE3Mp9g2JPkgx6wUg4TW7bbk`
- **Missing infix:** `HWE3Mp9g2JPkgx6w`

The reconstructed result matches the authoritative dataset entry recorded in [`satoshi/puzzle-proofs/puzzle045.json`](../satoshi/puzzle-proofs/puzzle045.json).

To verify programmatically in Python:

```python
import hashlib

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

payload = bytes.fromhex("00" + "f0225bfc68a6e17e87cd8b5e60ae3be18f120753")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
encoded = payload + checksum

value = int.from_bytes(encoded, "big")
digits = ""
while value:
    value, rem = divmod(value, 58)
    digits = ALPHABET[rem] + digits

prefix = sum(1 for byte in encoded if byte == 0)
address = "1" * prefix + digits
print(address)
```

Running the snippet prints `1NtiLNGegHWE3Mp9g2JPkgx6wUg4TW7bbk`, confirming the restored P2PKH address for Puzzle #45.
