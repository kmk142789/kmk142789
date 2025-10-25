# Bitcoin Puzzle #4 — P2PKH Reconstruction

The published clue for Puzzle #4 advertises the familiar five-opcode pay-to-public-key-hash (P2PKH) locking script:

```
1EhqbyUMv-6YKfPqb7e
OP_DUP
OP_HASH160
9652d86bedf43ad264362e6e6eba6eb764508127
OP_EQUALVERIFY
OP_CHECKSIG
```

Reconstructing the full address is a matter of decoding the embedded HASH160 payload and re-encoding it with the standard Base58Check procedure:

1. Prefix the 20-byte hash with the mainnet P2PKH version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four bytes.
3. Encode the resulting 25-byte buffer with the Base58 alphabet, preserving the leading version byte as `1`.

Executing these steps restores the missing middle segment of the clue and reveals the complete destination address:

- **Address:** `1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e`
- **Missing infix:** `vs7BfL8goY6qcPbD`

This matches the attested solution recorded in [`satoshi/puzzle-proofs/puzzle004.json`](../satoshi/puzzle-proofs/puzzle004.json) and the aggregate dataset in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

For a quick verification in Python:

```python
import hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

payload = bytes.fromhex("00" + "9652d86bedf43ad264362e6e6eba6eb764508127")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
encoded = payload + checksum
num = int.from_bytes(encoded, "big")
digits = ""
while num:
    num, rem = divmod(num, 58)
    digits = alphabet[rem] + digits
# account for the leading 0x00 prefix
prefix = sum(1 for byte in payload if byte == 0)
address = "1" * prefix + digits
print(address)
```

Running the snippet prints `1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e`, confirming the reconstructed address for Puzzle #4.
