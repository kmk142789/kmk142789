# Bitcoin Puzzle #12 — Reconstituting the Hidden Core

Puzzle #12 in the Bitcoin puzzle transaction series again reveals the five-opcode pay-to-public-key-hash (P2PKH) locking script with a censored middle segment in the advertised address:

```
1DBaumZxU-5kDtSZQot
Pkscript
OP_DUP
OP_HASH160
85a1f9ba4da24c24e582d9b891dacbd1b043f971
OP_EQUALVERIFY
OP_CHECKSIG
```

Cleaning the opcodes produces the canonical P2PKH template used by standard Bitcoin addresses:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Reconstructing the missing Base58Check infix follows the familiar process:

1. Prefix the published HASH160 with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the first four bytes.
3. Encode the resulting 25-byte buffer with the Bitcoin Base58 alphabet.

Executing these steps restores the elided section and yields the complete address:

- **Address:** `1DBaumZxUkM4qMQRt2LVWyFJq5kDtSZQot`
- **Missing segment:** `kM4qMQRt2LVWyFJq5`

The reconstructed address matches the authoritative catalogue entry recorded in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which pairs HASH160 `85a1f9ba4da24c24e582d9b891dacbd1b043f971` with the same mainnet P2PKH destination.

To validate locally with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1DBaumZxU-5kDtSZQot\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "85a1f9ba4da24c24e582d9b891dacbd1b043f971\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1DBaumZxUkM4qMQRt2LVWyFJq5kDtSZQot`, confirming the restored address for Puzzle #12.
