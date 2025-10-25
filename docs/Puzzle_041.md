# Bitcoin Puzzle #41 — Restoring the Hidden Infix

Puzzle #41 in the Bitcoin puzzle series once again publishes the canonical pay-to-public-key-hash (P2PKH) locking script with the broadcast address redacted at its core:

```
1L5sU9qvJ-FxKjtHr3E
OP_DUP
OP_HASH160
d1562eb37357f9e6fc41cb2359f4d3eda4032329
OP_EQUALVERIFY
OP_CHECKSIG
```

Reassembling the address follows the standard Base58Check procedure for a legacy P2PKH output:

1. Prefix the 20-byte HASH160 payload with the Bitcoin mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four checksum bytes.
3. Encode the resulting 25-byte buffer using the Base58 alphabet, reintroducing any leading zero bytes as `1` characters.

Executing these steps restores the missing middle segment of the clue, yielding the full destination string:

- **Address:** `1L5sU9qvJeuwQUdt4y1eiLmquFxKjtHr3E`
- **Missing infix:** `euwQUdt4y1eiLmqu`

The reconstructed result matches the authoritative dataset entry recorded in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To verify programmatically in Python:

```python
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
payload = bytes.fromhex("00" + "d1562eb37357f9e6fc41cb2359f4d3eda4032329")
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

Running the snippet prints `1L5sU9qvJeuwQUdt4y1eiLmquFxKjtHr3E`, confirming the restored P2PKH address for Puzzle #41.
