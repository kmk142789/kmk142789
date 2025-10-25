# Puzzle #116 P2PKH Reconstruction

Puzzle #116 again ships with the canonical pay-to-public-key-hash (P2PKH)
locking script together with a Base58Check address whose interior section was
redacted for the puzzle statement:

```
Puzzle #116
1MnJ6hdhv-xyWH2PHUV
Pkscript
OP_DUP
OP_HASH160
e3f381c34a20da049779b44cae0417c7fb2898d0
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode listing aligns with the five-operation legacy template that all
Bitcoin puzzle outputs have used:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the hidden portion only requires recomputing the Base58Check
encoding for the published HASH160 digest:

1. Prefix the digest with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte payload and append the first four checksum
   bytes.
3. Encode the resulting 25-byte buffer with Bitcoin's Base58 alphabet.

Running the procedure yields the unabridged destination and highlights the
redacted substring:

- **Address:** `1MnJ6hdhvK37VLmqcdEwqC3iFxyWH2PHUV`
- **Missing segment:** `K37VLmqcdEwqC3iF`

The reconstructed address matches the entry recorded for Puzzle #116 in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which
tracks the same HASH160 `e3f381c34a20da049779b44cae0417c7fb2898d0`.

To verify the reconstruction with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #116\n1MnJ6hdhv-xyWH2PHUV\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "e3f381c34a20da049779b44cae0417c7fb2898d0\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Executing the snippet prints `1MnJ6hdhvK37VLmqcdEwqC3iFxyWH2PHUV`, confirming
the canonical P2PKH output for Puzzle #116.
