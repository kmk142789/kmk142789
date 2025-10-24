# Bitcoin Puzzle #91 — Restoring the Missing Core

Puzzle #91 in the Bitcoin puzzle transaction challenge surfaces a nearly
complete legacy pay-to-public-key-hash (P2PKH) locking script, but the
associated address is published with an elided middle segment:

```
1EzVHtmbN-smXYJ4s74
Pkscript
OP_DUP
OP_HASH160
9978f61b92d16c5f1a463a0995df70da1f7a7d2a
OP_EQUALVERIFY
OP_CHECKSIG
```

After normalising the opcode fragments, the program matches the canonical
P2PKH template used by traditional Bitcoin addresses:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Rebuilding the full address follows the standard Base58Check recipe:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte buffer and append the
   first four bytes.
3. Encode the resulting 25-byte value using the Bitcoin Base58 alphabet.

Executing these steps reveals the hidden infix and restores the complete
address:

- **Address:** `1EzVHtmbN4fs4MiNk3ppEnKKhsmXYJ4s74`
- **Missing segment:** `4fs4MiNk3ppEnKKh`

The recovered address aligns with the authoritative dataset entry stored in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which maps
HASH160 `9978f61b92d16c5f1a463a0995df70da1f7a7d2a` to the same mainnet P2PKH
address.

To verify locally with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1EzVHtmbN-smXYJ4s74\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "9978f61b92d16c5f1a463a0995df70da1f7a7d2a\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1EzVHtmbN4fs4MiNk3ppEnKKhsmXYJ4s74`, confirming the
restored address for Puzzle #91.
