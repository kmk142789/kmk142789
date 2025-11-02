# Bitcoin Puzzle #120 — Restoring the Broadcast P2PKH Address

Puzzle #120 again publishes the classic pay-to-public-key-hash (P2PKH)
locking script with the Base58Check address censored across its center:

```
Puzzle #120
11d8MosPb-dQdSqrTwm
Pkscript
OP_DUP
OP_HASH160
001e283e0acd541dd54053b0be1129b1dcf8dc45
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode sequence is the standard five-step template the Bitcoin puzzle
series uses throughout:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

With the HASH160 digest published, recovering the missing infix is a
straightforward Base58Check reconstruction:

1. Prefix the 20-byte fingerprint with the mainnet version byte `0x00`.
2. Double-SHA256 hash the 21-byte payload and take the first four bytes as the
   checksum.
3. Append the checksum and encode the resulting 25-byte buffer with Bitcoin's
   Base58 alphabet.

Executing these steps restores the redacted characters and yields the complete
legacy address for Puzzle #120:

- **Address:** `11d8MosPb8jXPGUaHFx2pxpDdQdSqrTwm`
- **Missing segment:** `8jXPGUaHFx2pxpD`

The reconstructed address matches the authoritative catalogue entry recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which pairs
the same HASH160 `001e283e0acd541dd54053b0be1129b1dcf8dc45` with Puzzle #120.

You can verify the reconstruction with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #120\n11d8MosPb-dQdSqrTwm\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "001e283e0acd541dd54053b0be1129b1dcf8dc45\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `11d8MosPb8jXPGUaHFx2pxpDdQdSqrTwm`, confirming the
restored P2PKH address for Bitcoin Puzzle #120.
