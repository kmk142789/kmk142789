# Bitcoin Puzzle #160 — Completing the Broadcast Address

Puzzle #160 once again disguises a textbook pay-to-public-key-hash (P2PKH)
locking script, but the published Base58Check address is shown with its
centre excised:

```
1NBC8uXJy-51ps7EPTv
Pkscript
OP_DUP
OP_HASH160
e84818e1bf7f699aa6e28ef9edfb582099099292
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode layout already matches the canonical P2PKH template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Restoring the elided address block is therefore a straight Base58Check
reconstruction:

1. Prepend the mainnet version byte `0x00` to the 20-byte HASH160 payload.
2. Compute the double-SHA256 checksum of the 21-byte buffer and append the
   first four bytes.
3. Encode the resulting 25-byte value with the Bitcoin Base58 alphabet.

For completeness, the intermediate buffers look like this:

| Stage | Hex bytes |
|-------|-----------|
| Version + HASH160 | `00e84818e1bf7f699aa6e28ef9edfb582099099292` |
| Double-SHA256     | `5d351699ba4f28b56b96f73bf29ae149871c012b...` |
| Checksum (first 4 bytes) | `5d351699` |
| Final payload     | `00e84818e1bf7f699aa6e28ef9edfb5820990992925d351699` |

Encoding this payload reveals the missing infix:

- **Address:** `1NBC8uXJy1GiJ6drkiZa1WuKn51ps7EPTv`
- **Missing segment:** `1GiJ6drkiZa1WuKn`

The reconstructed address agrees with the authoritative entry for
HASH160 `e84818e1bf7f699aa6e28ef9edfb582099099292` in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To reproduce the decoding using the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1NBC8uXJy-51ps7EPTv\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "e84818e1bf7f699aa6e28ef9edfb582099099292\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1NBC8uXJy1GiJ6drkiZa1WuKn51ps7EPTv`, confirming the
restored address for Bitcoin Puzzle #160.
