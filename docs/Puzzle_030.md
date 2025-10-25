# Bitcoin Puzzle #30 — Reconstructing the Hidden Infix

Puzzle #30 in the well-known Bitcoin puzzle transaction series again
presents a canonical pay-to-public-key-hash (P2PKH) locking script, but the
headline address is missing its centre segment and the final opcode appears
in the usual fractured form:

```
1LHtnpd8n-jLc992bps
Pkscript
OP_DUP
OP_HASH160
d39c4704664e1deb76c9331e637564c257d68a08
OP_EQUALVERIFY
OP_CH
ECKSIG
```

Stitching the opcode halves back together yields the expected five-operation
P2PKH template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the missing middle of the Base58Check address follows the standard
workflow:

1. Prepend the HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the resulting 21-byte buffer and
   append the first four checksum bytes.
3. Encode the 25-byte value with the Bitcoin Base58 alphabet.

Running these steps restores the elided infix:

- **Address:** `1LHtnpd8nU5VHEMkG2TMYYNUjjLc992bps`
- **Missing segment:** `U5VHEMkG2TMYYNUjj`

The reconstructed address matches the authoritative HASH160 entry recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json) for Puzzle
#30, confirming the decoded output.

To reproduce the decoding with the project helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1LHtnpd8n-jLc992bps\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "d39c4704664e1deb76c9331e637564c257d68a08\nOP_EQUALVERIFY\nOP_CH\nECKSIG"
print(decode_p2pkh_script(script).address)
```

Executing the snippet prints `1LHtnpd8nU5VHEMkG2TMYYNUjjLc992bps`, validating the
restored P2PKH address for Puzzle #30.
