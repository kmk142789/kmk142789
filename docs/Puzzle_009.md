# Bitcoin Puzzle #9 — Restoring the Missing Infix

Puzzle #9 in the Bitcoin puzzle transaction catalogue again surfaces a
standard pay-to-public-key-hash (P2PKH) locking script.  The published
artefact redacts part of the advertised address and splits the final
opcode across two lines:

```
1CQFwcjw1-7ivBonGPV
Pkscript
OP_DUP
OP_HASH160
7d0f6c64afb419bbd7e971e943d7404b0e0daab4
OP_EQUALVERIFY
OP_CH
ECKSIG
```

Rejoining the fractured opcode yields the canonical five-opcode P2PKH
sequence:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the missing portion of the Base58Check address follows the
usual process:

1. Prefix the published HASH160 value with the mainnet version byte
   `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append
   the first four bytes of the digest.
3. Encode the resulting 25-byte buffer with the Bitcoin Base58 alphabet.

Executing these steps restores the elided middle segment:

- **Address:** `1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV`
- **Missing segment:** `dwhtkVWBttNLDtqL`

The reconstructed address matches the authoritative mapping for HASH160
`7d0f6c64afb419bbd7e971e943d7404b0e0daab4` recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To reproduce the calculation with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1CQFwcjw1-7ivBonGPV\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "7d0f6c64afb419bbd7e971e943d7404b0e0daab4\nOP_EQUALVERIFY\nOP_CH\nECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV`, confirming
the restored address for Puzzle #9.
