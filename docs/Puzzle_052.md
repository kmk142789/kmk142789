# Bitcoin Puzzle #52 — Restoring the Broadcast Address

Puzzle #52 in the Bitcoin puzzle transaction catalogue again reveals the canonical pay-to-public-key-hash (P2PKH) locking script with a censored middle segment in the published destination address:

```
15z9c9sVp-K4GqsGZim
OP_DUP
OP_HASH160
36af659edbe94453f6344e920d143f1778653ae7
OP_EQUALVERIFY
OP_CHECKSIG
```

Reconstructing the missing characters follows the standard Base58Check encoding flow for a legacy P2PKH output:

1. Prefix the 20-byte HASH160 payload with the Bitcoin mainnet version byte `0x00`.
2. Double-SHA256 the resulting 21-byte buffer and append the first four checksum bytes.
3. Interpret the 25-byte result as a big-endian integer and encode it with the Base58 alphabet, adding a leading `1` for each prefixed zero byte.

Carrying out these steps restores the full destination string advertised by the puzzle:

- **Address:** `15z9c9sVpu6fwNiK7dMAFgMYSK4GqsGZim`
- **Missing infix:** `u6fwNiK7dMAFgMYS`

The reconstructed address matches the authoritative entry recorded in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

A short Python snippet demonstrates the reconstruction:

```python
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
payload = bytes.fromhex("00" + "36af659edbe94453f6344e920d143f1778653ae7")
checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
encoded = payload + checksum

num = int.from_bytes(encoded, "big")
digits = ""
while num:
    num, rem = divmod(num, 58)
    digits = alphabet[rem] + digits

prefix = sum(1 for byte in encoded if byte == 0)
address = "1" * prefix + digits
print(address)
```

Running the snippet prints `15z9c9sVpu6fwNiK7dMAFgMYSK4GqsGZim`, confirming the restored P2PKH address for Puzzle #52.
