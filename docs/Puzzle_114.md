# Bitcoin Puzzle #114 — Reconstructing the Missing Core

Puzzle #114 in the long-running Bitcoin puzzle transaction campaign again uses
an ordinary pay-to-public-key-hash (P2PKH) locking script.  The clue preserves
the HASH160 payload, but the published Base58Check address is fractured — the
middle characters are replaced with a hyphen and the final opcode is split
across lines:

```
174SNxfqp-MRNZEePoy
Pkscript
OP_DUP
OP_HASH160
42773005f9594cd16b10985d428418acb7f352ec
OP_EQUALVERIFY
OP_CH
ECKSIG
```

As expected, the reconstructed locking script matches the canonical five-opcode
pattern:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Restoring the address simply requires the standard Base58Check steps for a
mainnet P2PKH output:

1. Prefix the HASH160 payload with the version byte `0x00`.
2. Double-SHA256 the 21-byte buffer and append the first four checksum bytes.
3. Encode the 25-byte result with the Bitcoin Base58 alphabet, preserving the
   leading `1` that corresponds to the version byte.

Applying this procedure recovers the missing infix:

- **Address:** `174SNxfqpdMGYy5YQcfLbSTK3MRNZEePoy`
- **Missing segment:** `dMGYy5YQcfLbSTK3`

For a quick confirmation, the following Python snippet reproduces the
Base58Check reconstruction locally:

```python
import hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

payload = bytes.fromhex("00" + "42773005f9594cd16b10985d428418acb7f352ec")
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

Running the script prints `174SNxfqpdMGYy5YQcfLbSTK3MRNZEePoy`, matching the
authoritative entry recorded in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json)
for puzzle #114.
