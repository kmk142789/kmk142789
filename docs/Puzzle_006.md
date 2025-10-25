# Bitcoin Puzzle #6 — Completing the P2PKH Address

Puzzle #6 provides the usual pay-to-public-key-hash (P2PKH) locking script,
but the printed Base58Check address drops its central payload and replaces it
with a hyphen:

```
1PitScNLy-nfmpPbfp8
Pkscript
OP_DUP
OP_HASH160
f93ec34e9e34a8f8ff7d600cdad83047b1bcb45c
OP_EQUALVERIFY
OP_CHECKSIG
```

Restoring the missing characters follows the standard reconstruction recipe
for legacy Bitcoin addresses encoded from a HASH160 payload:

1. Prefix the 20-byte HASH160 with the mainnet version byte `0x00` to create a
   21-byte buffer.
2. Double-SHA256 the buffer and append the first four checksum bytes.
3. Base58Check-encode the resulting 25-byte value.

Executing these steps fills in the missing infix segment:

- **Address:** `1PitScNLyp2HCygzadCh7FveTnfmpPbfp8`
- **Missing segment:** `p2HCygzadCh7FveT`

The reconstructed address matches the authoritative HASH160 entry for Puzzle #6
recorded in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json)
and [`satoshi/puzzle-proofs/puzzle006.json`](../satoshi/puzzle-proofs/puzzle006.json).

To confirm the derivation with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1PitScNLy-nfmpPbfp8\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "f93ec34e9e34a8f8ff7d600cdad83047b1bcb45c\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1PitScNLyp2HCygzadCh7FveTnfmpPbfp8`, confirming the
fully restored P2PKH address for Puzzle #6.
