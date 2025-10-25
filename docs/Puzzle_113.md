# Bitcoin Puzzle #113 — Restoring the Broadcast Address

Puzzle #113 again publishes the textbook pay-to-public-key-hash (P2PKH)
locking script alongside a Base58Check address whose core has been censored:

```
Puzzle #113
1NeGn21dU-XuBLA4WT4
Pkscript
OP_DUP
OP_HASH160
ed673389e4b12925316f9166d56d701829e53cf8
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode sequence is the familiar five-step P2PKH template that appears
throughout the Bitcoin puzzle series. With the HASH160 fingerprint supplied,
reconstructing the missing middle segment is a straightforward Base58Check
encoding exercise:

1. Prefix the 20-byte HASH160 with the mainnet version byte `0x00`.
2. Double-SHA256 hash the 21-byte payload and keep the first four bytes as the
   checksum.
3. Append the checksum and encode the 25-byte buffer with Bitcoin's Base58
   alphabet.

Executing these steps restores the hidden infix and yields the complete legacy
address for Puzzle #113:

- **Address:** `1NeGn21dUDDeqFQ63xb2SpgUuXuBLA4WT4`
- **Missing segment:** `DDeqFQ63xb2SpgUu`

The reconstructed address matches the authoritative catalogue entry in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which
records the same HASH160 `ed673389e4b12925316f9166d56d701829e53cf8` for Puzzle
#113.

You can verify the reconstruction with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #113\n1NeGn21dU-XuBLA4WT4\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "ed673389e4b12925316f9166d56d701829e53cf8\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1NeGn21dUDDeqFQ63xb2SpgUuXuBLA4WT4`, confirming the
restored P2PKH address for Bitcoin Puzzle #113.
