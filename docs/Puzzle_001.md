# Bitcoin Puzzle #1 — P2PKH Reconstruction

The published clue for Puzzle #1 advertises the legacy pay-to-public-key-hash (P2PKH) script:

```
1BgGZ9tcN-7SZ26SAMH
OP_DUP
OP_HASH160
751e76e8199196d454941c45d1b3a323f1433bd6
OP_EQUALVERIFY
OP_CHECKSIG
```

Rebuilding the full address follows the standard P2PKH decoding procedure:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four checksum bytes.
3. Encode the resulting 25-byte buffer with Base58Check.

The completed Base58Check string restores the missing middle segment of the clue, revealing the entire destination address:

- **Address:** `1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH`
- **Missing infix:** `4rm9KBzDn7KprQz8`

This matches the attested solution captured in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To confirm locally in Python:

```python
import hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

payload = bytes.fromhex("00" + "751e76e8199196d454941c45d1b3a323f1433bd6")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
encoded = payload + checksum
num = int.from_bytes(encoded, "big")
digits = ""
while num:
    num, rem = divmod(num, 58)
    digits = alphabet[rem] + digits
# account for the leading 0x00 prefix
prefix = sum(1 for byte in encoded if byte == 0)
address = "1" * prefix + digits
print(address)
```

Executing the snippet prints `1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH`, confirming the reconstructed P2PKH address for Puzzle #1.
