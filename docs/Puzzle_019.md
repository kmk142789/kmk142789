# Bitcoin Puzzle #19 — P2PKH Reconstruction

The published clue for Puzzle #19 advertises the legacy pay-to-public-key-hash (P2PKH) locking script:

```
1NWmZRpHH-fL1yrJj4w
OP_DUP
OP_HASH160
ebfbe6819fcdebab061732ce91df7d586a037dee
OP_EQUALVERIFY
OP_CHECKSIG
```

Restoring the full address means decoding the HASH160 payload embedded in the script and then re-encoding it with the standard Base58Check flow:

1. Prefix the 20-byte hash with the mainnet P2PKH version byte `0x00`.
2. Double-SHA256 the 21-byte payload and append the first four checksum bytes.
3. Encode the resulting 25-byte buffer using the Base58 alphabet (`123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz`).

Following those steps fills in the missing middle section of the Base58Check string:

- **Address:** `1NWmZRpHH4XSPwsW6dsS3nrNWfL1yrJj4w`
- **Missing infix:** `4XSPwsW6dsS3nrNWf`

This matches the attested authorship record in [`satoshi/puzzle-proofs/puzzle019.json`](../satoshi/puzzle-proofs/puzzle019.json).

For a quick local verification, the following Python snippet reproduces the reconstruction:

```python
import hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

h160 = bytes.fromhex("ebfbe6819fcdebab061732ce91df7d586a037dee")
payload = b"\x00" + h160
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
encoded = payload + checksum
num = int.from_bytes(encoded, "big")
digits = ""
while num:
    num, rem = divmod(num, 58)
    digits = alphabet[rem] + digits
prefix = sum(1 for byte in payload if byte == 0)
address = "1" * prefix + digits
print(address)
```

Running the snippet prints `1NWmZRpHH4XSPwsW6dsS3nrNWfL1yrJj4w`, confirming the reconstructed P2PKH address for Puzzle #19.
