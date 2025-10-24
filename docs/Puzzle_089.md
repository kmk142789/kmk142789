# Bitcoin Puzzle #89 — Reconstructing the Split Checksig

Puzzle #89 in the Bitcoin puzzle transaction catalogue presents a canonical
legacy pay-to-public-key-hash (P2PKH) script, but the published transcript splits
the final opcode across two separate lines:

```
19QciEHbG-JSBZ6TaVt
Pkscript
OP_DUP
OP_HASH160
5c3862203d1e44ab3af441503e22db97b1c5097e
OP_EQUALVERIFY
OP_CH
ECKSIG
```

Normalising the opcode fragments merges `OP_CH` / `ECKSIG` back into the single
`OP_CHECKSIG` instruction, leaving the textbook five-element P2PKH program:

```
OP_DUP OP_HASH160 <20-byte hash> OP_EQUALVERIFY OP_CHECKSIG
```

Deriving the corresponding Base58Check address is therefore a standard three-step
process:

1. Prefix the HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the resulting 21-byte buffer and append
   the first four bytes.
3. Encode the 25-byte result using the Bitcoin Base58 alphabet.

Executing these steps reveals the complete address and confirms the missing
segment introduced by the split opcode:

- **Address:** `19QciEHbGVNY4hrhfKXmcBBCrJSBZ6TaVt`
- **Missing infix:** `VNY4hrhfKXmcBBCr`

The derived address matches the attested dataset entry stored in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which lists
the same HASH160 `5c3862203d1e44ab3af441503e22db97b1c5097e` for Puzzle #89.

To validate locally with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """19QciEHbG-JSBZ6TaVt\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "5c3862203d1e44ab3af441503e22db97b1c5097e\nOP_EQUALVERIFY\nOP_CH\nECKSIG"\n
decoded = decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `19QciEHbGVNY4hrhfKXmcBBCrJSBZ6TaVt`, confirming the
reconstructed address for Puzzle #89.
