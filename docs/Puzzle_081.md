# Bitcoin Puzzle #81 — Restoring the Hidden Infix

Puzzle #81 in the Bitcoin puzzle transaction series reveals a nearly complete
legacy pay-to-public-key-hash (P2PKH) script, but the associated address is
presented with a missing middle segment:

```
15qsCm78w-zxTQopnHZ
Pkscript
OP_DUP
OP_HASH160
351e605fac813965951ba433b7c2956bf8ad95ce
OP_EQUALVERIFY
OP_CH
ECKSIG
```

The script itself is the canonical five-token P2PKH program.  After normalising
the split `OP_CHECKSIG` opcode, the structure is identical to the template used
by every legacy Bitcoin address:

```
OP_DUP OP_HASH160 <20-byte hash> OP_EQUALVERIFY OP_CHECKSIG
```

Reconstructing the full address is therefore a straightforward Base58Check
encoding exercise:

1. Prefix the published HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte buffer and append the
   first four bytes.
3. Encode the resulting 25-byte value using the Bitcoin Base58 alphabet.

Performing these steps reveals the missing infix and confirms the canonical
address:

- **Address:** `15qsCm78whspNQFydGJQk5rexzxTQopnHZ`
- **Missing infix:** `hspNQFydGJQk5rex`

This matches the attested dataset entry stored in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), where the
HASH160 `351e605fac813965951ba433b7c2956bf8ad95ce` corresponds to the same
mainnet address.

To verify locally with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """15qsCm78w-zxTQopnHZ\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "351e605fac813965951ba433b7c2956bf8ad95ce\nOP_EQUALVERIFY\nOP_CH\nECKSIG"\n
decoded = decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `15qsCm78whspNQFydGJQk5rexzxTQopnHZ`, confirming the
restored address for Puzzle #81.
