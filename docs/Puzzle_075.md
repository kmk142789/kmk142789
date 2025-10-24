# Bitcoin Puzzle #75 — P2PKH Reconstruction

The published clue for Puzzle #75 provides the legacy pay-to-public-key-hash (P2PKH) script:

```
1J36UjUBy-Vv9caEeAt
OP_DUP
OP_HASH160
badf8b0d34289e679ec65c6c61d3a974353be5cf
OP_EQUALVERIFY
OP_CHECKSIG
```

Rebuilding the legacy address is a matter of decoding the hash160 payload inside the script.

1. Prefix the 20-byte hash with the mainnet P2PKH version byte `0x00`.
2. Compute the double-SHA256 checksum and append the first four bytes.
3. Encode the resulting 25-byte buffer in Base58Check.

The resulting Base58Check string fills the missing middle section of the clue, revealing the full puzzle address:

- **Address:** `1J36UjUByGroXcCvmj13U6uwaVv9caEeAt`
- **Missing infix:** `GroXcCvmj13U6uwa`

This matches the attested solution published in [`satoshi/puzzle-proofs/puzzle075.json`](../satoshi/puzzle-proofs/puzzle075.json).

To verify locally with Python:

```python
import hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

payload = bytes.fromhex("00" + "badf8b0d34289e679ec65c6c61d3a974353be5cf")
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

Running the snippet prints the canonical address `1J36UjUByGroXcCvmj13U6uwaVv9caEeAt`, confirming the reconstruction.
