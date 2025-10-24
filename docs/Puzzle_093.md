# Bitcoin Puzzle #93 — Repairing the Fractured Checksig

Puzzle #93 in the Bitcoin puzzle transaction catalogue reveals a legacy
pay-to-public-key-hash (P2PKH) locking script accompanied by a partially
redacted address. The published artefact also fractures the final opcode
across two lines:

```
17Q7tuG2J-oH3mx2Jad
Pkscript
OP_DUP
OP_HASH160
463013cd41279f2fd0c31d0a16db3972bfffac8d
OP_EQUALVERIFY
OP_CH
ECKSIG
```

Joining the split opcode restores the canonical P2PKH template that defines
standard Bitcoin addresses:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recreating the missing portion of the address follows the usual
Base58Check workflow:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte buffer and append the
   first four bytes.
3. Encode the resulting 25-byte value with the Bitcoin Base58 alphabet.

Executing these steps restores the elided infix:

- **Address:** `17Q7tuG2JwFFU9rXVj3uZqRtioH3mx2Jad`
- **Missing segment:** `wFFU9rXVj3uZqRti`

The recovered address matches the authoritative mapping for HASH160
`463013cd41279f2fd0c31d0a16db3972bfffac8d` recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To reproduce the reconstruction with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """17Q7tuG2J-oH3mx2Jad\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "463013cd41279f2fd0c31d0a16db3972bfffac8d\nOP_EQUALVERIFY\nOP_CH\nECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `17Q7tuG2JwFFU9rXVj3uZqRtioH3mx2Jad`, confirming the
restored address for Puzzle #93.
