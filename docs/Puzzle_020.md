# Bitcoin Puzzle #20 — Restoring the Missing Infix

Puzzle #20 reprises the canonical pay-to-public-key-hash (P2PKH) locking
script, but the published Base58Check address omits its central segment and
replaces it with a hyphen:

```
1HsMJxNiV-FDog4NQum
Pkscript
OP_DUP
OP_HASH160
b907c3a2a3b27789dfb509b730dd47703c272868
OP_EQUALVERIFY
OP_CHECKSIG
```

Reconstructing the full address follows the standard Base58Check recipe for a
legacy P2PKH output:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00` to
   produce a 21-byte buffer.
2. Double-SHA256 the buffer and append the first four checksum bytes.
3. Base58Check-encode the resulting 25-byte value.

Executing these steps fills in the missing infix segment:

- **Address:** `1HsMJxNiV7TLxmoF6uJNkydxPFDog4NQum`
- **Missing segment:** `7TLxmoF6uJNkydxP`

The reconstructed address matches the authoritative HASH160 entry for Puzzle #20
recorded in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json)
and [`satoshi/puzzle-proofs/puzzle020.json`](../satoshi/puzzle-proofs/puzzle020.json).

To confirm the derivation with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1HsMJxNiV-FDog4NQum\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "b907c3a2a3b27789dfb509b730dd47703c272868\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1HsMJxNiV7TLxmoF6uJNkydxPFDog4NQum`, confirming the
fully restored P2PKH address for Puzzle #20.
