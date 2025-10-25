# Bitcoin Puzzle #121 — Reconstructing the Redacted P2PKH Address

Puzzle #121 once again shares a legacy pay-to-public-key-hash (P2PKH) locking
script alongside a Base58Check destination with its middle section censored:

```
1GDSuiThE-dGjqkxKyh
Pkscript
OP_DUP
OP_HASH160
a6e4818537e42f7b3f021daa810367dad4dda16f
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode sequence follows the canonical P2PKH pattern used throughout the
campaign:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the missing characters therefore reduces to running the standard
Base58Check steps against the published HASH160 digest:

1. Prefix the 20-byte digest with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte payload and take the first four bytes as the
   checksum.
3. Append the checksum and encode the resulting 25-byte buffer with the Bitcoin
   Base58 alphabet.

Executing this procedure reinstates the elided middle segment and yields the
complete legacy address:

- **Address:** `1GDSuiThEV64c166LUFC9uDcVdGjqkxKyh`
- **Missing segment:** `V64c166LUFC9uDcV`

The reconstruction matches the canonical catalogue entry for Puzzle #121 in the
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json) registry,
which pairs the same HASH160 fingerprint
`a6e4818537e42f7b3f021daa810367dad4dda16f` with the recovered destination.

You can confirm the derivation with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #121\n1GDSuiThE-dGjqkxKyh\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "a6e4818537e42f7b3f021daa810367dad4dda16f\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1GDSuiThEV64c166LUFC9uDcVdGjqkxKyh`, confirming the
restored P2PKH address for Bitcoin Puzzle #121.
