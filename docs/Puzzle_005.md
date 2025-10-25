# Bitcoin Puzzle #5 — Restoring the Hidden Infix

Puzzle #5 in the Bitcoin puzzle transaction series again supplies the
standard pay-to-public-key-hash (P2PKH) locking script, but the published
address is missing its middle segment and the final opcode is split across
two lines:

```
1E6NuFjCi-84zJeBW3k
Pkscript
OP_DUP
OP_HASH160
8f9dff39a81ee4abcbad2ad8bafff090415a2be8
OP_EQUALVERIFY
OP_CH
ECKSIG
```

Joining the fractured opcode yields the canonical five-opcode P2PKH
template that secures a legacy Bitcoin address:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the missing characters in the Base58Check address follows the
usual reconstruction steps:

1. Prefix the HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte buffer and append the
   first four checksum bytes.
3. Encode the resulting 25-byte value with the Bitcoin Base58 alphabet.

Executing these steps restores the elided infix:

- **Address:** `1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k`
- **Missing segment:** `27W5zoXg8TRdcSRq`

The reconstructed address matches the authoritative entry for HASH160
`8f9dff39a81ee4abcbad2ad8bafff090415a2be8` captured in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To reproduce the decoding with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1E6NuFjCi-84zJeBW3k\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "8f9dff39a81ee4abcbad2ad8bafff090415a2be8\nOP_EQUALVERIFY\nOP_CH\nECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k`, confirming the
restored P2PKH address for Puzzle #5.
