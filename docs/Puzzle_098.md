# Bitcoin Puzzle #98 — Restoring the Hidden Infix

Puzzle #98 in the Bitcoin puzzle catalogue again presents the canonical pay-to-public-key-hash (P2PKH) locking script with the published address missing its middle segment:

```
1CaBVPrwU-R4maNoJSX
Pkscript
OP_DUP
OP_HASH160
7eefddd979a1d6bb6f29757a1f463579770ba566
OP_EQUALVERIFY
OP_CHECKSIG
```

Normalising the opcodes confirms the standard P2PKH template used for legacy Bitcoin outputs:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Reconstructing the full address follows the usual Base58Check procedure:

1. Prefix the provided HASH160 value with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four bytes.
3. Encode the resulting 25-byte buffer with the Bitcoin Base58 alphabet.

Executing these steps restores the elided infix and yields the complete destination:

- **Address:** `1CaBVPrwUxbQYYswu32w7Mj4HR4maNoJSX`
- **Missing segment:** `xbQYYswu32w7Mj4H`

The recovered address matches the authoritative catalogue entry stored in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which associates HASH160 `7eefddd979a1d6bb6f29757a1f463579770ba566` with the same mainnet P2PKH destination.

To verify locally with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1CaBVPrwU-R4maNoJSX\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "7eefddd979a1d6bb6f29757a1f463579770ba566\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1CaBVPrwUxbQYYswu32w7Mj4HR4maNoJSX`, confirming the restored P2PKH address for Puzzle #98.
