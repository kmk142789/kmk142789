# Puzzle #96 P2PKH Reconstruction

Puzzle #96 in the Bitcoin puzzle series again publishes the canonical five-opcode pay-to-public-key-hash (P2PKH) locking script.  The clue provides the Base58Check address with a missing infix — `15ANYzzCp-zgPLWaD8b` — alongside the 20-byte HASH160 digest `2da63cbd251d23c7b633cb287c09e6cf888b3fe4`.

## Script template

```
OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
```

Filling in the supplied digest yields the standard mainnet P2PKH assembly.  Recovering the full address only requires re-encoding the hash with Bitcoin's Base58Check algorithm.

1. Prefix the HASH160 with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte payload and keep the first four checksum bytes.
3. Append the checksum, then encode the result with the Base58 alphabet, reintroducing the missing characters.

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

payload = bytes.fromhex("002da63cbd251d23c7b633cb287c09e6cf888b3fe4")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
address = base58encode(payload + checksum)
print(address)  # 15ANYzzCp5BFHcCnVFzXqyibpzgPLWaD8b
```

The reconstructed Base58Check string restores the omitted segment (`5BFHcCnVFzXqyibp`) and matches the canonical entry logged in `satoshi/puzzle_solutions.json`, confirming the standard P2PKH output for Puzzle #96.
