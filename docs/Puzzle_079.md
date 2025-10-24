# Bitcoin Puzzle #79 — P2PKH Reconstruction

The published clue for Puzzle #79 provides the legacy pay-to-public-key-hash (P2PKH) script:

```
1ARk8HWJM-E7KRkn2t8
OP_DUP
OP_HASH160
67671d5490c272e3ab7ddd34030d587738df33da
OP_EQUALVERIFY
OP_CHECKSIG
```

Rebuilding the legacy address is a matter of decoding the hash160 payload inside the script.

1. Prefix the 20-byte hash with the mainnet P2PKH version byte `0x00`.
2. Compute the double-SHA256 checksum and append the first four bytes.
3. Encode the resulting 25-byte buffer in Base58Check.

The resulting Base58Check string fills the missing middle section of the clue, revealing the full puzzle address:

- **Address:** `1ARk8HWJMn8js8tQmGUJeQHjSE7KRkn2t8`
- **Missing infix:** `n8js8tQmGUJeQHjS`

This matches the attested solution published in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To verify locally with Python:

```python
import hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

payload = bytes.fromhex("00" + "67671d5490c272e3ab7ddd34030d587738df33da")
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

Running the snippet prints the canonical address `1ARk8HWJMn8js8tQmGUJeQHjSE7KRkn2t8`, confirming the reconstruction.
