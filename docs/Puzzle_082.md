# Bitcoin Puzzle #82 — P2PKH Reconstruction

The published clue for Puzzle #82 provides the legacy pay-to-public-key-hash (P2PKH) script:

```
13zYrYhhJ-NWM45ARAC
OP_DUP
OP_HASH160
20d28d4e87543947c7e4913bcdceaa16e2f8f061
OP_EQUALVERIFY
OP_CHECKSIG
```

Rebuilding the legacy address is a matter of decoding the hash160 payload inside the script.

1. Prefix the 20-byte hash with the mainnet P2PKH version byte `0x00`.
2. Compute the double-SHA256 checksum and append the first four bytes.
3. Encode the resulting 25-byte buffer in Base58Check.

The resulting Base58Check string fills the missing middle section of the clue, revealing the full puzzle address:

- **Address:** `13zYrYhhJxp6Ui1VV7pqa5WDhNWM45ARAC`
- **Missing infix:** `xp6Ui1VV7pqa5WDh`

This matches the attested solution published in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To verify locally with Python:

```python
import hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

payload = bytes.fromhex("00" + "20d28d4e87543947c7e4913bcdceaa16e2f8f061")
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

Running the snippet prints the canonical address `13zYrYhhJxp6Ui1VV7pqa5WDhNWM45ARAC`, confirming the reconstruction.
