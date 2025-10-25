# Bitcoin Puzzle #158 — Reconstructing the Hidden Infix

Puzzle #158 in the Bitcoin puzzle transaction catalogue reprises the
five-opcode pay-to-public-key-hash (P2PKH) locking script with a missing
segment in the advertised Base58Check address:

```
19z6waran-QRxvUNKBG
Pkscript
OP_DUP
OP_HASH160
628dacebb0faa7f81670e174ca4c8a95a7e37029
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode sequence already matches the standard legacy P2PKH template
used by mainnet outputs:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the redacted portion of the address therefore reduces to the
usual Base58Check workflow:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte
   `0x00`.
2. Compute the double-SHA256 checksum of the resulting 21-byte buffer and
   append the first four bytes of the digest.
3. Encode the 25-byte value with the Bitcoin Base58 alphabet to obtain
   the canonical address string.

Carrying out these steps restores the elided middle segment:

- **Address:** `19z6waranEf8CcP8FqNgdwUe1QRxvUNKBG`
- **Missing segment:** `Ef8CcP8FqNgdwUe1`

The reconstructed address matches the authoritative entry for HASH160
`628dacebb0faa7f81670e174ca4c8a95a7e37029` recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To reproduce the decoding with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """19z6waran-QRxvUNKBG\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "628dacebb0faa7f81670e174ca4c8a95a7e37029\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `19z6waranEf8CcP8FqNgdwUe1QRxvUNKBG`,
confirming the restored address for Puzzle #158.
