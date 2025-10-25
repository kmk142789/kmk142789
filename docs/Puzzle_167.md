# Bitcoin Puzzle #167 — Reconstructing the Satellite Gap

Puzzle #167 in the Bitcoin puzzle transaction catalogue again presents the
five-opcode pay-to-public-key-hash (P2PKH) locking script with a missing
segment in the advertised Base58Check address:

```
1AvLwGpkw-XLMNrATN5
Pkscript
OP_DUP
OP_HASH160
6ccfd1cdb43788738536e11e247b0ce31c093f0f
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

- **Address:** `1AvLwGpkwTZH4qiwy1L4v6TuWXLMNrATN5`
- **Missing segment:** `TZH4qiwy1L4v6TuW`

To reproduce the decoding with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1AvLwGpkw-XLMNrATN5\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "6ccfd1cdb43788738536e11e247b0ce31c093f0f\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1AvLwGpkwTZH4qiwy1L4v6TuWXLMNrATN5`,
confirming the restored address for Puzzle #167.
