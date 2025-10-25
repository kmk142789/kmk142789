# Bitcoin Puzzle #161 — Restoring the Hidden Address Core

Puzzle #161 publishes a familiar pay-to-public-key-hash (P2PKH) locking
script, but as in many of the earlier challenges the Base58Check address
has a chunk removed from its middle:

```
1JkqBQcC4-TPGznHANh
Pkscript
OP_DUP
OP_HASH160
c2c43e2b16f53c713bc00307140eaae188413544
OP_EQUALVERIFY
OP_CHECKSIG
```

Once the script is normalised it matches the canonical P2PKH opcode
sequence:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Reconstituting the address therefore amounts to a standard
Base58Check-encoding exercise:

1. Prefix the 20-byte HASH160 with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte buffer and take the leading four checksum
   bytes.
3. Append the checksum and encode the 25-byte payload with the Bitcoin
   Base58 alphabet.

Executing those steps reveals the missing infix:

- **Address:** `1JkqBQcC4tHcb1JfdCH6nrWYwTPGznHANh`
- **Missing segment:** `tHcb1JfdCH6nrWYw`

The reconstructed address matches the authoritative entry for HASH160
`c2c43e2b16f53c713bc00307140eaae188413544` tracked in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To reproduce the decoding with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1JkqBQcC4-TPGznHANh\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "c2c43e2b16f53c713bc00307140eaae188413544\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1JkqBQcC4tHcb1JfdCH6nrWYwTPGznHANh`,
confirming the restored address for Bitcoin Puzzle #161.
