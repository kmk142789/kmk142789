# Bitcoin Puzzle #92 — Restoring the Hidden Infix

Puzzle #92 in the Bitcoin puzzle catalogue again presents a legacy pay-to-public-key-hash (P2PKH) locking script with a redacted middle segment in the advertised address:

```
1AE8NzzgK-MbPo82NB5
Pkscript
OP_DUP
OP_HASH160
6534b31208fe6e100d29f9c9c75aac8bf06fbb38
OP_EQUALVERIFY
OP_CHECKSIG
```

Normalising the opcodes yields the canonical P2PKH template used for standard Bitcoin addresses:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Reconstructing the full address follows the Base58Check procedure:

1. Prefix the published HASH160 with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four bytes.
3. Encode the resulting 25-byte buffer with the Bitcoin Base58 alphabet.

Executing these steps restores the elided infix and produces the complete address:

- **Address:** `1AE8NzzgKE7Yhz7BWtAcAAxiFMbPo82NB5`
- **Missing segment:** `E7Yhz7BWtAcAAxiF`

The recovered address matches the authoritative catalogue entry stored in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which associates HASH160 `6534b31208fe6e100d29f9c9c75aac8bf06fbb38` with the same mainnet P2PKH destination.

To verify locally with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1AE8NzzgK-MbPo82NB5\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "6534b31208fe6e100d29f9c9c75aac8bf06fbb38\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1AE8NzzgKE7Yhz7BWtAcAAxiFMbPo82NB5`, confirming the restored address for Puzzle #92.
