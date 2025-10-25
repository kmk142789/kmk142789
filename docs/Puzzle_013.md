# Bitcoin Puzzle #13 — Reweaving the Broadcast Address

Puzzle #13 publishes the familiar five-opcode pay-to-public-key-hash (P2PKH) locking script with a censored
center segment in the Base58Check-encoded address:

```
1Pie8JkxB-2D8q3GBc1
Pkscript
OP_DUP
OP_HASH160
f932d0188616c964416b91fb9cf76ba9790a921e
OP_EQUALVERIFY
OP_CHECKSIG
```

Removing the line breaks yields the canonical P2PKH template used by legacy Bitcoin destinations:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the hidden portion of the address follows the standard reconstruction procedure:

1. Prefix the HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte buffer and append the first four bytes.
3. Encode the resulting 25-byte payload using the Bitcoin Base58 alphabet.

Executing these steps restores the elided characters and produces the full address:

- **Address:** `1Pie8JkxBT6MGPz9Nvi3fsPkr2D8q3GBc1`
- **Missing segment:** `T6MGPz9Nvi3fsPkr`

The reconstructed address matches the authoritative catalogue entry recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which maps HASH160
`f932d0188616c964416b91fb9cf76ba9790a921e` to the same mainnet P2PKH destination.

Validate locally with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1Pie8JkxB-2D8q3GBc1\nPkscript\nOP_DUP\nOP_HASH160\nf932d0188616c964416b91fb9cf76ba9790a921e\nOP_EQUALVERIFY\nOP_CHECKSIG\n"""
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1Pie8JkxBT6MGPz9Nvi3fsPkr2D8q3GBc1`, confirming the restored address for Puzzle #13.
