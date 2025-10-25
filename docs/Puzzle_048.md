# Bitcoin Puzzle #48 — Restoring the Broadcast Address

Puzzle #48 in the Bitcoin puzzle transaction series again presents the classic pay-to-public-key-hash (P2PKH) locking script with its broadcast address partially redacted:

```
1DFYhaB2J-s9VBqDHzv
OP_DUP
OP_HASH160
8661cb56d9df0a61f01328b55af7e56a3fe7a2b2
OP_EQUALVERIFY
OP_CHECKSIG
```

Reconstructing the full address follows the textbook Base58Check procedure for a legacy P2PKH output:

1. Prefix the 20-byte HASH160 payload with the Bitcoin mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the resulting 21-byte buffer and append the first four checksum bytes.
3. Encode the 25-byte result with the Base58 alphabet, preserving every leading zero byte as a `1` character.

Applying these steps restores the missing middle segment from the clue, yielding the complete destination string:

- **Address:** `1DFYhaB2J9q1LLZJWKTnscPWos9VBqDHzv`
- **Missing infix:** `9q1LLZJWKTnscPWo`

The reconstructed address matches the authoritative dataset entry recorded in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

A short Python snippet verifies the recovery:

```python
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
payload = bytes.fromhex("00" + "8661cb56d9df0a61f01328b55af7e56a3fe7a2b2")
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

Running the snippet prints `1DFYhaB2J9q1LLZJWKTnscPWos9VBqDHzv`, confirming the restored P2PKH address for Puzzle #48.
